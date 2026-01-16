import pandas as pd
import glob
import os

class SentinelEngine:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.df_enrol = pd.DataFrame()
        
    def load_data(self):
        # 1. Load Pincode Master
        coord_path = os.path.join(self.data_dir, "pincode_master.csv")
        if not os.path.exists(coord_path): return False
        pincode_coords = pd.read_csv(coord_path).rename(columns={'latitude': 'lat', 'longitude': 'lon'})
        pincode_coords['pincode'] = pincode_coords['pincode'].astype(str)
        pincode_coords = pincode_coords.drop_duplicates(subset=['pincode'])

        # 2. Load Enrolment Data
        enrol_files = glob.glob(os.path.join(self.data_dir, "api_data_aadhar_enrolment_*.csv"))
        df_master = pd.concat((pd.read_csv(f) for f in enrol_files), ignore_index=True)
        df_master['pincode'] = df_master['pincode'].astype(str)

        # 3. Load & Aggregate Biometric Data (Crucial for Graphs)
        bio_files = glob.glob(os.path.join(self.data_dir, "api_data_aadhar_biometric_*.csv"))
        if bio_files:
            df_bio = pd.concat((pd.read_csv(f) for f in bio_files), ignore_index=True)
            df_bio['pincode'] = df_bio['pincode'].astype(str)
            # Create the 'biometric_updated' column expected by app.py
            df_bio['biometric_updated'] = df_bio['bio_age_5_17'] + df_bio['bio_age_17_']
            # Aggregate to avoid duplication during merge
            df_bio_agg = df_bio.groupby(['pincode', 'state', 'district'])['biometric_updated'].sum().reset_index()
            df_master = pd.merge(df_master, df_bio_agg, on=['pincode', 'state', 'district'], how='left')

        # 4. Load & Aggregate Demographic Data (Crucial for Graphs)
        demo_files = glob.glob(os.path.join(self.data_dir, "api_data_aadhar_demographic_*.csv"))
        if demo_files:
            df_demo = pd.concat((pd.read_csv(f) for f in demo_files), ignore_index=True)
            df_demo['pincode'] = df_demo['pincode'].astype(str)
            # Create the 'demographic_updated' column expected by app.py
            df_demo['demographic_updated'] = df_demo['demo_age_5_17'] + df_demo['demo_age_17_']
            # Aggregate
            df_demo_agg = df_demo.groupby(['pincode', 'state', 'district'])['demographic_updated'].sum().reset_index()
            df_master = pd.merge(df_master, df_demo_agg, on=['pincode', 'state', 'district'], how='left')

        # 5. Final Cleaning & Coordinate Merge
        df_master = pd.merge(df_master, pincode_coords[['pincode', 'lat', 'lon']], on='pincode', how='left')
        
        # Normalize State names and filter India bounds
        df_master['state'] = df_master['state'].astype(str).str.upper().str.strip()
        df_master['lat'] = pd.to_numeric(df_master['lat'], errors='coerce')
        df_master['lon'] = pd.to_numeric(df_master['lon'], errors='coerce')
        
        india_filter = (df_master['lat'] >= 6.0) & (df_master['lat'] <= 38.0) & \
                       (df_master['lon'] >= 68.0) & (df_master['lon'] <= 98.0)
        
        # Fill missing updates with 0
        df_master['biometric_updated'] = df_master['biometric_updated'].fillna(0)
        df_master['demographic_updated'] = df_master['demographic_updated'].fillna(0)

        self.df_enrol = df_master[india_filter].dropna(subset=['lat', 'lon'])
        return True

    def get_priority_spot(self, state_name, district_name):
        """Calculates the exact spot where the van is needed most"""
        df = self.df_enrol[
            (self.df_enrol['state'] == state_name.upper()) & 
            (self.df_enrol['district'] == district_name)
        ].copy()
        
        if df.empty: return None

        df['total_need'] = df.get('age_0_5', 0) + df.get('age_5_17', 0) + df.get('age_18_greater', 0)
        
        top_spot = df.groupby(['pincode', 'lat', 'lon']).agg({'total_need': 'sum'}).reset_index()
        if top_spot.empty: return None
        
        top_spot = top_spot.sort_values(by='total_need', ascending=False).iloc[0]
        return top_spot.to_dict()
