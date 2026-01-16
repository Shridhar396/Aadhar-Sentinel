from flask import Flask, jsonify, request
from flask_cors import CORS
from sentinel_metrics import SentinelEngine
import os
import pandas as pd

app = Flask(__name__)
CORS(app)

# Initialize Engine
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'data'))
engine = SentinelEngine(data_dir=DATA_DIR)
engine.load_data()

@app.route('/api/state/list', methods=['GET'])
def get_states():
    if engine.df_enrol.empty: return jsonify([])
    return jsonify(sorted(engine.df_enrol['state'].unique().tolist()))

@app.route('/api/state/analysis', methods=['GET'])
def get_state_details():
    state_name = request.args.get('state')
    state_df = engine.df_enrol[engine.df_enrol['state'] == state_name.upper()].copy()
    if state_df.empty: return jsonify({"error": "No data"}), 404

    bio = int(state_df['biometric_updated'].sum()) if 'biometric_updated' in state_df.columns else 0
    demo = int(state_df['demographic_updated'].sum()) if 'demographic_updated' in state_df.columns else 0
    
    # Rank districts by enrollment (Lowest first to see underserved regions)
    dist_rank = state_df.groupby('district').size().reset_index(name='enrolments')
    dist_rank = dist_rank.sort_values(by='enrolments', ascending=True)

    return jsonify({
        "metrics": {"total_enrolments": len(state_df), "biometric_updates": bio, "demographic_updates": demo},
        "district_ranking": dist_rank.to_dict(orient='records')
    })

@app.route('/api/van/dynamic_deployment', methods=['GET'])
def get_dynamic_deployment():
    state_name = request.args.get('state')
    state_df = engine.df_enrol[engine.df_enrol['state'] == state_name.upper()].copy()
    if state_df.empty: return jsonify({"error": "No data"}), 404

    # Data Cleaning
    state_df['lat'] = pd.to_numeric(state_df['lat'], errors='coerce')
    state_df['lon'] = pd.to_numeric(state_df['lon'], errors='coerce')
    state_df = state_df.dropna(subset=['lat', 'lon'])

    # 1. IDENTIFY CROWDED HUB (Supply Center)
    counts = state_df.groupby('district').size().reset_index(name='count')
    hub_name = counts.sort_values(by='count', ascending=False).iloc[0]['district']
    hub_coords = state_df[state_df['district'] == hub_name][['lat', 'lon']].mean()

    # 2. IDENTIFY TARGET ORIGIN (Where the people are traveling from)
    state_df['update_need'] = state_df.get('biometric_updated', 0) + state_df.get('demographic_updated', 0)
    # Find high update need in districts OTHER than the hub
    source_df = state_df[state_df['district'] != hub_name]
    target_spot = source_df.sort_values(by='update_need', ascending=False).iloc[0]

    return jsonify({
        "hub": {"name": hub_name, "lat": float(hub_coords['lat']), "lon": float(hub_coords['lon']), "count": int(counts.max()['count'])},
        "target": {
            "district": target_spot['district'], "pincode": target_spot['pincode'],
            "lat": float(target_spot['lat']), "lon": float(target_spot['lon']),
            "need": int(target_spot['update_need'])
        }
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
