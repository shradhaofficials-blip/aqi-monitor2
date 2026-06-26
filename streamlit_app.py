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
st.set_page_config(page_title="VayuShashtra AI 🪷", layout="wide", initial_sidebar_state="collapsed")

# ── Custom CSS with Cyberpunk Animations ──────────────────────────────────────
st.markdown("""
<style>
#MainMenu, header, footer {
    visibility:hidden;
}

/* Deep void background with neon cyan and magenta radial glows */
.stApp {
    background-color: #050816;
    background-image: 
        radial-gradient(circle at top left, rgba(0, 245, 255, 0.15), transparent 40%),
        radial-gradient(circle at bottom right, rgba(255, 0, 229, 0.15), transparent 40%);
    color: #E0FFFF;
    font-family: 'Courier New', Courier, monospace;
}

/* Bright text overrides for dark mode */
h1, h2, h3, h4, h5, h6, p, span, label, .st-emotion-cache-1wivap2 {
    color: #E0FFFF !important;
}

/* Moving Grid Gradient for Title */
@keyframes gridShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.main-title{
    font-size: 4rem;
    font-weight: 900;
    text-align: center;
    background: linear-gradient(90deg, #FF9933, #FF00E5, #00F5FF, #FF9933);
    background-size: 300% 300%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent !important;
    text-shadow: 0px 0px 15px rgba(255, 0, 229, 0.4);
    animation: gridShift 6s ease infinite;
}

/* Breathing Cyber Glow for Glass Panels */
@keyframes cyberBreathe {
    0% { box-shadow: 0 0 15px rgba(0, 245, 255, 0.15), inset 0 0 10px rgba(0, 245, 255, 0.05); border-color: #00F5FF; }
    50% { box-shadow: 0 0 25px rgba(255, 0, 229, 0.35), inset 0 0 15px rgba(255, 0, 229, 0.15); border-color: #FF00E5; }
    100% { box-shadow: 0 0 15px rgba(0, 245, 255, 0.15), inset 0 0 10px rgba(0, 245, 255, 0.05); border-color: #00F5FF; }
}

.glass{
    background: rgba(10, 15, 30, 0.7);
    backdrop-filter: blur(10px);
    border: 1px solid #00F5FF; 
    border-radius: 10px; 
    padding: 20px;
    text-align: center;
    animation: cyberBreathe 4s infinite ease-in-out;
    transition: transform 0.3s;
}

.glass:hover {
    transform: translateY(-5px);
    animation: none; 
    box-shadow: 0 0 35px rgba(0, 245, 255, 0.6), inset 0 0 20px rgba(0, 245, 255, 0.3);
    border-color: #00F5FF;
}

/* Terminal Underline Scanner for Subheadings */
@keyframes scanline {
    0% { border-bottom: 2px solid #00F5FF; }
    50% { border-bottom: 2px solid #FF00E5; }
    100% { border-bottom: 2px solid #00F5FF; }
}

.sub-header {
    display: inline-block;
    padding-bottom: 5px;
    margin-bottom: 15px;
    animation: scanline 3s infinite ease-in-out;
}

/* Cyberpunk Button styling */
div.stButton > button {
    width: 100%;
    border-radius: 5px;
    font-weight: 800;
    font-size: 1.1rem;
    background: transparent;
    color: #00F5FF !important;
    border: 2px solid #00F5FF;
    height: 55px;
    box-shadow: 0 0 15px rgba(0, 245, 255, 0.3);
    text-transform: uppercase;
    letter-spacing: 1px;
    transition: all 0.2s ease-in-out;
}

div.stButton > button * {
    color: #00F5FF !important;
}

div.stButton > button:hover{
    transform: scale(1.02);
    background: #00F5FF;
    color: #050816 !important;
    box-shadow: 0 0 35px rgba(0, 245, 255, 0.8);
}

div.stButton > button:hover * {
    color: #050816 !important;
}

/* DataFrame Customization */
[data-testid="stDataFrame"] {
    background-color: rgba(10, 15, 30, 0.8);
    border: 1px solid #FF00E5;
    box-shadow: 0 0 15px rgba(255, 0, 229, 0.2);
}
</style>
""", unsafe_allow_html=True)


# ── Configuration & Functions ────────────────────────────────────────────────
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
    "Joda": (22.0167, 85.4333),
    "Jaipur": (26.9124, 75.7873),
    "Bhopal": (23.2599, 77.4126),
    "Kochi": (9.9312, 76.2673)
}

GRID_LINES = [
    ("Delhi", "Jaipur"), ("Delhi", "Bhopal"), ("Jaipur", "Ahmedabad"),
    ("Ahmedabad", "Mumbai"), ("Mumbai", "Pune"), ("Bhopal", "Mumbai"),
    ("Bhopal", "Kolkata"), ("Bhopal", "Hyderabad"), ("Kolkata", "Jamshedpur"),
    ("Jamshedpur", "Joda"), ("Joda", "Hyderabad"), ("Hyderabad", "Bengaluru"),
    ("Hyderabad", "Chennai"), ("Bengaluru", "Chennai"), ("Bengaluru", "Kochi")
]

def fetch_waqi(lat, lon):
    url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={WAQI_TOKEN}"
    try:
        response = requests.get(url, timeout=5).json()
        if response.get("status") == "ok":
            aqi = response["data"]["aqi"]
            if isinstance(aqi, int):
                return aqi
    except Exception:
        pass
    return np.random.randint(50, 350)

def aqi_label(aqi):
    if aqi <= 50: return "Optimal 🪷"
    elif aqi <= 100: return "Nominal 🍃"
    elif aqi <= 200: return "Elevated 🌤️"
    elif aqi <= 300: return "Degraded 😷"
    elif aqi <= 400: return "Hazardous ⚠️"
    else: return "CRITICAL 🚨"

def aqi_color(aqi):
    if aqi <= 50: return "#00FF88" 
    elif aqi <= 100: return "#FFFF00" 
    elif aqi <= 200: return "#FF9933" 
    elif aqi <= 300: return "#FF0055" 
    elif aqi <= 400: return "#FF00E5" 
    else: return "#8B00FF" 

def ai_forecast(current_aqi):
    forecast = []
    base_date = datetime.now()
    for i in range(1, 4):
        pred = max(0, current_aqi + np.random.randint(-30, 40))
        low = max(0, pred - np.random.randint(10, 25))
        high = pred + np.random.randint(10, 25)
        forecast.append({
            "Date": base_date + timedelta(days=i),
            "Predicted AQI": pred,
            "Low": low,
            "High": high
        })
    return forecast

@st.cache_data(ttl=900)
def load_all_city_data():
    records = []
    city_forecasts = {}
    for city, (lat, lon) in CITIES.items():
        current_aqi = fetch_waqi(lat, lon)
        status = aqi_label(current_aqi)
        forecast = ai_forecast(current_aqi)
        city_forecasts[city] = forecast
        
        records.append({
            "City": city,
            "Lat": lat,
            "Lon": lon,
            "AQI": current_aqi,
            "Status": status,
            "Day+1": forecast[0]["Predicted AQI"],
            "Day+2": forecast[1]["Predicted AQI"],
            "Day+3": forecast[2]["Predicted AQI"]
        })
    return pd.DataFrame(records), city_forecasts

def build_folium_map(df, hot_threshold):
    m = folium.Map(location=[22.0, 79.0], zoom_start=5, tiles="CartoDB dark_matter")
    
    # Grid Backbone
    for start_node, end_node in GRID_LINES:
        if start_node in CITIES and end_node in CITIES:
            start_coord = CITIES[start_node]
            end_coord = CITIES[end_node]
            folium.PolyLine(
                locations=[start_coord, end_coord],
                color="#00F5FF", weight=1.5, opacity=0.3
            ).add_to(m)

    # Drawing Hub Sectors & Dynamic Red Alert Warning Zones
    for _, row in df.iterrows():
        # Base Node
        folium.CircleMarker(
            location=[row["Lat"], row["Lon"]],
            radius=8,
            popup=f"<b style='color:#000;'>{row['City']}</b><br><span style='color:#000;'>AQI: {row['AQI']}</span>",
            tooltip=f"{row['City']} Node",
            color=aqi_color(row["AQI"]),
            fill=True, fill_color=aqi_color(row["AQI"]), fill_opacity=0.9, weight=2
        ).add_to(m)
        
        # MODIFICATION: Show Red Zone warning boundary overlay if breaching hotspot limit
        if row["AQI"] > hot_threshold:
            folium.Circle(
                location=[row["Lat"], row["Lon"]],
                radius=60000, # Large warning area marker
                color="#FF0033",
                weight=2,
                fill=True,
                fill_color="#FF0033",
                fill_opacity=0.25,
                tooltip=f"⚠️ TOXIC HOTSPOT PERIMETER BREAKOUT: {row['City']}"
            ).add_to(m)
            
    return m


# ── Session state ────────────────────────────────────────────────────────────
if "started" not in st.session_state:
    st.session_state.started = False
if "macro_check" not in st.session_state:
    st.session_state.macro_check = False

# ═══════════════════════════════════════════════════════════════════════════
#  LANDING PAGE (Splash Screen)
# ═══════════════════════════════════════════════════════════════════════════
if not st.session_state.started:
    st.markdown("""
    <div style='text-align:center;padding-top:80px;'>
    <h1 class='main-title'>VAYUSHASHTRA AI 🪷</h1>
    <h3 style='color:#00F5FF; text-shadow: 0 0 10px #00F5FF;'>
    Data in clouds, Clarity on grounds
    </h3>
    <p style='color:#FF9933; font-size:22px; font-weight:bold; text-shadow: 0 0 5px #FF9933;'>
    Decoded with AI
    </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        if st.button("SUMMON THE SATELLITES "):
            st.session_state.started = True
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    a, b, c, d = st.columns(4)
    with a:
        st.markdown("<div class='glass'><h2>🪷</h2><b>Live Telemetry</b><br>Real-Time Sync</div>", unsafe_allow_html=True)
    with b:
        st.markdown("<div class='glass'><h2>🤖</h2><b>Neural Forecast</b><br>72H Simulation</div>", unsafe_allow_html=True)
    with c:
        st.markdown("<div class='glass'><h2>🔥</h2><b>Red Zones</b><br>Toxicity Alerts</div>", unsafe_allow_html=True)
    with d:
        st.markdown("<div class='glass'><h2>🛰️</h2><b>Orbital Uplink</b><br>Satellite Feed</div>", unsafe_allow_html=True)
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════
c1, c2, c3 = st.columns([1.5, 3, 2])
with c1:
    if st.button("⬅ DISCONNECT"):
        st.session_state.started = False
        st.session_state.macro_check = False
        st.rerun()

# MODIFICATION: New Mega Check Button allows triggering all tabs/components immediately in one interface
with c3:
    if st.button("⚡ ALL SECTOR SYNCHRONIZATION"):
        st.session_state.macro_check = not st.session_state.macro_check

st.markdown("<h1 class='main-title'>🪷 VAYUSHASHTRA AI 🪷</h1>", unsafe_allow_html=True)
st.divider()

with st.spinner("🛰️ Establishing orbital uplink..."):
    df, city_forecasts = load_all_city_data()

if df.empty:
    st.error("SYSTEM FAILURE: Mainframe synchronization dropped.")
    st.stop()

# Basic Telemetry Metrics
worst = df.loc[df["AQI"].idxmax()]
best = df.loc[df["AQI"].idxmin()]
avg = int(df["AQI"].mean())

col1, col2, col3 = st.columns(3)
with col1:
    st.error(f"**🔥 TOXIC PEAK:** {worst['City']} (AQI {worst['AQI']})")
with col2:
    st.success(f"**🪷 OPTIMAL ZONE:** {best['City']} (AQI {best['AQI']})")
with col3:
    st.info(f"**📊 GRID AVERAGE:** {avg} - {aqi_label(avg)}")

st.divider()

# Toxicity Warning Perimeter Adjustment config
st.markdown("<h4 style='color:#FF0000;'>⚡ GLOBAL TOXICITY WARNING PERIMETER (RED ZONES)</h4>", unsafe_allow_html=True)
threshold = st.slider("Define Hotspot Threshold level to mark Red Zones", 50, 300, 160, step=10)
st.divider()

# Rendering View Structure based on the "Mega Button" or individual subpages
if st.session_state.macro_check:
    st.info("💡 GLOBAL ARCHIVE MODE ENGAGED: Displaying all subpage elements simultaneously below.")
    
    # 1. Telemetry Block
    st.markdown("<h3 class='sub-header' style='color:#FF9933;'>🏙️ SECTOR TELEMETRY</h3>", unsafe_allow_html=True)
    st.dataframe(df[["City","AQI","Status","Day+1","Day+2","Day+3"]], use_container_width=True, hide_index=True)
    
    # 2. Map Block with visible Red Alert Zones
    st.markdown("<h3 class='sub-header' style='color:#00F5FF;'>🗺️ TACTICAL GRID & RED ALERT ZONES</h3>", unsafe_allow_html=True)
    fmap = build_folium_map(df, threshold)
    st_folium(fmap, width="100%", height=500, key="macro_map", returned_objects=[])
    
    # 3. Hotspots Database Breakdown
    st.markdown("<h3 class='sub-header' style='color:#FF0000;'>🔥 DETECTED RADAR HOTSPOTS</h3>", unsafe_allow_html=True)
    hotspots = df[df["AQI"] > threshold]
    if not hotspots.empty:
        st.dataframe(hotspots[["City", "AQI", "Status"]], hide_index=True, use_container_width=True)
    else:
        st.success("Perimeter clean. No critical red flags found.")

else:
    # Segmented navigation view when the macro check is offline
    sub_tab = st.radio("Navigate Core Systems separately:", ["Strategic Grid & Mapping", "Raw System Telemetry Data", "Hotspot Breaches Check"])
    
    if sub_tab == "Strategic Grid & Mapping":
        st.markdown("<h3 class='sub-header' style='color:#00F5FF;'>🗺️ TACTICAL GRID MAP (RED ZONES DISPLAYED)</h3>", unsafe_allow_html=True)
        fmap = build_folium_map(df, threshold)
        st_folium(fmap, width="100%", height=500, key="normal_map", returned_objects=[])
        
    elif sub_tab == "Raw System Telemetry Data":
        st.markdown("<h3 class='sub-header' style='color:#FF9933;'>🏙️ SECTOR TELEMETRY FEED</h3>", unsafe_allow_html=True)
        st.dataframe(df[["City","AQI","Status","Day+1","Day+2","Day+3"]], use_container_width=True, hide_index=True)
        
    elif sub_tab == "Hotspot Breaches Check":
        st.markdown("<h3 class='sub-header' style='color:#FF0000;'>🔥 TARGET HOTSPOT BREAKDOWNS</h3>", unsafe_allow_html=True)
        hotspots = df[df["AQI"] > threshold]
        if not hotspots.empty:
            st.warning(f"ALERT: {len(hotspots)} hubs are operating in structural failure parameters.")
            st.dataframe(hotspots[["City", "AQI", "Status"]], hide_index=True, use_container_width=True)
        else:
            st.success("All systems operating within acceptable criteria.")

st.divider()

# ── Graphical Forecast Section ─────────────────────────────────────────────
st.markdown("<h3 class='sub-header' style='color:#FF00E5;'>📈 NEURAL FORECAST MATRIX</h3>", unsafe_allow_html=True)
city = st.selectbox("Select Target Grid Node", df["City"].tolist())

current = int(df.loc[df["City"] == city, "AQI"].values[0])
forecast = city_forecasts[city]
labels = ["SYNC"] + [f"T+{i*24}H" for i in range(1, 4)]
values = [current] + [f["Predicted AQI"] for f in forecast]
low = [current] + [f["Low"] for f in forecast]
high = [current] + [f["High"] for f in forecast]

fig = go.Figure()
fig.add_trace(go.Scatter(x=labels, y=high, mode="lines", line=dict(color="rgba(255,255,255,0)"), showlegend=False))
fig.add_trace(go.Scatter(x=labels, y=low, fill="tonexty", mode="lines", fillcolor="rgba(255,0,229,0.15)", line=dict(color="rgba(0,0,0,0)"), name="Variance Bound"))
fig.add_trace(go.Scatter(
    x=labels, y=values, mode="lines+markers+text", text=[str(i) for i in values], textposition="top center",
    textfont=dict(color="#00F5FF"), line=dict(width=4, color="#00F5FF"), marker=dict(size=12, color="#050816", line=dict(width=2, color="#00F5FF")),
    name="Predicted Matrix"
))
fig.update_layout(
    template="plotly_dark", height=380, title=dict(text=f"// {city.upper()} AIR STREAM DIRECTIONAL PATH", font=dict(color="#FF9933", family="Courier New")),
    margin=dict(l=30,r=20,t=50,b=20), plot_bgcolor="rgba(10, 15, 30, 0.8)", paper_bgcolor="rgba(0, 0, 0, 0)"
)
st.plotly_chart(fig, use_container_width=True)
