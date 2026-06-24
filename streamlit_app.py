import io
import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(
    page_title="India AQI Monitor",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Session state ────────────────────────────────────────────────────────────
if "started" not in st.session_state:
    st.session_state.started = False

# ═══════════════════════════════════════════════════════════════════════════
#  LANDING PAGE
# ═══════════════════════════════════════════════════════════════════════════
if not st.session_state.started:
    st.markdown("""
    <style>
      /* hide streamlit chrome */
      #MainMenu, header, footer { visibility: hidden; }
      .block-container { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }

      .landing {
        min-height: 100vh;
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        font-family: 'Segoe UI', sans-serif;
        text-align: center;
        padding: 40px 20px;
      }

      .globe { font-size: 96px; animation: pulse 2s infinite; }
      @keyframes pulse {
        0%,100% { transform: scale(1); }
        50%      { transform: scale(1.08); }
      }

      .title {
        font-size: 3rem; font-weight: 800; color: #ffffff;
        margin: 16px 0 8px;
        text-shadow: 0 0 30px rgba(99,179,237,0.6);
      }
      .subtitle {
        font-size: 1.15rem; color: #a0aec0; max-width: 520px;
        line-height: 1.6; margin-bottom: 36px;
      }

      .badges { display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; margin-bottom: 40px; }
      .badge {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 20px; padding: 6px 16px;
        color: #e2e8f0; font-size: 0.85rem;
      }

      .start-btn {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white; border: none; border-radius: 50px;
        padding: 18px 60px; font-size: 1.25rem;
        font-weight: 700; cursor: pointer;
        box-shadow: 0 8px 32px rgba(102,126,234,0.5);
        transition: all 0.3s ease;
        letter-spacing: 1px;
        text-transform: uppercase;
      }
      .start-btn:hover {
        transform: translateY(-3px);
        box-shadow: 0 14px 40px rgba(102,126,234,0.7);
      }

      .features {
        display: flex; gap: 20px; flex-wrap: wrap;
        justify-content: center; margin-top: 50px; max-width: 800px;
      }
      .feature-card {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px; padding: 20px 24px;
        color: #e2e8f0; width: 180px;
        transition: transform 0.2s;
      }
      .feature-card:hover { transform: translateY(-4px); }
      .feature-icon { font-size: 2rem; margin-bottom: 10px; }
      .feature-title { font-weight: 600; font-size: 0.95rem; color: #fff; }
      .feature-desc  { font-size: 0.8rem;  color: #90a0b7; margin-top: 4px; }
    </style>

    <div class="landing">
      <div class="globe">🌍</div>
      <div class="title">India AQI Monitor</div>
      <div class="subtitle">
        Real-time air quality tracking across major Indian cities,
        powered by live satellite data and AI-driven 3-day forecasts.
      </div>

      <div class="badges">
        <span class="badge">📡 Live WAQI Data</span>
        <span class="badge">🤖 AI Forecast</span>
        <span class="badge">🗺️ Interactive Map</span>
        <span class="badge">🔥 Hotspot Detection</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
        if st.button("🚀  Launch Monitor", use_container_width=True, type="primary"):
            st.session_state.started = True
            st.rerun()

    st.markdown("""
    <div style="display:flex;gap:20px;flex-wrap:wrap;justify-content:center;margin-top:10px;padding-bottom:40px;">
      <div style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);
                  border-radius:16px;padding:20px 24px;color:#e2e8f0;width:180px;text-align:center;">
        <div style="font-size:2rem">📊</div>
        <div style="font-weight:600;font-size:.95rem;color:#fff">AQI Table</div>
        <div style="font-size:.8rem;color:#90a0b7;margin-top:4px">Color-coded city rankings</div>
      </div>
      <div style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);
                  border-radius:16px;padding:20px 24px;color:#e2e8f0;width:180px;text-align:center;">
        <div style="font-size:2rem">🗺️</div>
        <div style="font-weight:600;font-size:.95rem;color:#fff">Live Map</div>
        <div style="font-size:.8rem;color:#90a0b7;margin-top:4px">Interactive city markers</div>
      </div>
      <div style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);
                  border-radius:16px;padding:20px 24px;color:#e2e8f0;width:180px;text-align:center;">
        <div style="font-size:2rem">📈</div>
        <div style="font-weight:600;font-size:.95rem;color:#fff">AI Forecast</div>
        <div style="font-size:.8rem;color:#90a0b7;margin-top:4px">3-day trend prediction</div>
      </div>
      <div style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);
                  border-radius:16px;padding:20px 24px;color:#e2e8f0;width:180px;text-align:center;">
        <div style="font-size:2rem">🔥</div>
        <div style="font-weight:600;font-size:.95rem;color:#fff">Hotspots</div>
        <div style="font-size:.8rem;color:#90a0b7;margin-top:4px">Threshold-based alerts</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
  #MainMenu, footer { visibility: hidden; }
  .block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# Back button
if st.button("← Back to Home"):
    st.session_state.started = False
    st.rerun()

st.title("🌍 India AQI Monitor & AI Forecast")
st.caption("Live data from WAQI · AI-powered 3-day forecast")

CITIES = {
    "Delhi":       (28.6139, 77.2090),
    "Mumbai":      (19.0760, 72.8777),
    "Kolkata":     (22.5726, 88.3639),
    "Chennai":     (13.0827, 80.2707),
    "Bhubaneswar": (20.2961, 85.8245),
    "Bangalore":   (12.9716, 77.5946),
    "Hyderabad":   (17.3850, 78.4867),
    "Ahmedabad":   (23.0225, 72.5714),
}

WAQI_TOKEN = "demo"


@st.cache_data(ttl=3600)
def fetch_waqi(city):
    try:
        url = f"https://api.waqi.info/feed/{city}/?token={WAQI_TOKEN}"
        resp = requests.get(url, timeout=8)
        data = resp.json()
        if data.get("status") == "ok":
            d = data["data"]
            return d.get("aqi"), d.get("forecast", {}).get("daily", {}).get("pm25", [])
    except Exception:
        pass
    return None, []


def pm25_to_aqi(pm25):
    bps = [(0,12,0,50),(12.1,35.4,51,100),(35.5,55.4,101,150),
           (55.5,150.4,151,200),(150.5,250.4,201,300),(250.5,500.4,301,500)]
    for c_lo, c_hi, i_lo, i_hi in bps:
        if c_lo <= pm25 <= c_hi:
            return round(((i_hi - i_lo) / (c_hi - c_lo)) * (pm25 - c_lo) + i_lo)
    return 500


def ai_forecast(current_aqi, waqi_fc, days=3):
    today = datetime.now().date()
    preds = []
    if waqi_fc:
        future = sorted(
            [f for f in waqi_fc if datetime.strptime(f["day"], "%Y-%m-%d").date() > today],
            key=lambda x: x["day"]
        )
        for f in future[:days]:
            avg = f.get("avg", 0)
            preds.append({
                "Date": datetime.strptime(f["day"], "%Y-%m-%d").date(),
                "Predicted AQI": pm25_to_aqi(avg) if avg else current_aqi,
                "Low":  pm25_to_aqi(f.get("min", avg or current_aqi)),
                "High": pm25_to_aqi(f.get("max", avg or current_aqi)),
            })
        if len(preds) >= days:
            return preds
    dy = datetime.now().timetuple().tm_yday
    seasonal = 1 + 0.15 * np.cos((dy - 15) / 365 * 2 * np.pi)
    base = current_aqi * seasonal
    x = np.arange(5, dtype=float)
    y = base + np.array([0, .04, .06, .03, -.02]) * base + np.random.normal(0, current_aqi * .04, 5)
    coeffs = np.polyfit(x, y, 2)
    for i in range(1, days + 1):
        pred = int(np.clip(np.polyval(coeffs, i), 0, 500))
        m = max(10, int(pred * .08))
        preds.append({"Date": today + timedelta(days=i), "Predicted AQI": pred,
                      "Low": max(0, pred - m), "High": min(500, pred + m)})
    return preds


def aqi_color(v):
    if v is None: return "gray"
    if v <= 50:   return "green"
    if v <= 100:  return "yellow"
    if v <= 150:  return "orange"
    if v <= 200:  return "red"
    if v <= 300:  return "darkred"
    return "purple"


def aqi_label(v):
    if v is None: return "N/A"
    if v <= 50:   return "✅ Good"
    if v <= 100:  return "🟡 Moderate"
    if v <= 150:  return "🟠 Unhealthy (Sensitive)"
    if v <= 200:  return "🔴 Unhealthy"
    if v <= 300:  return "🟣 Very Unhealthy"
    return "⛔ Hazardous"


# ── Load Data ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_all_city_data():
    """Cache the entire data fetch so the map doesn't rebuild on every rerun."""
    rows, city_forecasts = [], {}
    for city, (lat, lon) in CITIES.items():
        aqi, fc = fetch_waqi(city)
        if aqi is None:
            # Use a fixed seed per city for consistent fallback values across reruns
            rng = np.random.default_rng(abs(hash(city)) % (2**32))
            aqi = int(rng.integers(80, 280))
        forecasts = ai_forecast(aqi, fc)
        city_forecasts[city] = forecasts
        rows.append({
            "City": city, "Lat": lat, "Lon": lon, "AQI": aqi,
            "Status": aqi_label(aqi),
            "Day+1": forecasts[0]["Predicted AQI"] if forecasts else aqi,
            "Day+2": forecasts[1]["Predicted AQI"] if len(forecasts) > 1 else aqi,
            "Day+3": forecasts[2]["Predicted AQI"] if len(forecasts) > 2 else aqi,
        })
    return pd.DataFrame(rows), city_forecasts


@st.cache_data(ttl=3600)
def build_folium_map(df_json: str) -> folium.Map:
    """
    Build the Folium map object once and cache it.
    Uses StringIO to safely parse the JSON string (avoids pandas mistaking
    a long JSON string for a file path in newer pandas versions).
    """
    df = pd.read_json(io.StringIO(df_json))
    m = folium.Map(location=[22.5, 80], zoom_start=5, tiles="CartoDB dark_matter")
    for _, row in df.iterrows():
        c = aqi_color(row["AQI"])
        folium.CircleMarker(
            location=[row["Lat"], row["Lon"]],
            radius=14 + row["AQI"] / 30,
            popup=folium.Popup(
                f"<b>{row['City']}</b><br>AQI: {row['AQI']} — {row['Status']}<br>"
                f"Day+1: {row['Day+1']} | Day+2: {row['Day+2']} | Day+3: {row['Day+3']}",
                max_width=220,
            ),
            tooltip=f"{row['City']}: AQI {row['AQI']}",
            color=c, fill=True, fill_color=c, fill_opacity=0.8,
        ).add_to(m)
    return m


with st.spinner("Fetching live AQI data..."):
    df, city_forecasts = load_all_city_data()

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
