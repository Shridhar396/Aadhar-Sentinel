from flask import Flask, jsonify, request
from flask_cors import CORS
from sentinel_metrics import SentinelEngine
import os

app = Flask(__name__)
CORS(app)  # Enables the frontend to talk to this API

# Initialize the Engine
# We use os.path to ensure it finds the 'data' folder regardless of where you run the script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')

engine = SentinelEngine(data_dir=DATA_DIR)
data_loaded = engine.load_data()

@app.route('/')
def home():
    return jsonify({"status": "Sentinel API is Online", "data_loaded": data_loaded})

@app.route('/api/geospatial', methods=['GET'])
def geospatial_scan():
    """
    Returns the Geospatial Concentration Scores.
    If a specific district is requested ?district=Barmer, returns single object.
    Otherwise returns the top critical zones.
    """
    district = request.args.get('district')
    if district:
        result = engine.get_geospatial_score(district)
    else:
        # Get top 10 critical deserts for the map
        result = engine.get_geospatial_score()
    return jsonify(result)

@app.route('/api/bio-stress', methods=['GET'])
def bio_stress_scan():
    """
    Returns Bio-Stress Indices.
    """
    district = request.args.get('district')
    if district:
        result = engine.get_bio_stress_index(district)
    else:
        result = engine.get_bio_stress_index()
    return jsonify(result)

@app.route('/api/dispatch', methods=['POST'])
def dispatch_vans():
    """
    Simulates Phase 3: Automated Logistics Dispatch.
    In a real scenario, this would call the GraphHopper API .
    Here, we return mock routing coordinates for the dashboard visualization.
    """
    # Mock response confirming dispatch
    return jsonify({
        "status": "DISPATCH CONFIRMED",
        "units_deployed": 3,
        "target_districts": ["WEST KHASI HILLS", "WEST JAINTIA HILLS", "DINAJPUR UTTAR"],
        "estimated_arrival": "4 hours",
        "log_message": "Optimizing Routes via GraphHopper API..."
    })

if __name__ == '__main__':
    print("--- STARTING SENTINEL ORCHESTRATION ENGINE ---")
    app.run(debug=True, port=5000)