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
    /* Dark glass effect for containers */
    .metric-container {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        text-align: center;
    }
    /* Pulsing glow for the title */
    .glow-text {
        color: #00f2ff;
        text-shadow: 0 0 10px #00f2ff, 0 0 20px #00f2ff;
        font-family: 'Courier New', Courier, monospace;
        text-align: center;
        margin-bottom: 20px;
    }
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #050a14;
        border-right: 1px solid #00f2ff;
    }
    /* Metric styling override */
    [data-testid="stMetricValue"] {
        color: #00f2ff !important;
    }
    </style>
    """, unsafe_allow_html=True)

API_BASE = "http://127.0.0.1:5000/api"

if 'view' not in st.session_state:
    st.session_state.view = 'dashboard'

# --- VIEW 1: LANDING ---
if st.session_state.view == 'dashboard':
    st.markdown("<h1 class='glow-text'>SENTINEL COMMAND</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>Dynamic Asset Deployment & Outreach Engine</p>", unsafe_allow_html=True)
    
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

# --- VIEW 2: LOGISTICS & SATELLITE MAP ---
else:
    with st.sidebar:
        st.markdown("<h2 style='color:#00f2ff;'>LOGISTICS</h2>", unsafe_allow_html=True)
        if st.button("🔄 Change Region", use_container_width=True):
            st.session_state.view = 'dashboard'
            st.rerun()
        st.divider()
        
    state = st.session_state.selected_state
    st.markdown(f"<h2 style='margin:0;'>Operational Feed: <span style='color:#00f2ff;'>{state}</span></h2>", unsafe_allow_html=True)

    try:
        # Fetching data from backend
        analysis_res = requests.get(f"{API_BASE}/state/analysis", params={"state": state})
        deploy_res = requests.get(f"{API_BASE}/van/dynamic_deployment", params={"state": state})

        if deploy_res.status_code == 200:
            analysis = analysis_res.json()
            deploy = deploy_res.json()
            hub, target = deploy['hub'], deploy['target']

            # --- TOP METRICS ---
            st.write("")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("RESOURCE HUB", hub['name'], f"{hub['count']:,} Enrolled")
            with c2:
                st.metric("OUTREACH TARGET", target['district'], f"PIN: {target['pincode']}")
            with c3:
                st.metric("URGENCY SCORE", f"{target['need']} UPDATES", delta="ACTION REQUIRED", delta_color="inverse")

            st.write("")
            st.info(f"💡 **Deployment Strategy:** Dispatching mobility van from high-density hub **{hub['name']}** to address resident origins in **{target['district']}**.")

            # --- SATELLITE MAP ---
            # Center map between Hub and Target
            center_lat = (hub['lat'] + target['lat']) / 2
            center_lon = (hub['lon'] + target['lon']) / 2

            m = folium.Map(
                location=[center_lat, center_lon], 
                zoom_start=7,
                tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', # Hybrid Satellite
                attr='Google Satellite Hybrid'
            )

            # Markers
            folium.Marker(
                [hub['lat'], hub['lon']], 
                tooltip=f"Crowded Hub: {hub['name']}", 
                icon=folium.Icon(color='blue', icon='building', prefix='fa')
            ).add_to(m)

            folium.Marker(
                [target['lat'], target['lon']], 
                tooltip=f"Deployment Origin: {target['pincode']}", 
                icon=folium.Icon(color='red', icon='truck', prefix='fa')
            ).add_to(m)

            # Deployment Path (Dashed Line)
            folium.PolyLine(
                locations=[[hub['lat'], hub['lon']], [target['lat'], target['lon']]], 
                color="#00f2ff", weight=5, opacity=0.8, dash_array='15',
                tooltip="Deployment Outreach Path"
            ).add_to(m)

            st_folium(m, width=1300, height=600, key="deployment_map")

            # --- LOWER ANALYSIS ---
            st.divider()
            col_chart, col_rank = st.columns([2, 1])
            with col_chart:
                st.write("#### 📊 Update Requirement Intensity")
                metrics = analysis.get('metrics', {})
                chart_data = pd.DataFrame({
                    "Category": ["Biometric", "Demographic"],
                    "Needs": [metrics.get('biometric_updates', 0), metrics.get('demographic_updates', 0)]
                }).set_index("Category")
                st.bar_chart(chart_data)

            with col_rank:
                st.write("#### 📉 Underserved Districts")
                rank_df = pd.DataFrame(analysis['district_ranking']).head(10)
                st.dataframe(rank_df, use_container_width=True, hide_index=True)

        else:
            st.error(f"Engine Failure: {deploy_res.text}")

    except Exception as e:
        st.error(f"Command Error: {e}")

st.caption("Aadhaar Sentinel | Strategic Satellite Outreach Logistics Engine")
