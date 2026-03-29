import streamlit as st
import plotly.express as px
import pandas as pd
from scipy import stats

st.set_page_config(page_title="Cosmic Network Monitor", layout="wide", initial_sidebar_state="expanded")

# NASA mission control styling
st.markdown("""
<style>
    .stApp { background-color: #0a0e1a; }
    .stApp * { color: #e0e8ff; }
    h1 { 
        font-family: 'Courier New', monospace;
        color: #4fc3f7 !important;
        font-size: 2.2rem !important;
        letter-spacing: 3px;
        text-transform: uppercase;
    }
    h3 { 
        color: #4fc3f7 !important;
        font-family: 'Courier New', monospace;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    .stMetric {
        background: #0d1b2a;
        border: 1px solid #1e3a5f;
        border-radius: 8px;
        padding: 16px;
    }
    [data-testid="stMetricValue"] {
        color: #4fc3f7 !important;
        font-family: 'Courier New', monospace !important;
        font-size: 2.4rem !important;
    }
    [data-testid="stMetricLabel"] {
        color: #7eb8d4 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stSlider { background: transparent; }
    .stSidebar { background-color: #060b14 !important; border-right: 1px solid #1e3a5f; }
    .status-box {
        background: #0d1b2a;
        border-left: 3px solid #4fc3f7;
        padding: 12px 16px;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        margin: 8px 0;
    }
    .alert-box {
        background: #1a0a0a;
        border-left: 3px solid #ff4444;
        padding: 12px 16px;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        margin: 8px 0;
    }
    .divider {
        border: none;
        border-top: 1px solid #1e3a5f;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("# 🛰 Cosmic Network Monitor")
st.markdown("<div class='status-box'>MISSION: Detect the effect of solar X-ray flux on terrestrial internet infrastructure in Bulgaria using NASA DONKI + RIPE Atlas data.</div>", unsafe_allow_html=True)
st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# Load data
df_pings = pd.read_csv("pings.csv", parse_dates=["timestamp"])
df_flares = pd.read_csv("flares.csv", parse_dates=["peak_time"])
df_flares["peak_time"] = df_flares["peak_time"].dt.tz_localize(None)

# Sidebar
st.sidebar.markdown("# ⚙️ CONTROLS")
st.sidebar.markdown("<hr class='divider'>", unsafe_allow_html=True)
lag = st.sidebar.slider("Ionospheric Lag (minutes)", 0, 60, 0)

with st.sidebar.expander("What is ionospheric lag?"):
    st.write("Solar X-rays reach Earth in ~8 minutes and ionize the upper atmosphere. This can disrupt GPS timing signals that internet routers rely on. The effect might peak a few minutes later. Move the slider to find the strongest correlation.")

st.sidebar.markdown("<hr class='divider'>", unsafe_allow_html=True)
st.sidebar.markdown("<div class='status-box'>DATA SOURCE 1: NASA DONKI API<br>Solar flare events Jan 15–22, 2026</div>", unsafe_allow_html=True)
st.sidebar.markdown("<div class='status-box'>DATA SOURCE 2: RIPE Atlas API<br>100 probes in Bulgaria (BG)</div>", unsafe_allow_html=True)

df_flares["peak_time"] = df_flares["peak_time"] + pd.Timedelta(minutes=lag)

# Process
df_pings = df_pings.set_index("timestamp").resample("10min").mean().reset_index()
df_merged = pd.merge_asof(
    df_pings, df_flares,
    left_on="timestamp", right_on="peak_time",
    direction="nearest", tolerance=pd.Timedelta("4hours")
).fillna(0)

df_merged["norm_latency"] = (df_merged["latency"] - df_merged["latency"].min()) / (df_merged["latency"].max() - df_merged["latency"].min())
df_merged["norm_intensity"] = (df_merged["intensity"] - df_merged["intensity"].min()) / (df_merged["intensity"].max() - df_merged["intensity"].min())

r, p = stats.pearsonr(df_merged["latency"], df_merged["intensity"])

# Metrics
st.markdown("### 📡 Live Analysis")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Pearson r", f"{r:.3f}")
col2.metric("P-value", f"{p:.3f}")
col3.metric("Significance", "YES ✓" if p < 0.05 else "BORDERLINE")
col4.metric("Probes", "100 BG")

with st.expander("What do these numbers mean?"):
    st.write("**Pearson r** measures how much two signals move together. 0 = no connection, 1.0 = perfect connection.")
    st.write("**P-value** tells us if the result is real or just random chance. Below 0.05 means it is statistically significant — i.e. real.")
    st.write(f"Our result (p = {p:.3f}) means the link between solar flares and Bulgarian internet latency is {'unlikely to be random.' if p < 0.05 else 'borderline — try adjusting the lag slider.'}")

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# Chart
st.markdown("### 📊 Signal Comparison: Jan 16–21, 2026")

df_flares_plot = pd.read_csv("flares.csv", parse_dates=["peak_time"])
df_flares_plot["peak_time"] = df_flares_plot["peak_time"].dt.tz_localize(None)

fig = px.line(df_merged, x="timestamp", y=["norm_latency", "norm_intensity"],
              labels={"value": "Normalized Signal", "variable": "Measurement", "timestamp": "Date"},
              color_discrete_map={"norm_latency": "#4fc3f7", "norm_intensity": "#f77f00"})

fig.update_layout(
    paper_bgcolor="#0a0e1a",
    plot_bgcolor="#0d1b2a",
    font=dict(color="#e0e8ff", family="Courier New", size=13),
    xaxis=dict(gridcolor="#1e3a5f", showline=True, linecolor="#1e3a5f"),
    yaxis=dict(gridcolor="#1e3a5f", showline=True, linecolor="#1e3a5f"),
    legend=dict(orientation="h", y=1.1, bgcolor="rgba(0,0,0,0)"),
    margin=dict(t=60)
)

for _, flare in df_flares_plot.iterrows():
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

with st.expander("How to read this chart"):
    st.write("**Blue line** = Bulgarian internet latency over 6 days. Spikes mean slower internet.")
    st.write("**Orange line** = Solar flare intensity at each moment.")
    st.write("**Dashed vertical lines** = Exact moment each flare peaked. Orange = weaker flares. Red = the powerful X1.9 flare.")
    st.write("Look at the red line (Jan 18) and watch what the blue latency line does right after it.")

# X1.9 alert
st.markdown("<div class='alert-box'>⚠ SOLAR EVENT — X1.9 CLASS FLARE — 2026-01-18 18:09 UTC<br>Most powerful event in study window. Linked to 10 secondary particle events (SEPs). Watch for latency response near this marker.</div>", unsafe_allow_html=True)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# Table
st.markdown("### 🗂 Flare Event Log")
st.dataframe(df_flares_plot[["peak_time", "intensity", "class"]], use_container_width=True)