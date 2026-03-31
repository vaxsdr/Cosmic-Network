import streamlit as st
import pandas as pd
from scipy import stats
import plotly.express as px
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import requests
from ripe.atlas.cousteau import AtlasResultsRequest, ProbeRequest

load_dotenv("api.env")

st.set_page_config(page_title="Live Analysis", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0a0e1a; }
    .stApp * { color: #e0e8ff; }
    h1 { font-family: 'Courier New', monospace; color: #4fc3f7 !important; letter-spacing: 3px; text-transform: uppercase; }
    h3 { color: #4fc3f7 !important; font-family: 'Courier New', monospace; letter-spacing: 2px; text-transform: uppercase; }
    .stMetric { background: #0d1b2a; border: 1px solid #1e3a5f; border-radius: 8px; padding: 16px; }
    [data-testid="stMetricValue"] { color: #4fc3f7 !important; font-family: 'Courier New', monospace !important; font-size: 2.4rem !important; }
    [data-testid="stMetricLabel"] { color: #7eb8d4 !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 1px; }
    .stSidebar { background-color: #060b14 !important; border-right: 1px solid #1e3a5f; }
    .status-box { background: #0d1b2a; border-left: 3px solid #4fc3f7; padding: 12px 16px; border-radius: 4px; font-family: 'Courier New', monospace; font-size: 0.85rem; margin: 8px 0; }
    .alert-box { background: #1a0a0a; border-left: 3px solid #ff4444; padding: 12px 16px; border-radius: 4px; font-family: 'Courier New', monospace; font-size: 0.85rem; margin: 8px 0; }
    .divider { border: none; border-top: 1px solid #1e3a5f; margin: 20px 0; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 📡 Live Analysis")
st.markdown("<div class='status-box'>Fetching real-time data from NASA DONKI and RIPE Atlas. This may take 30–60 seconds.</div>", unsafe_allow_html=True)
st.markdown("<hr class='divider'>", unsafe_allow_html=True)

end_date = datetime.utcnow()
start_date = end_date - timedelta(days=7)

st.sidebar.markdown("# ⚙️ CONTROLS")
lag = st.sidebar.slider("Ionospheric Lag (minutes)", 0, 60, 0)
with st.sidebar.expander("What is ionospheric lag?"):
    st.write("Move the slider to shift flare times and find the strongest correlation with network latency.")

if st.button("🔄 Fetch Live Data"):

    # Fetch flares
    with st.spinner("Contacting NASA DONKI..."):
        try:
            response = requests.get("https://api.nasa.gov/DONKI/FLR", params={
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "api_key": os.getenv("NASA_API_KEY")
            })
            data = response.json()
            flares = []
            for f in data:
                try:
                    magnitude = float(f["classType"][1:])
                    flares.append({
                        "peak_time": pd.to_datetime(f["peakTime"]),
                        "intensity": magnitude,
                        "class": f["classType"]
                    })
                except:
                    continue
            df_flares = pd.DataFrame(flares).sort_values("peak_time") if flares else pd.DataFrame()
            # Save to session state
            st.session_state["df_flares"] = df_flares
            if df_flares.empty:
                st.warning("No flares detected in the last 7 days. The Sun is quiet!")
            else:
                st.success(f"Found {len(df_flares)} solar flare events.")
        except Exception as e:
            st.error(f"NASA API error: {e}")
            st.stop()

    # Fetch pings
    with st.spinner("Contacting RIPE Atlas (this takes ~30 seconds)..."):
        try:
            filters = {"country_code": "BG", "status": 1}
            probes = ProbeRequest(**filters)
            bg_ids = [p['id'] for p in probes]
            kwargs = {
                "msm_id": 1004,
                "start": start_date,
                "stop": end_date,
                "probe_ids": bg_ids[:50]
            }
            is_success, results = AtlasResultsRequest(**kwargs).create()
            pings = []
            if is_success:
                for r in results:
                    if r.get('min') is not None:
                        pings.append({
                            "timestamp": pd.to_datetime(r['timestamp'], unit='s'),
                            "latency": r['min']
                        })
            df_pings = pd.DataFrame(pings).sort_values("timestamp")
            # Save to session state
            st.session_state["df_pings"] = df_pings
            st.success(f"Fetched {len(df_pings)} ping measurements from {len(bg_ids)} Bulgarian probes.")
        except Exception as e:
            st.error(f"RIPE Atlas error: {e}")
            st.stop()

# ---- Everything below uses session state, so slider works instantly ----
if "df_pings" in st.session_state and "df_flares" in st.session_state:
    df_pings = st.session_state["df_pings"]
    df_flares = st.session_state["df_flares"]

    df_pings_resampled = df_pings.set_index("timestamp").resample("10min").mean().reset_index()

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown("### 📡 Live Results")

    if df_flares.empty:
        st.markdown("<div class='alert-box'>NO SOLAR FLARES DETECTED IN THE LAST 7 DAYS — Sun is currently quiet. Showing network baseline data only.</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        col1.metric("Flares found", "0")
        col2.metric("Average Latency (baseline)", f"{df_pings['latency'].mean():.2f} ms")

        fig = px.line(df_pings_resampled, x="timestamp", y="latency",
                      title="Bulgarian Internet Latency — Last 7 Days (No Flare Activity)",
                      labels={"latency": "Latency (ms)", "timestamp": "Date"},
                      color_discrete_sequence=["#4fc3f7"])
        fig.update_layout(
            paper_bgcolor="#0a0e1a", plot_bgcolor="#0d1b2a",
            font=dict(color="#e0e8ff", family="Courier New", size=13),
            xaxis=dict(gridcolor="#1e3a5f"), yaxis=dict(gridcolor="#1e3a5f")
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        df_flares = df_flares.copy()
        df_flares["peak_time"] = df_flares["peak_time"].dt.tz_localize(None)
        df_flares["peak_time"] = df_flares["peak_time"] + pd.Timedelta(minutes=lag)

        df_merged = pd.merge_asof(
            df_pings_resampled, df_flares,
            left_on="timestamp", right_on="peak_time",
            direction="nearest", tolerance=pd.Timedelta("4hours")
        ).fillna(0)

        df_merged["norm_latency"] = (df_merged["latency"] - df_merged["latency"].min()) / (df_merged["latency"].max() - df_merged["latency"].min())
        df_merged["norm_intensity"] = (df_merged["intensity"] - df_merged["intensity"].min()) / (df_merged["intensity"].max() - df_merged["intensity"].min())

        r_val, p_val = stats.pearsonr(df_merged["latency"], df_merged["intensity"])

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Pearson r", f"{r_val:.3f}")
        col2.metric("P-value", f"{p_val:.3f}")
        col3.metric("Significance", "YES ✓" if p_val < 0.05 else "NO")
        col4.metric("Flares found", len(df_flares))

        fig = px.line(df_merged, x="timestamp", y=["norm_latency", "norm_intensity"],
                      labels={"value": "Normalized Signal", "variable": "Measurement", "timestamp": "Date"},
                      color_discrete_map={"norm_latency": "#4fc3f7", "norm_intensity": "#f77f00"})
        fig.update_layout(
            paper_bgcolor="#0a0e1a", plot_bgcolor="#0d1b2a",
            font=dict(color="#e0e8ff", family="Courier New", size=13),
            xaxis=dict(gridcolor="#1e3a5f"), yaxis=dict(gridcolor="#1e3a5f"),
            legend=dict(orientation="h", y=1.1, bgcolor="rgba(0,0,0,0)")
        )

        for _, flare in df_flares.iterrows():
            is_x = flare["class"][0] == "X"
            color = "#ff4444" if is_x else "#ff9900"
            fig.add_shape(type="line",
                x0=str(flare["peak_time"]), x1=str(flare["peak_time"]),
                y0=0, y1=1, yref="paper",
                line=dict(color=color, dash="dash", width=2.5 if is_x else 1.5))
            fig.add_annotation(
                x=str(flare["peak_time"]), y=1, yref="paper",
                text=flare["class"], showarrow=False,
                font=dict(color=color, size=11, family="Courier New"), yshift=8)

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 🗂 Live Flare Event Log")
        st.dataframe(df_flares[["peak_time", "intensity", "class"]], use_container_width=True)

else:
    st.markdown("<div class='status-box'>Press the button above to fetch live data from NASA and RIPE Atlas.</div>", unsafe_allow_html=True)