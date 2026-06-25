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
st.markdown("""
<h1 class='main-title'>
🌎 AIRVERSE AI
</h1>
""", unsafe_allow_html=True)

st.markdown(
"<center><h4 style='color:#b8c1ec'>Predict Tomorrow's Air Before It Happens 🚀</h4></center>",
unsafe_allow_html=True
)

# ── KPI Cards ────────────────────────────────────────────────────────────────
worst = df.loc[df["AQI"].idxmax()]
best  = df.loc[df["AQI"].idxmin()]
avg   = int(df["AQI"].mean())

c1, c2, c3 = st.columns(3)
c1.metric("🔴 Most Polluted", worst["City"], f"AQI {worst['AQI']}")
c2.metric("🟢 Cleanest City", best["City"],  f"AQI {best['AQI']}")
c3.metric("📊 Avg AQI (All Cities)", str(avg), aqi_label(avg))

st.divider()

# ── Table + Map ──────────────────────────────────────────────────────────────
col_map, col_tbl = st.columns([6, 4])

with col_tbl:
    st.subheader("📋 City AQI Table")
    display = df[["City","AQI","Status","Day+1","Day+2","Day+3"]].copy()
    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "AQI":   st.column_config.ProgressColumn("AQI",   min_value=0, max_value=500, format="%d"),
            "Day+1": st.column_config.ProgressColumn("Day+1", min_value=0, max_value=500, format="%d"),
            "Day+2": st.column_config.ProgressColumn("Day+2", min_value=0, max_value=500, format="%d"),
            "Day+3": st.column_config.ProgressColumn("Day+3", min_value=0, max_value=500, format="%d"),
        },
    )

with col_map:
    st.subheader("🗺️ AQI Map")
    # Build map from cached data; pass df as JSON string for a hashable cache key
    folium_map = build_folium_map(df.to_json())

    # FIX: returned_objects=[] prevents st_folium from emitting map-interaction
    # events back to Streamlit, which is the primary cause of flickering reruns.
    # A stable `key` stops the iframe from remounting on unrelated state changes.
    st_folium(
        folium_map,
        width="100%",
        height=400,
        key="aqi_map",           # stable key → no remount on reruns
        returned_objects=[],     # no interaction callbacks → no flicker reruns
    )

st.divider()

# ── Forecast Chart ───────────────────────────────────────────────────────────
st.subheader("📈 AI Forecast — Next 3 Days")
city = st.selectbox("Select city:", df["City"].tolist())

current_aqi = int(df.loc[df["City"] == city, "AQI"].values[0])
fc = city_forecasts[city]
labels = ["Today"] + [f["Date"].strftime("%a %b %d") for f in fc]
vals   = [current_aqi] + [f["Predicted AQI"] for f in fc]
lows   = [current_aqi] + [f["Low"] for f in fc]
highs  = [current_aqi] + [f["High"] for f in fc]

fig = go.Figure()
fig.add_trace(go.Scatter(x=labels, y=highs, fill=None, mode="lines",
    line=dict(color="rgba(255,100,50,0)"), showlegend=False))
fig.add_trace(go.Scatter(x=labels, y=lows, fill="tonexty", mode="lines",
    fillcolor="rgba(255,150,50,0.18)", line=dict(color="rgba(0,0,0,0)"),
    name="Confidence range"))
fig.add_trace(go.Scatter(x=labels, y=vals, mode="lines+markers+text",
    text=[str(v) for v in vals], textposition="top center",
    line=dict(color="#e74c3c", width=3),
    marker=dict(size=11, line=dict(width=2, color="white")),
    name="Predicted AQI"))

for y0, y1, col in [(0,50,"green"),(50,100,"yellow"),(100,150,"orange"),
                    (150,200,"red"),(200,300,"purple"),(300,500,"darkred")]:
    fig.add_hrect(y0=y0, y1=y1, fillcolor=col, opacity=0.05, line_width=0)

fig.update_layout(
    title=f"AQI Forecast — {city}",
    xaxis_title="Date", yaxis_title="AQI",
    template="plotly_dark", height=380,
    yaxis=dict(range=[0, max(highs + [300]) + 40]),
    margin=dict(l=40, r=20, t=50, b=40),
)
st.plotly_chart(fig, use_container_width=True)

m1, m2, m3 = st.columns(3)
for col, f in zip([m1, m2, m3], fc):
    delta = f["Predicted AQI"] - current_aqi
    col.metric(f["Date"].strftime("%A, %b %d"),
               f"AQI {f['Predicted AQI']}", f"{delta:+d} vs today",
               delta_color="inverse")

st.divider()

# ── Hotspot Detection ────────────────────────────────────────────────────────
st.subheader("🔥 Pollution Hotspots")
threshold = st.slider("AQI threshold", 50, 300, 150, step=10)
hot = df[df["AQI"] > threshold]
if len(hot):
    st.warning(f"⚠️ {len(hot)} city/cities exceed AQI {threshold}")
    st.dataframe(hot[["City","AQI","Status","Day+1","Day+2","Day+3"]],
                 hide_index=True, use_container_width=True)
else:
    st.success(f"✅ No cities exceed AQI {threshold}")
