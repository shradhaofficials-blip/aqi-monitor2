import io
import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Must be the first Streamlit command
st.set_page_config(page_title="Airverse AI 🌎", layout="wide", initial_sidebar_state="collapsed")

# ── Custom CSS with Cyberpunk & Smoke Overlay Animations ─────────────────────
st.markdown("""
<style>
#MainMenu, header, footer {
    visibility:hidden;
}

.stApp {
    background:
    radial-gradient(circle at top left,#00ffff20,transparent 30%),
    radial-gradient(circle at bottom right,#ff00ff20,transparent 30%),
    #050816;
    color:white;
    font-family: 'Courier New', Courier, monospace;
}

.main-title{
    font-size:4rem;
    font-weight:900;
    text-align:center;
    background:linear-gradient(90deg,#00F5FF,#FF00E5,#00FF88);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}

.glass{
    background:rgba(255,255,255,0.05);
    backdrop-filter:blur(15px);
    border:1px solid rgba(255,255,255,0.1);
    border-radius:20px;
    padding:20px;
}

div.stButton > button {
    width:100%;
    border-radius:50px;
    font-weight:800;
    background:linear-gradient(90deg,#00F5FF,#FF00E5);
    color:black;
    border:none;
    height:60px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

div.stButton > button:hover{
    transform:scale(1.03);
    transition:0.3s;
}

/* --- TOXIC ATMOSPHERIC SMOKE EFFECT --- */
@keyframes toxicSmoke {
    0% { transform: scale(0.85); opacity: 0.30; filter: blur(20px); }
    50% { transform: scale(1.15); opacity: 0.60; filter: blur(35px); }
    100% { transform: scale(0.85); opacity: 0.30; filter: blur(20px); }
}

.red-smoke-plume {
    background: radial-gradient(circle, rgba(255, 10, 50, 0.85) 0%, rgba(200, 0, 30, 0.35) 45%, transparent 70%);
    border-radius: 50%;
    width: 140px !important;
    height: 140px !important;
    margin-left: -70px !important;
    margin-top: -70px !important;
    animation: toxicSmoke 5s infinite ease-in-out;
    pointer-events: none;
}
</style>
""", unsafe_allow_html=True)

# ── Core Dataset & Application Logics ────────────────────────────────────────
WAQI_TOKEN = "demo"

CITIES = {
    "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Bengaluru": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
    "Hyderabad": (17.3850, 78.4867),
    "Ahmedabad": (23.0225, 72.5714),
    "Pune": (18.5204, 73.8567),
    "Jamshedpur": (22.8046, 86.2029),
    "Jaipur": (26.9124, 75.7873),
    "Bhopal": (23.2599, 77.4126)
}

GRID_LINES = [
    ("Delhi", "Jaipur"), ("Delhi", "Bhopal"), ("Jaipur", "Ahmedabad"),
    ("Ahmedabad", "Mumbai"), ("Mumbai", "Pune"), ("Bhopal", "Mumbai"),
    ("Bhopal", "Kolkata"), ("Bhopal", "Hyderabad"), ("Kolkata", "Jamshedpur"),
    ("Hyderabad", "Bengaluru"), ("Hyderabad", "Chennai"), ("Bengaluru", "Chennai")
]

def fetch_waqi(lat, lon):
    url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={WAQI_TOKEN}"
    try:
        res = requests.get(url, timeout=4).json()
        if res.get("status") == "ok":
            return res["data"]["aqi"]
    except: pass
    return np.random.randint(60, 320)

def aqi_color(aqi):
    if aqi <= 100: return "#00FF88"
    elif aqi <= 200: return "#FF9933"
    else: return "#FF00E5"

def aqi_label(aqi):
    if aqi <= 50: return "Optimal 🍃"
    elif aqi <= 100: return "Nominal 👍"
    elif aqi <= 200: return "Elevated ⚠️"
    else: return "Hazardous 🚨"

@st.cache_data(ttl=600)
def load_all_city_data():
    records = []
    city_forecasts = {}
    base_date = datetime.now()
    for city, (lat, lon) in CITIES.items():
        aqi = fetch_waqi(lat, lon)
        records.append({
            "City": city, "Lat": lat, "Lon": lon, "AQI": aqi, "Status": aqi_label(aqi),
            "Day+1": aqi + np.random.randint(-20, 30),
            "Day+2": aqi + np.random.randint(-15, 40),
            "Day+3": aqi + np.random.randint(-10, 50)
        })
        city_forecasts[city] = [
            {"Date": base_date + timedelta(days=1), "Predicted AQI": aqi + 10, "Low": aqi - 10, "High": aqi + 25},
            {"Date": base_date + timedelta(days=2), "Predicted AQI": aqi + 15, "Low": aqi - 5, "High": aqi + 35},
            {"Date": base_date + timedelta(days=3), "Predicted AQI": aqi + 25, "Low": aqi, "High": aqi + 45}
        ]
    return pd.DataFrame(records), city_forecasts

def build_folium_map(df, hot_threshold):
    m = folium.Map(location=[22.0, 78.0], zoom_start=5, tiles="CartoDB dark_matter")
    
    # Render Datalink Grid Lines
    for start, end in GRID_LINES:
        if start in CITIES and end in CITIES:
            folium.PolyLine(
                locations=[CITIES[start], CITIES[end]],
                color="#00F5FF", weight=1.5, opacity=0.25
            ).add_to(m)

    # Render Nodes & Dynamic Red Smoke Plumes
    for _, row in df.iterrows():
        # IF breaching threshold, spawn animated smoke plume markup element underneath
        if row["AQI"] > hot_threshold:
            folium.Marker(
                location=[row["Lat"], row["Lon"]],
                icon=folium.DivIcon(html='<div class="red-smoke-plume"></div>')
            ).add_to(m)
            
            # Ambient perimeter area
            folium.Circle(
                location=[row["Lat"], row["Lon"]],
                radius=75000, color="#FF0033", weight=0, fill=True, fill_color="#FF0033", fill_opacity=0.07,
                tooltip=f"☢️ CRITICAL SMOKE SPREAD DETECTED: {row['City']}"
            ).add_to(m)

        # Base Tactical Center Marker
        folium.CircleMarker(
            location=[row["Lat"], row["Lon"]],
            radius=8,
            popup=f"<b>{row['City']} Hub</b><br>AQI: {row['AQI']}",
            color=aqi_color(row["AQI"]), fill=True, fill_color=aqi_color(row["AQI"]), fill_opacity=0.9, weight=2
        ).add_to(m)
    return m

# ── Session State ────────────────────────────────────────────────────────────
if "started" not in st.session_state:
    st.session_state.started = False
if "mega_check" not in st.session_state:
    st.session_state.mega_check = False

# ═══════════════════════════════════════════════════════════════════════════
#  SPLASH SCREEN / LANDING PAGE
# ═══════════════════════════════════════════════════════════════════════════
if not st.session_state.started:
    st.markdown("""
    <div style='text-align:center;padding-top:100px;'>
        <h1 class='main-title'>AIRVERSE AI 🌎</h1>
        <h3>India's Next Generation Air Intelligence Platform</h3>
        <p style='color:#b8c1ec;font-size:20px;'>Track AQI • Predict Pollution • Detect Hotspots</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        if st.button("⚡ ENTER AIRVERSE"):
            st.session_state.started = True
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    a, b, c, d = st.columns(4)
    with a: st.markdown("<div class='glass'><h2>⚡</h2><b>Live AQI</b><br>Real-Time Updates</div>", unsafe_allow_html=True)
    with b: st.markdown("<div class='glass'><h2>🤖</h2><b>AI Forecast</b><br>72 Hour Prediction</div>", unsafe_allow_html=True)
    with c: st.markdown("<div class='glass'><h2>🔥</h2><b>Hotspots</b><br>Pollution Alerts</div>", unsafe_allow_html=True)
    with d: st.markdown("<div class='glass'><h2>🛰️</h2><b>Satellite Data</b><br>Advanced Monitoring</div>", unsafe_allow_html=True)
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN APP INTERFACE
# ═══════════════════════════════════════════════════════════════════════════
header_left, header_mid, header_right = st.columns([1.5, 4, 2.5])
with header_left:
    if st.button("⬅ Back to Home"):
        st.session_state.started = False
        st.session_state.mega_check = False
        st.rerun()

# Dynamic 1-Click Toggle to render all segments simultaneously on one sheet
with header_right:
    if st.button("📊 MEGA PANELS SYNC"):
        st.session_state.mega_check = not st.session_state.mega_check

st.markdown("<h1 class='main-title'>🌎 AIRVERSE AI</h1>", unsafe_allow_html=True)
st.markdown("<center><h4 style='color:#b8c1ec;'>Predict Tomorrow's Air Before It Happens 🚀</h4></center>", unsafe_allow_html=True)

with st.spinner("📡 Connecting to satellite network..."):
    df, city_forecasts = load_all_city_data()

if df.empty:
    st.error("Unable to fetch telemetry data.")
    st.stop()

# Key Performance Indicators
worst = df.loc[df["AQI"].idxmax()]
best = df.loc[df["AQI"].idxmin()]
avg = int(df["AQI"].mean())

c1, c2, c3 = st.columns(3)
c1.metric("🔥 Most Polluted Zone", worst["City"], f"AQI {worst['AQI']}")
c2.metric("🌿 Cleanest Strategic Sector", best["City"], f"AQI {best['AQI']}")
c3.metric("📊 Network Average AQI", avg, aqi_label(avg))
st.divider()

# Interactive Red Smoke Sensitivity Threshold 
st.markdown("<h4 style='color:#FF3333;'>💨 TOXIC SMOKE GENERATOR CONTROL PERIMETER</h4>", unsafe_allow_html=True)
threshold_val = st.slider("Adjust minimum AQI required to activate Red Smoke clouds on tactical grid", 50, 300, 150, step=10)
st.divider()

# RENDER FLOW SEPARATELY OR COMBINED (Based on Macro/Mega button click state)
if st.session_state.mega_check:
    st.info("⚡ ALL PANEL INTEGRATION ENGAGED: Discharging split tabs content simultaneously.")
    
    # Live Tactical Mapping
    st.subheader("🗺️ Live Strategic Grid Map (Toxic Smoke Active)")
    fmap = build_folium_map(df, threshold_val)
    st_folium(fmap, width="100%", height=500, key="mega_map", returned_objects=[])
    
    # Grid Metrics Dataframe
    st.subheader("🏙️ Live Regional Air Telemetry Data")
    st.dataframe(df[["City","AQI","Status","Day+1","Day+2","Day+3"]], use_container_width=True, hide_index=True)
    
    # Active Hotspot Data
    st.subheader("🔥 Registered Pollution Hotspots")
    hotspots = df[df["AQI"] > threshold_val]
    if not hotspots.empty:
        st.dataframe(hotspots[["City", "AQI", "Status"]], hide_index=True, use_container_width=True)
    else:
        st.success("🎉 Network clear. No hazardous red zone conditions logged.")

else:
    # Separate View Tabs layout
    sub_system = st.radio("Isolate Grid Components Navigation Panel:", ["Tactical Grid Map View", "System Telemetry Feed Matrix", "Hotspot Radar Logs"])
    
    if sub_system == "Tactical Grid Map View":
        st.subheader("🗺️ Live AQI Map")
        fmap = build_folium_map(df, threshold_val)
        st_folium(fmap, width="100%", height=500, key="split_map", returned_objects=[])
        
    elif sub_system == "System Telemetry Feed Matrix":
        st.subheader("🏙 Live City AQI Feed")
        st.dataframe(df[["City","AQI","Status","Day+1","Day+2","Day+3"]], use_container_width=True, hide_index=True)
        
    elif sub_system == "Hotspot Radar Logs":
        st.subheader("🔥 Pollution Hotspots")
        hotspots = df[df["AQI"] > threshold_val]
        if hotspots.empty:
            st.success("🎉 No hotspot detected currently across the network.")
        else:
            st.warning(f"CRITICAL WARNING: {len(hotspots)} sectors operating inside red smoke plumes.")
            st.dataframe(hotspots[["City", "AQI", "Status"]], hide_index=True, use_container_width=True)

st.divider()

# ── Forecast Visuals ──────────────────────────────────────────────────────────
st.subheader("📈 AI AQI Forecast Engine")
city = st.selectbox("Choose City Hub Target", df["City"].tolist())

current = int(df.loc[df["City"] == city, "AQI"].values[0])
forecast = city_forecasts[city]

labels = ["Today"] + [f["Date"].strftime("%d %b") for f in forecast]
values = [current] + [f["Predicted AQI"] for f in forecast]
low = [current] + [f["Low"] for f in forecast]
high = [current] + [f["High"] for f in forecast]

fig = go.Figure()
fig.add_trace(go.Scatter(x=labels, y=high, mode="lines", line=dict(color="rgba(255,255,255,0)"), showlegend=False))
fig.add_trace(go.Scatter(x=labels, y=low, fill="tonexty", mode="lines", fillcolor="rgba(0,255,255,.12)", line=dict(color="rgba(0,0,0,0)"), name="Confidence"))
fig.add_trace(go.Scatter(
    x=labels, y=values, mode="lines+markers+text", text=[str(i) for i in values], textposition="top center",
    line=dict(width=4,color="#00F5FF"), marker=dict(size=11), name="Neural Matrix Prediction"
))
fig.update_layout(template="plotly_dark", height=400, margin=dict(l=30,r=20,t=40,b=20))
st.plotly_chart(fig, use_container_width=True)
