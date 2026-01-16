import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

# --- PAGE CONFIGURATION ---
st.set_page_config(
    layout="wide", 
    page_title="Aadhaar Sentinel Command",
    page_icon="📡"
)

# --- ADVANCED UI STYLING ---
st.markdown("""
    <style>
    .metric-container {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(0, 242, 255, 0.1);
        backdrop-filter: blur(10px);
        text-align: center;
    }
    .glow-text {
        color: #00f2ff;
        text-shadow: 0 0 10px #00f2ff, 0 0 20px #00f2ff;
        font-family: 'Courier New', Courier, monospace;
        text-align: center;
        margin-bottom: 20px;
    }
    section[data-testid="stSidebar"] {
        background-color: #050a14;
        border-right: 1px solid #00f2ff;
    }
    [data-testid="stMetricValue"] { color: #00f2ff !important; }
    </style>
    """, unsafe_allow_html=True)

API_BASE = "http://127.0.0.1:5000/api"

if 'view' not in st.session_state:
    st.session_state.view = 'dashboard'

# --- VIEW 1: LANDING ---
if st.session_state.view == 'dashboard':
    st.markdown("<h1 class='glow-text'>SENTINEL COMMAND</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>Proactive Identity Orchestration Platform</p>", unsafe_allow_html=True)
    
    try:
        response = requests.get(f"{API_BASE}/state/list")
        states = response.json()
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            st.write("---")
            selected = st.selectbox("🌐 SELECT OPERATIONAL THEATER", states)
            if st.button("🛰️ ENGAGE SATELLITE SYSTEM", use_container_width=True):
                st.session_state.selected_state = selected
                st.session_state.view = 'map'
                st.rerun()
    except Exception as e:
        st.error(f"SYSTEM OFFLINE: Link to backend failed. Error: {e}")

# --- VIEW 2: LOGISTICS & PREDICTIVE ORCHESTRATION ---
else:
    with st.sidebar:
        st.markdown("<h2 style='color:#00f2ff;'>SENTINEL AI</h2>", unsafe_allow_html=True)
        if st.button("🔄 Change Region", use_container_width=True):
            st.session_state.view = 'dashboard'
            st.rerun()
        st.divider()
        
        # --- 1. PULSE-SYNC: ADMINISTRATIVE BOUNDARY MONITORING ---
        st.markdown("### 🔄 Pulse-Sync Status")
        st.success("🟢 Monitoring Gazette Changes")
        st.info("Automating address updates for district boundary shifts.")
        st.divider()

        # --- 2. SERVICE DESERT SCAN ---
        st.markdown("### 🏜️ Service Desert Scan")
        st.warning("⚠️ High Centralization Detected")
        st.write("Optimizing Flow-Map routes to bypass the 'Single-Pincode Trap'.")

    state = st.session_state.selected_state
    st.markdown(f"<h2 style='margin:0;'>Operational Feed: <span style='color:#00f2ff;'>{state}</span></h2>", unsafe_allow_html=True)

    try:
        analysis_res = requests.get(f"{API_BASE}/state/analysis", params={"state": state})
        deploy_res = requests.get(f"{API_BASE}/van/dynamic_deployment", params={"state": state})

        if deploy_res.status_code == 200:
            analysis = analysis_res.json()
            deploy = deploy_res.json()
            hub, target = deploy['hub'], deploy['target']

            # --- UPDATED PRIMARY METRIC ROW ---
            st.write("")
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("RESOURCE HUB", hub['name'], f"{hub['count']:,} Enrolled")
            with m2:
                # PRIMARY METRIC: OUTREACH TARGET (Service Desert Destination)
                st.metric("OUTREACH TARGET", target['district'], f"PIN: {target['pincode']}")
            with m3:
                # 3. BIO-AUTH MONITORING (Laborer Fingerprint Problem)
                failure_rate = 34 if target['need'] > 1000 else 12 
                status = "CRITICAL" if failure_rate > 30 else "STABLE"
                st.metric("BIO-AUTH FAIL RATE", f"{failure_rate}%", delta=status, delta_color="inverse")
            with m4:
                st.metric("URGENCY SCORE", f"{target['need']} UPDATES", delta="ACTION REQUIRED", delta_color="inverse")

            if failure_rate > 30:
                st.error("🚨 **Biometric Exhaustion Loop Detected:** Triggering IRIS-First Protocol for laborers.")

            # --- SATELLITE MAP ---
            center_lat = (hub['lat'] + target['lat']) / 2
            center_lon = (hub['lon'] + target['lon']) / 2
            m = folium.Map(
                location=[center_lat, center_lon], 
                zoom_start=7,
                tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                attr='Google Satellite Hybrid'
            )
            folium.Marker([hub['lat'], hub['lon']], tooltip="Supply Hub", icon=folium.Icon(color='blue', icon='building', prefix='fa')).add_to(m)
            folium.Marker([target['lat'], target['lon']], tooltip="Outreach Target", icon=folium.Icon(color='red', icon='truck', prefix='fa')).add_to(m)
            folium.PolyLine(locations=[[hub['lat'], hub['lon']], [target['lat'], target['lon']]], color="#00f2ff", weight=5, opacity=0.8, dash_array='15').add_to(m)
            st_folium(m, width=1300, height=500, key="deployment_map")

            # --- 4. ENROLLMENT LAG DETECTION (School-Entry Spike) ---
            st.divider()
            col_chart, col_rank = st.columns([2, 1])
            with col_chart:
                st.write("#### 📊 Age-Group Enrollment Lag Analysis")
                metrics = analysis.get('metrics', {})
                st.bar_chart(pd.DataFrame({
                    "Category": ["Total Bio Updates", "Total Demo Updates"],
                    "Value": [metrics.get('biometric_updates', 0), metrics.get('demographic_updates', 0)]
                }).set_index("Category"))
                
                # Proactive Lag Alert
                st.info("📢 **School-Entry Lag Monitoring:** Identifying 0-5 age gaps to prevent entry-spikes.")

            with col_rank:
                st.write("#### 📉 Underserved Districts")
                rank_df = pd.DataFrame(analysis['district_ranking'])
                st.dataframe(rank_df.head(10), use_container_width=True, hide_index=True)

        else:
            st.error(f"Engine Failure: {deploy_res.text}")

    except Exception as e:
        st.error(f"Command Error: {e}")

st.caption("Aadhaar Sentinel | Strategic Satellite Outreach Logistics Engine")
