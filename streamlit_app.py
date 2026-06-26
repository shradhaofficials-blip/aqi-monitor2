import io
import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

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

    c1,c2,c3 = st.columns([1,2,1])

    with c2:
        if st.button("⚡ ENTER AIRVERSE"):
            st.session_state.started = True
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    a,b,c,d = st.columns(4)

    with a:
        st.markdown("""
        <div class='glass'>
        <h2>⚡</h2>
        <b>Live AQI</b><br>
        Real-Time Updates
        </div>
        """, unsafe_allow_html=True)

    with b:
        st.markdown("""
        <div class='glass'>
        <h2>🤖</h2>
        <b>AI Forecast</b><br>
        72 Hour Prediction
        </div>
        """, unsafe_allow_html=True)

    with c:
        st.markdown("""
        <div class='glass'>
        <h2>🔥</h2>
        <b>Hotspots</b><br>
        Pollution Alerts
        </div>
        """, unsafe_allow_html=True)

    with d:
        st.markdown("""
        <div class='glass'>
        <h2>🛰️</h2>
        <b>Satellite Data</b><br>
        Advanced Monitoring
        </div>
        """, unsafe_allow_html=True)

    st.stop()

# ═══════════════════════════════════════════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════════════
# MAIN APP
# ════════════════════════════════════════════════════════════════

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

c1.metric(
    "🔥 Most Polluted",
    worst["City"],
    f"AQI {worst['AQI']}"
)

c2.metric(
    "🌿 Cleanest",
    best["City"],
    f"AQI {best['AQI']}"
)

c3.metric(
    "📊 Average AQI",
    avg,
    aqi_label(avg)
)

st.divider()

# ---------------------------------------------------
# TABLE + MAP
# ---------------------------------------------------

left, right = st.columns([4,6])

with left:

    st.subheader("🏙 Live City AQI")

    table = df[
        ["City","AQI","Status","Day+1","Day+2","Day+3"]
    ].copy()

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "AQI": st.column_config.ProgressColumn(
                "AQI",
                min_value=0,
                max_value=500
            ),
            "Day+1": st.column_config.ProgressColumn(
                "Day +1",
                min_value=0,
                max_value=500
            ),
            "Day+2": st.column_config.ProgressColumn(
                "Day +2",
                min_value=0,
                max_value=500
            ),
            "Day+3": st.column_config.ProgressColumn(
                "Day +3",
                min_value=0,
                max_value=500
            ),
        }
    )

with right:

    st.subheader("🗺 Live AQI Map")

    fmap = build_folium_map(df.to_json())

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

city = st.selectbox(
    "Choose City",
    df["City"].tolist()
)

current = int(
    df.loc[df["City"] == city, "AQI"].values[0]
)

forecast = city_forecasts[city]

labels = ["Today"] + [
    f["Date"].strftime("%d %b")
    for f in forecast
]

values = [current] + [
    f["Predicted AQI"]
    for f in forecast
]

low = [current] + [
    f["Low"]
    for f in forecast
]

high = [current] + [
    f["High"]
    for f in forecast
]

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=labels,
    y=high,
    mode="lines",
    line=dict(color="rgba(255,255,255,0)"),
    showlegend=False
))

fig.add_trace(go.Scatter(
    x=labels,
    y=low,
    fill="tonexty",
    mode="lines",
    fillcolor="rgba(0,255,255,.18)",
    line=dict(color="rgba(0,0,0,0)"),
    name="Confidence"
))

fig.add_trace(go.Scatter(
    x=labels,
    y=values,
    mode="lines+markers+text",
    text=[str(i) for i in values],
    textposition="top center",
    line=dict(width=4,color="#00F5FF"),
    marker=dict(size=12),
    name="Prediction"
))

fig.update_layout(
    template="plotly_dark",
    height=450,
    title=f"{city} AQI Forecast",
    yaxis_title="AQI",
    xaxis_title="Date",
    margin=dict(l=30,r=20,t=60,b=20)
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.divider()

# ---------------------------------------------------
# HOTSPOTS
# ---------------------------------------------------

st.subheader("🔥 Pollution Hotspots")

threshold = st.slider(
    "AQI Threshold",
    50,
    300,
    150,
    step=10
)

hotspots = df[df["AQI"] > threshold]

if hotspots.empty:

    st.success("🎉 No hotspot detected.")

else:

    st.warning(
        f"{len(hotspots)} hotspot(s) detected."
    )

    st.dataframe(
        hotspots[
            [
                "City",
                "AQI",
                "Status",
                "Day+1",
                "Day+2",
                "Day+3"
            ]
        ],
        hide_index=True,
        use_container_width=True
    )
