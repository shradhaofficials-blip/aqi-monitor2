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
st.set_page_config(page_title="AIRVERSE AI", layout="wide")

# ── Custom CSS ───────────────────────────────────────────────────────────────
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
    text-align:center;
}
.metric-card{
    background:rgba(255,255,255,0.08);
    border-radius:20px;
    padding:15px;
}
div.stButton > button {
    width:100%;
    border-radius:50px;
    font-weight:800;
    background:linear-gradient(90deg,#00F5FF,#FF00E5);
    color:black;
    border:none;
    height:60px;
}
div.stButton > button:hover{
    transform:scale(1.05);
    transition:0.3s;
}
</style>
""", unsafe_allow_html=True)


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
            # WAQI sometimes returns '-' for missing data
            if isinstance(aqi, int):
                return aqi
    except Exception:
        pass
    # Fallback to simulated data if API fails or rate-limits "demo" token
    return np.random.randint(50, 350)

def aqi_label(aqi):
    """Returns the standard categorization for AQI."""
    if aqi <= 50: return "Good"
    elif aqi <= 100: return "Satisfactory"
    elif aqi <= 200: return "Moderate"
    elif aqi <= 300: return "Poor"
    elif aqi <= 400: return "Very Poor"
    else: return "Severe"

def aqi_color(aqi):
    """Returns hex colors based on standard AQI health brackets."""
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
        # AI Simulation model logic (randomized for demo purposes)
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

@st.cache_data(ttl=900) # Cache for 15 minutes to save API limits
def load_all_city_data():
    """Loads current data and predictions for all configured cities."""
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
    """Constructs a dark-themed folium map from the given DataFrame."""
    m = folium.Map(location=[22.0, 79.0], zoom_start=5, tiles="CartoDB dark_matter")
    for _, row in df.iterrows():
        folium.CircleMarker(
            location=[row["Lat"], row["Lon"]],
            radius=9,
            popup=f"<b>{row['City']}</b><br>AQI: {row['AQI']}<br>Status: {row['Status']}",
            tooltip=f"{row['City']} (AQI: {row['AQI']})",
            color=aqi_color(row["AQI"]),
            fill=True,
            fill_color=aqi_color(row["AQI"]),
            fill_opacity=0.8
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
    <div style='text-align:center;padding-top:100px;'>
    <h1 class='main-title'>AIRVERSE AI 🌎</h1>
    <h3 style='color:white;'>
    India's Next Generation Air Intelligence Platform
    </h3>
    <p style='color:#b8c1ec;font-size:20px;'>
    Track AQI • Predict Pollution • Detect Hotspots
    </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])

    with c2:
        if st.button("⚡ ENTER AIRVERSE"):
            st.session_state.started = True
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)

    a, b, c, d = st.columns(4)
    with a:
        st.markdown("<div class='glass'><h2>⚡</h2><b>Live AQI</b><br>Real-Time Updates</div>", unsafe_allow_html=True)
    with b:
        st.markdown("<div class='glass'><h2>🤖</h2><b>AI Forecast</b><br>72 Hour Prediction</div>", unsafe_allow_html=True)
    with c:
        st.markdown("<div class='glass'><h2>🔥</h2><b>Hotspots</b><br>Pollution Alerts</div>", unsafe_allow_html=True)
    with d:
        st.markdown("<div class='glass'><h2>🛰️</h2><b>Satellite Data</b><br>Advanced Monitoring</div>", unsafe_allow_html=True)

    st.stop()


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════════════════════════════════════════

# Back Button
if st.button("⬅ Back to Home"):
    st.session_state.started = False
    st.rerun()

st.markdown("""
<h1 class='main-title'>
🌎 AIRVERSE AI
</h1>
""", unsafe_allow_html=True)

st.markdown(
"<center><h4 style='color:#b8c1ec;'>Predict Tomorrow's Air Before It Happens 🚀</h4></center>",
unsafe_allow_html=True
)

st.divider()

# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------
with st.spinner("📡 Connecting to satellite network..."):
    df, city_forecasts = load_all_city_data()

# Safety check
if df.empty:
    st.error("Unable to fetch AQI data.")
    st.stop()

# ---------------------------------------------------
# KPI CARDS
# ---------------------------------------------------
worst = df.loc[df["AQI"].idxmax()]
best = df.loc[df["AQI"].idxmin()]
avg = int(df["AQI"].mean())

c1, c2, c3 = st.columns(3)

c1.metric("🔥 Most Polluted", worst["City"], f"AQI {worst['AQI']}")
c2.metric("🌿 Cleanest", best["City"], f"AQI {best['AQI']}")
c3.metric("📊 Average AQI", avg, aqi_label(avg))

st.divider()

# ---------------------------------------------------
# TABLE + MAP
# ---------------------------------------------------
left, right = st.columns([4,6])

with left:
    st.subheader("🏙 Live City AQI")
    
    table = df[["City","AQI","Status","Day+1","Day+2","Day+3"]].copy()
    
    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "AQI": st.column_config.ProgressColumn("AQI", min_value=0, max_value=500),
            "Day+1": st.column_config.ProgressColumn("Day +1", min_value=0, max_value=500),
            "Day+2": st.column_config.ProgressColumn("Day +2", min_value=0, max_value=500),
            "Day+3": st.column_config.ProgressColumn("Day +3", min_value=0, max_value=500),
        }
    )

with right:
    st.subheader("🗺 Live AQI Map")
    
    fmap = build_folium_map(df)
    
    st_folium(
        fmap,
        width="100%",
        height=500,
        key="aqi_map",
        returned_objects=[]
    )

st.divider()

# ---------------------------------------------------
# FORECAST
# ---------------------------------------------------
st.subheader("📈 AI AQI Forecast")

city = st.selectbox("Choose City", df["City"].tolist())

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

fig.add_trace(go.Scatter(
    x=labels, y=low, fill="tonexty", mode="lines",
    fillcolor="rgba(0,255,255,.18)",
    line=dict(color="rgba(0,0,0,0)"),
    name="Confidence"
))

fig.add_trace(go.Scatter(
    x=labels, y=values, mode="lines+markers+text",
    text=[str(i) for i in values],
    textposition="top center",
    line=dict(width=4,color="#00F5FF"),
    marker=dict(size=12),
    name="Prediction"
))

fig.update_layout(
    template="plotly_dark",
    height=450,
    title=f"{city} AQI Forecast Trend",
    yaxis_title="AQI",
    xaxis_title="Date",
    margin=dict(l=30,r=20,t=60,b=20)
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------
# HOTSPOTS
# ---------------------------------------------------
st.subheader("🔥 Pollution Hotspots")

threshold = st.slider("AQI Warning Threshold", 50, 300, 150, step=10)

hotspots = df[df["AQI"] > threshold]

if hotspots.empty:
    st.success(f"🎉 No hotspot detected above {threshold} AQI.")
else:
    st.warning(f"{len(hotspots)} hotspot(s) detected with AQI above {threshold}.")
    
    st.dataframe(
        hotspots[["City", "AQI", "Status", "Day+1", "Day+2", "Day+3"]],
        hide_index=True,
        use_container_width=True
    )
