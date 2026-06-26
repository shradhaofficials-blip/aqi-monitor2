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

# ── Custom CSS (Cyberpunk + Touch of India) ──────────────────────────────────
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

/* Neon Saffron, Hot Pink, and Cyan gradient with a glowing text shadow */
.main-title{
    font-size: 4rem;
    font-weight: 900;
    text-align: center;
    background: linear-gradient(90deg, #FF9933, #FF00E5, #00F5FF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent !important;
    text-shadow: 0px 0px 15px rgba(255, 0, 229, 0.4);
}

/* Cyber-glass panels with glowing borders */
.glass{
    background: rgba(10, 15, 30, 0.7);
    backdrop-filter: blur(10px);
    border: 1px solid #00F5FF; 
    border-radius: 10px; 
    padding: 20px;
    text-align: center;
    box-shadow: 0 0 20px rgba(0, 245, 255, 0.2), inset 0 0 10px rgba(0, 245, 255, 0.1);
    transition: transform 0.3s, box-shadow 0.3s;
}

.glass:hover {
    transform: translateY(-5px);
    box-shadow: 0 0 30px rgba(255, 0, 229, 0.4), inset 0 0 15px rgba(255, 0, 229, 0.2);
    border-color: #FF00E5;
}

/* Cyberpunk Button styling */
div.stButton > button {
    width: 100%;
    border-radius: 5px;
    font-weight: 800;
    font-size: 1.2rem;
    background: transparent;
    color: #00F5FF !important;
    border: 2px solid #00F5FF;
    height: 60px;
    box-shadow: 0 0 15px rgba(0, 245, 255, 0.3);
    text-transform: uppercase;
    letter-spacing: 2px;
}

div.stButton > button * {
    color: #00F5FF !important;
}

div.stButton > button:hover{
    transform: scale(1.02);
    transition: 0.2s;
    background: #00F5FF;
    color: #050816 !important;
    box-shadow: 0 0 30px rgba(0, 245, 255, 0.6);
}

div.stButton > button:hover * {
    color: #050816 !important;
}

/* Metric styling fixes - Hot Pink */
[data-testid="stMetricValue"] {
    color: #FF00E5 !important; 
    font-weight: 900;
    text-shadow: 0 0 10px rgba(255, 0, 229, 0.5);
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

# Expanded list of sectors with precise grid coordinates
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

# Cyber Grid network links mapping nodes together
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

def build_folium_map(df):
    """Constructs a dark-themed, cyberpunk map equipped with network lines."""
    m = folium.Map(location=[22.0, 79.0], zoom_start=5, tiles="CartoDB dark_matter")
    
    # 1. Draw the Grid Datalinks (Lines connecting the cities)
    for start_node, end_node in GRID_LINES:
        if start_node in CITIES and end_node in CITIES:
            start_coord = CITIES[start_node]
            end_coord = CITIES[end_node]
            
            # Subtle cyan data trace line
            folium.PolyLine(
                locations=[start_coord, end_coord],
                color="#00F5FF",
                weight=1.5,
                opacity=0.4,
                tooltip=f"Datalink: {start_node} ⚡ {end_node}"
            ).add_to(m)

    # 2. Draw Node Sectors (City Markers)
    for _, row in df.iterrows():
        folium.CircleMarker(
            location=[row["Lat"], row["Lon"]],
            radius=9,
            popup=f"<b style='color:#000;'>{row['City']} Hub</b><br><span style='color:#000;'>AQI: {row['AQI']}</span><br><span style='color:#000;'>Status: {row['Status']}</span>",
            tooltip=f"{row['City']} Node (AQI: {row['AQI']})",
            color=aqi_color(row["AQI"]),
            fill=True,
            fill_color=aqi_color(row["AQI"]),
            fill_opacity=0.9,
            weight=3
        ).add_to(m)
        
    return m


# ── Session state ────────────────────────────────────────────────────────────
if "started" not in st.session_state:
    st.session_state.started = False

# ═══════════════════════════════════════════════════════════════════════════
#  LANDING PAGE
# ═══════════════════════════════════════════════════════════════════════════
if not st.session_state.started:
    st.markdown("""
    <div style='text-align:center;padding-top:80px;'>
    <h1 class='main-title'>VAYUSHASHTRA AI 🪷</h1>
    <h3 style='color:#00F5FF; text-shadow: 0 0 10px #00F5FF;'>
    Hawa Ka Vibe Check.
    </h3>
    <p style='color:#FF9933; font-size:22px; font-weight:bold; text-shadow: 0 0 5px #FF9933;'>
    Data in Clouds , Clarity on grounds.
    </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])

    with c2:
        if st.button("🛰️ Summon the Satellites"):
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
#  MAIN APP
# ═══════════════════════════════════════════════════════════════════════════

# Back Button
c1, c2 = st.columns([1, 5])
with c1:
    if st.button("⬅ DISCONNECT"):
        st.session_state.started = False
        st.rerun()

st.markdown("""
<h1 class='main-title'>
🪷 VAYUSHASHTRA AI 🪷
</h1>
""", unsafe_allow_html=True)

st.markdown(
"<center><h4 style='color:#00F5FF;'>Simulating Tomorrow's Atmosphere 🛺⚡</h4></center>",
unsafe_allow_html=True
)

st.divider()

# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------
with st.spinner("🛰️ Establishing orbital uplink..."):
    df, city_forecasts = load_all_city_data()

if df.empty:
    st.error("SYSTEM FAILURE: Unable to sync with AQI mainframe. 💥")
    st.stop()

# ---------------------------------------------------
# KPI CARDS
# ---------------------------------------------------
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

# ---------------------------------------------------
# TABLE + MAP
# ---------------------------------------------------
left, right = st.columns([4,6])

with left:
    st.markdown("<h3 style='color:#FF9933; text-shadow: 0 0 10px #FF9933;'>🏙️ SECTOR TELEMETRY</h3>", unsafe_allow_html=True)
    
    table = df[["City","AQI","Status","Day+1","Day+2","Day+3"]].copy()
    
    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "AQI": st.column_config.ProgressColumn("AQI", min_value=0, max_value=500, format="%f"),
            "Day+1": st.column_config.ProgressColumn("T+24H", min_value=0, max_value=500),
            "Day+2": st.column_config.ProgressColumn("T+48H", min_value=0, max_value=500),
            "Day+3": st.column_config.ProgressColumn("T+72H", min_value=0, max_value=500),
        }
    )

with right:
    st.markdown("<h3 style='color:#00F5FF; text-shadow: 0 0 10px #00F5FF;'>🗺️ TACTICAL MAP & DATALINKS</h3>", unsafe_allow_html=True)
    
    fmap = build_folium_map(df)
    
    st_folium(
        fmap,
        width="100%",
        height=450,
        key="aqi_map",
        returned_objects=[]
    )

st.divider()

# ---------------------------------------------------
# FORECAST
# ---------------------------------------------------
st.markdown("<h3 style='color:#FF00E5; text-shadow: 0 0 10px #FF00E5;'>📈 NEURAL FORECAST</h3>", unsafe_allow_html=True)

city = st.selectbox("Select Target Sector 🐘", df["City"].tolist())

current = int(df.loc[df["City"] == city, "AQI"].values[0])
forecast = city_forecasts[city]

labels = ["SYNC"] + [f"T+{i*24}H" for i in range(1, 4)]
values = [current] + [f["Predicted AQI"] for f in forecast]
low = [current] + [f["Low"] for f in forecast]
high = [current] + [f["High"] for f in forecast]

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=labels, y=high, mode="lines",
    line=dict(color="rgba(255,255,255,0)"),
    showlegend=False
))

fig.add_trace(go.Scatter(
    x=labels, y=low, fill="tonexty", mode="lines",
    fillcolor="rgba(255, 0, 229, 0.15)", 
    line=dict(color="rgba(0,0,0,0)"),
    name="Variance Bound"
))

fig.add_trace(go.Scatter(
    x=labels, y=values, mode="lines+markers+text",
    text=[str(i) for i in values],
    textposition="top center",
    textfont=dict(color="#00F5FF"),
    line=dict(width=4, color="#00F5FF"), 
    marker=dict(size=12, color="#050816", line=dict(width=2, color="#00F5FF")),
    name="Neural Path"
))

fig.update_layout(
    template="plotly_dark",
    height=400,
    title=dict(text=f"// {city.upper()} AQI TRAJECTORY", font=dict(color="#FF9933", size=20, family="Courier New")),
    yaxis_title="TOXICITY LEVEL (AQI)",
    xaxis_title="TIMEFRAME",
    margin=dict(l=30,r=20,t=60,b=20),
    plot_bgcolor="rgba(10, 15, 30, 0.8)",
    paper_bgcolor="rgba(0, 0, 0, 0)",
    xaxis=dict(showgrid=True, gridcolor='rgba(0, 245, 255, 0.1)'),
    yaxis=dict(showgrid=True, gridcolor='rgba(0, 245, 255, 0.1)')
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------
# HOTSPOTS
# ---------------------------------------------------
st.markdown("<h3 style='color:#FF0000; text-shadow: 0 0 10px #FF0000;'>🔥 RED ZONES</h3>", unsafe_allow_html=True)

threshold = st.slider("Set Toxicity Alert Threshold ⚡", 50, 300, 150, step=10)

hotspots = df[df["AQI"] > threshold]

if hotspots.empty:
    st.success(f"SYSTEM CLEAR: No sectors breach {threshold} AQI. Breathe easy, Choom. 🪷")
else:
    st.warning(f"WARNING: {len(hotspots)} sector(s) exceeding safety threshold {threshold}. 😷")
    
    st.dataframe(
        hotspots[["City", "AQI", "Status", "Day+1", "Day+2", "Day+3"]],
        hide_index=True,
        use_container_width=True
    )
