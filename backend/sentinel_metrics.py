import pandas as pd
import glob
import os

class SentinelEngine:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.df_enrol = pd.DataFrame()
        self.df_bio = pd.DataFrame()
        
    def load_data(self):
        """
        Loads and merges split CSV files from the data directory.
        """
        print(f"Loading data from {self.data_dir}...")
        
        # 1. Load Enrolment Data (for Geospatial Score)
        enrol_files = glob.glob(os.path.join(self.data_dir, "api_data_aadhar_enrolment_*.csv"))
        if enrol_files:
            self.df_enrol = pd.concat((pd.read_csv(f) for f in enrol_files), ignore_index=True)
            # Clean District Names
            self.df_enrol['district'] = self.df_enrol['district'].str.upper().str.strip().str.replace('?', '-')
        else:
            print("WARNING: No enrolment files found.")

        # 2. Load Biometric Data (for Bio-Stress Index)
        bio_files = glob.glob(os.path.join(self.data_dir, "api_data_aadhar_biometric_*.csv"))
        if bio_files:
            self.df_bio = pd.concat((pd.read_csv(f) for f in bio_files), ignore_index=True)
            self.df_bio['district'] = self.df_bio['district'].str.upper().str.strip().str.replace('?', '-')
        else:
            print("WARNING: No biometric files found.")
            
        print(f"Data Loaded. Enrolment Records: {len(self.df_enrol)} | Biometric Records: {len(self.df_bio)}")
        return not self.df_enrol.empty

    def get_geospatial_score(self, district_name=None):
        """
        Calculates Metric A: Geospatial Concentration Score (S)
        Formula: S = Total Enrolments / Count of Active Pincodes
        """
        # Aggregate data by District
        # We sum the age columns to get total enrolments
        district_agg = self.df_enrol.groupby('district').agg({
            'pincode': 'nunique',
            'age_0_5': 'sum', 
            'age_5_17': 'sum', 
            'age_18_greater': 'sum'
        }).reset_index()
        
        district_agg['total_enrolments'] = (district_agg['age_0_5'] + 
                                          district_agg['age_5_17'] + 
                                          district_agg['age_18_greater'])
        
        # Avoid division by zero
        district_agg['s_score'] = district_agg.apply(
            lambda row: row['total_enrolments'] / row['pincode'] if row['pincode'] > 0 else 0, axis=1
        )
        
        if district_name:
            # Return specific district
            clean_name = district_name.upper().strip()
            row = district_agg[district_agg['district'] == clean_name]
            if row.empty: return {"error": "District not found"}
            row = row.iloc[0]
            return {
                "district": clean_name,
                "active_pincodes": int(row['pincode']),
                "total_enrolments": int(row['total_enrolments']),
                "s_score": round(row['s_score'], 2),
                "is_service_desert": bool(row['s_score'] > 1000) # Threshold adjusted based on data
            }
        else:
            # Return top 5 Service Deserts
            return district_agg.sort_values('s_score', ascending=False).head(5).to_dict('records')

    def get_bio_stress_index(self, district_name=None):
        """
        Calculates Metric B: Bio-Stress Index (BSI)
        Formula: BSI = Total Biometric Updates / Fresh Enrolments
        """
        # Aggregate Biometric Data
        bio_agg = self.df_bio.groupby('district').agg({
            'bio_age_5_17': 'sum',
            'bio_age_17_': 'sum'
        }).reset_index()
        bio_agg['total_bio_updates'] = bio_agg['bio_age_5_17'] + bio_agg['bio_age_17_']
        
        # Aggregate Enrolment Data (Denominator)
        enrol_agg = self.df_enrol.groupby('district').agg({
            'age_0_5': 'sum', 'age_5_17': 'sum', 'age_18_greater': 'sum'
        }).reset_index()
        enrol_agg['total_fresh'] = (enrol_agg['age_0_5'] + enrol_agg['age_5_17'] + enrol_agg['age_18_greater'])

        # Merge
        merged = pd.merge(enrol_agg, bio_agg, on='district', how='inner')
        
        # Calculate BSI
        merged['bsi'] = merged.apply(
            lambda row: row['total_bio_updates'] / row['total_fresh'] if row['total_fresh'] > 0 else 0, axis=1
        )

        if district_name:
            clean_name = district_name.upper().strip()
            row = merged[merged['district'] == clean_name]
            if row.empty: return {"error": "District not found in both datasets"}
            row = row.iloc[0]
            return {
                "district": clean_name,
                "bsi_score": round(row['bsi'], 2),
                "status": "CRITICAL BIO-STRESS" if row['bsi'] > 2.5 else "NORMAL"
            }
        else:
             return merged.sort_values('bsi', ascending=False).head(5).to_dict('records')