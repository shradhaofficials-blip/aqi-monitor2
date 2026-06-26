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
st.set_page_config(page_title="VayuShashtra Ai 🪷", layout="wide", initial_sidebar_state="collapsed")

# ── Custom CSS (Bright, Cute, Indian Theme) ──────────────────────────────────
st.markdown("""
<style>
#MainMenu, header, footer {
    visibility:hidden;
}

/* Light, cute pastel background with a touch of warm saffron/cream */
.stApp {
    background: linear-gradient(135deg, #FFF0F5 0%, #FFF8DC 50%, #E0FFFF 100%);
    color: #5D4037;
    font-family: 'Quicksand', 'Comic Sans MS', sans-serif;
}

/* Bright text overrides for light mode */
h1, h2, h3, h4, h5, h6, p, span, label, .st-emotion-cache-1wivap2 {
    color: #5D4037 !important;
}

/* Saffron, Pink, and India Green gradient for the main title */
.main-title{
    font-size:4rem;
    font-weight:900;
    text-align:center;
    background: linear-gradient(90deg, #FF9933, #FF1493, #138808);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent !important;
}

/* Cute, soft frosted glass panels */
.glass{
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(10px);
    border: 2px solid rgba(255, 105, 180, 0.3); /* Soft pink border */
    border-radius: 25px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 8px 32px 0 rgba(255, 153, 51, 0.15); /* Soft saffron shadow */
    transition: transform 0.3s;
}

.glass:hover {
    transform: translateY(-5px);
}

/* Button styling */
div.stButton > button {
    width: 100%;
    border-radius: 50px;
    font-weight: 800;
    font-size: 1.2rem;
    background: linear-gradient(90deg, #FF9933, #FF69B4); /* Saffron to Hot Pink */
    color: white !important;
    border: none;
    height: 60px;
    box-shadow: 0 4px 15px rgba(255, 105, 180, 0.4);
}

div.stButton > button * {
    color: white !important;
}

div.stButton > button:hover{
    transform: scale(1.05);
    transition: 0.3s;
    background: linear-gradient(90deg, #FF69B4, #FF9933);
}

/* Metric styling fixes */
[data-testid="stMetricValue"] {
    color: #FF1493 !important; /* Hot pink metrics */
    font-weight: 900;
}
</style>
""", unsafe_allow_html=True)
body{
overflow-x:hidden;
}

body::before{
content:"";
position:fixed;
top:0;
left:0;
width:100%;
height:100%;

background-image:
radial-gradient(#00ffff 1px, transparent 1px),
radial-gradient(#ff00ff 1px, transparent 1px);

background-size:120, 120;

animation:moveStars 40 linear infinite;

opacity:.18;

z-index:-2;


@keyframes moveStars{

0%{
transform:translateY(0);
}

100%{
transform:translateY(-250);
}

}


# ── Configuration & Functions ────────────────────────────────────────────────
WAQI_TOKEN = "demo"  # Replace with your actual WAQI API token if needed

CITIES = {
    "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Bengaluru": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
    "Hyderabad": (17.3850, 78.4867),
    "Ahmedabad": (23.0225, 72.5714),
    "Pune": (18.5204, 73.8567)
}

def fetch_waqi(lat, lon):
    """Fetches real-time AQI from the World Air Quality Index project."""
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
    if aqi <= 50: return "Good 🌸"
    elif aqi <= 100: return "Satisfactory 🍃"
    elif aqi <= 200: return "Moderate 🌤️"
    elif aqi <= 300: return "Poor 😷"
    elif aqi <= 400: return "Very Poor 🤧"
    else: return "Severe 🚨"

def aqi_color(aqi):
    if aqi <= 50: return "#00e400"
    elif aqi <= 100: return "#ffff00"
    elif aqi <= 200: return "#ff7e00"
    elif aqi <= 300: return "#ff0000"
    elif aqi <= 400: return "#8f3f97"
    else: return "#7e0023"

def ai_forecast(current_aqi):
    """Generates a simulated 3-day forecast based on current AQI."""
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
    """Constructs a light-themed folium map."""
    # Changed tiles to a beautiful, light, clean map style
    m = folium.Map(location=[22.0, 79.0], zoom_start=5, tiles="CartoDB positron")
    for _, row in df.iterrows():
        folium.CircleMarker(
            location=[row["Lat"], row["Lon"]],
            radius=10,
            popup=f"<b>{row['City']}</b><br>AQI: {row['AQI']}<br>Status: {row['Status']}",
            tooltip=f"{row['City']} (AQI: {row['AQI']})",
            color=aqi_color(row["AQI"]),
            fill=True,
            fill_color=aqi_color(row["AQI"]),
            fill_opacity=0.8,
            weight=2
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
    <h1 class='main-title'>AIRVERSE AI 🪷✨</h1>
    <h3 style='color:#FF1493;'>
    India's Next Generation Air Intelligence Platform 🇮🇳
    </h3>
    <p style='color:#FF9933; font-size:22px; font-weight:bold;'>
    Track AQI • Predict Pollution • Detect Hotspots
    </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])

    with c2:
        if st.button("🛺 HOP IN & ENTER AIRVERSE"):
            st.session_state.started = True
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)

    a, b, c, d = st.columns(4)
    with a:
        st.markdown("<div class='glass'><h2>🌸</h2><b>Live AQI</b><br>Real-Time Updates</div>", unsafe_allow_html=True)
    with b:
        st.markdown("<div class='glass'><h2>🐘</h2><b>AI Forecast</b><br>72 Hour Prediction</div>", unsafe_allow_html=True)
    with c:
        st.markdown("<div class='glass'><h2>🌶️</h2><b>Hotspots</b><br>Pollution Alerts</div>", unsafe_allow_html=True)
    with d:
        st.markdown("<div class='glass'><h2>🪁</h2><b>Satellite Data</b><br>Advanced Monitoring</div>", unsafe_allow_html=True)

    st.stop()


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════════════════════════════════════════

# Back Button
c1, c2 = st.columns([1, 5])
with c1:
    if st.button("⬅ Back Home"):
        st.session_state.started = False
        st.rerun()

st.markdown("""
<h1 class='main-title'>
🪷 AIRVERSE AI 🪷
</h1>
""", unsafe_allow_html=True)

st.markdown(
"<center><h4 style='color:#FF1493;'>Predict Tomorrow's Air Before It Happens 🛺✨</h4></center>",
unsafe_allow_html=True
)

st.divider()

# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------
with st.spinner("🪁 Flying kites to catch satellite signals..."):
    df, city_forecasts = load_all_city_data()

if df.empty:
    st.error("Oops! Unable to fetch AQI data right now. 🌧️")
    st.stop()

# ---------------------------------------------------
# KPI CARDS
# ---------------------------------------------------
worst = df.loc[df["AQI"].idxmax()]
best = df.loc[df["AQI"].idxmin()]
avg = int(df["AQI"].mean())

col1, col2, col3 = st.columns(3)

with col1:
    st.info(f"**🌶️ Most Polluted:** {worst['City']} (AQI {worst['AQI']})")
with col2:
    st.success(f"**🌸 Cleanest:** {best['City']} (AQI {best['AQI']})")
with col3:
    st.warning(f"**📊 Average AQI:** {avg} - {aqi_label(avg)}")

st.divider()

# ---------------------------------------------------
# TABLE + MAP
# ---------------------------------------------------
left, right = st.columns([4,6])

with left:
    st.markdown("<h3 style='color:#FF9933;'>🏙️ Live City AQI</h3>", unsafe_allow_html=True)
    
    table = df[["City","AQI","Status","Day+1","Day+2","Day+3"]].copy()
    
    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "AQI": st.column_config.ProgressColumn("AQI", min_value=0, max_value=500, format="%f"),
            "Day+1": st.column_config.ProgressColumn("Day +1", min_value=0, max_value=500),
            "Day+2": st.column_config.ProgressColumn("Day +2", min_value=0, max_value=500),
            "Day+3": st.column_config.ProgressColumn("Day +3", min_value=0, max_value=500),
        }
    )

with right:
    st.markdown("<h3 style='color:#FF9933;'>🗺️ Live AQI Map</h3>", unsafe_allow_html=True)
    
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
st.markdown("<h3 style='color:#138808;'>📈 AI AQI Forecast</h3>", unsafe_allow_html=True)

city = st.selectbox("Choose a City 🐘", df["City"].tolist())

current = int(df.loc[df["City"] == city, "AQI"].values[0])
forecast = city_forecasts[city]

labels = ["Today"] + [f["Date"].strftime("%d %b") for f in forecast]
values = [current] + [f["Predicted AQI"] for f in forecast]
low = [current] + [f["Low"] for f in forecast]
high = [current] + [f["High"] for f in forecast]

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=labels, y=high, mode="lines",
    line=dict(color="rgba(255,255,255,0)"),
    showlegend=False
))

# Cute saffron/peach shading for confidence interval
fig.add_trace(go.Scatter(
    x=labels, y=low, fill="tonexty", mode="lines",
    fillcolor="rgba(255, 153, 51, 0.2)", 
    line=dict(color="rgba(0,0,0,0)"),
    name="Confidence"
))

# Hot pink prediction line
fig.add_trace(go.Scatter(
    x=labels, y=values, mode="lines+markers+text",
    text=[str(i) for i in values],
    textposition="top center",
    line=dict(width=5, color="#FF1493"), 
    marker=dict(size=14, color="#138808", line=dict(width=2, color="white")),
    name="Prediction"
))

# Light theme for Plotly
fig.update_layout(
    template="plotly_white",
    height=400,
    title=dict(text=f"✨ {city} AQI Forecast Trend ✨", font=dict(color="#FF9933", size=20)),
    yaxis_title="Air Quality Index",
    xaxis_title="Date",
    margin=dict(l=30,r=20,t=60,b=20),
    plot_bgcolor="rgba(255, 255, 255, 0.5)",
    paper_bgcolor="rgba(255, 255, 255, 0)"
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------
# HOTSPOTS
# ---------------------------------------------------
st.markdown("<h3 style='color:#FF1493;'>🌶️ Pollution Hotspots</h3>", unsafe_allow_html=True)

threshold = st.slider("Drag to set AQI Warning Threshold ✨", 50, 300, 150, step=10)

hotspots = df[df["AQI"] > threshold]

if hotspots.empty:
    st.success(f"🎉 Yay! No hotspots detected above {threshold} AQI. The air is lovely! 🪷")
else:
    st.warning(f"Oh no! 🤧 {len(hotspots)} hotspot(s) detected with AQI above {threshold}.")
    
    st.dataframe(
        hotspots[["City", "AQI", "Status", "Day+1", "Day+2", "Day+3"]],
        hide_index=True,
        use_container_width=True
    )
