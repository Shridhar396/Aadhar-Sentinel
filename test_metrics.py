from backend.sentinel_metrics import SentinelEngine

# Initialize
engine = SentinelEngine(data_dir="data")

if engine.load_data():
    print("\n--- TEST 1: Service Deserts (Geospatial Score) ---")
    # Check West Khasi Hills (Mentioned in PDF Page 8)
    print(engine.get_geospatial_score("West Khasi Hills"))
    
    print("\n--- TEST 2: High Priority Zones ---")
    # Show top 3 deserts automatically detected
    top_deserts = engine.get_geospatial_score()
    for d in top_deserts[:3]:
        print(f"District: {d['district']} | Score: {d['s_score']:.1f}")

    print("\n--- TEST 3: Bio-Stress Index ---")
    # Check a high stress district (e.g. Dantewada or similar)
    print(engine.get_bio_stress_index("Dantewada"))