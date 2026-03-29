import streamlit as st
import plotly.express as px
import pandas as pd
from scipy import stats

st.set_page_config(page_title="Cosmic Network Monitor", layout="wide")
st.title("🛰️ Cosmic Network Health Monitor")
st.markdown("### Analyzing Solar Flares vs Bulgaria's Internet Latency")

# Load data
df_pings = pd.read_csv("pings.csv", parse_dates=["timestamp"])
df_flares = pd.read_csv("flares.csv", parse_dates=["peak_time"])
df_flares["peak_time"] = df_flares["peak_time"].dt.tz_localize(None)

# Lag slider
lag = st.sidebar.slider("Ionospheric Lag (minutes)", 0, 60, 0)
df_flares["peak_time"] = df_flares["peak_time"] + pd.Timedelta(minutes=lag)

# Process
df_pings = df_pings.set_index("timestamp").resample("10min").mean().reset_index()
df_merged = pd.merge_asof(
    df_pings, df_flares,
    left_on="timestamp", right_on="peak_time",
    direction="nearest", tolerance=pd.Timedelta("4hours")
).fillna(0)

# Normalize
df_merged["norm_latency"] = (df_merged["latency"] - df_merged["latency"].min()) / (df_merged["latency"].max() - df_merged["latency"].min())
df_merged["norm_intensity"] = (df_merged["intensity"] - df_merged["intensity"].min()) / (df_merged["intensity"].max() - df_merged["intensity"].min())

# Correlation
r, p = stats.pearsonr(df_merged["latency"], df_merged["intensity"])

# Metrics
col1, col2 = st.columns(2)
col1.metric("Pearson r", f"{r:.3f}")
col2.metric("P-value", f"{p:.3f}")

# Build chart ONCE
fig = px.line(df_merged, x="timestamp", y=["norm_latency", "norm_intensity"],
              title="Solar Intensity vs Network Latency (Normalized)")

# Add ALL flare markers BEFORE rendering
df_flares_plot = pd.read_csv("flares.csv", parse_dates=["peak_time"])
df_flares_plot["peak_time"] = df_flares_plot["peak_time"].dt.tz_localize(None)

for _, flare in df_flares_plot.iterrows():
    color = "red" if flare["class"][0] == "X" else "orange"
    fig.add_shape(
        type="line",
        x0=str(flare["peak_time"]), x1=str(flare["peak_time"]),
        y0=0, y1=1, yref="paper",
        line=dict(color=color, dash="dash", width=1.5)
    )
    fig.add_annotation(
        x=str(flare["peak_time"]), y=1, yref="paper",
        text=flare["class"], showarrow=False,
        font=dict(color=color, size=10), yshift=5
    )

# Render chart ONCE here
st.plotly_chart(fig, use_container_width=True)

# Table
st.write("### Flare Events")
st.dataframe(df_flares_plot[["peak_time", "intensity", "class"]])