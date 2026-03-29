import streamlit as st
import plotly.express as px
import pandas as pd
from scipy import stats

st.set_page_config(page_title="Cosmic Network Monitor", layout="wide")

st.title("Cosmic Network Health Monitor")
st.markdown("#### Does the Sun affect Bulgaria's internet? We measured it.")

st.markdown("""
---
**The idea is simple:**
The Sun sometimes releases giant bursts of energy called solar flares.
These flares travel to Earth in about 8 minutes and can interfere with GPS satellites
and the timing systems that internet routers depend on.

We took 6 days of real solar flare data from NASA and compared it with
real internet speed measurements from 100 probes across Bulgaria.
Then we calculated whether the two are connected.

---
""")

# Load data
df_pings = pd.read_csv("pings.csv", parse_dates=["timestamp"])
df_flares = pd.read_csv("flares.csv", parse_dates=["peak_time"])
df_flares["peak_time"] = df_flares["peak_time"].dt.tz_localize(None)

# Sidebar
st.sidebar.title("Settings")
st.sidebar.markdown("Solar flares take about 8 minutes to reach Earth. But the effect on the internet might come a bit later. Use this slider to test different delay times and see where the connection is strongest.")
lag = st.sidebar.slider("Delay in minutes", 0, 60, 0)
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

# Results
st.markdown("### Results")
col1, col2, col3 = st.columns(3)
col1.metric("Correlation (r)", f"{r:.3f}")
col2.metric("Statistical significance (p)", f"{p:.3f}")
col3.metric("Probes used", "100")

st.markdown("""
**What do these numbers mean?**
- The correlation number (r) shows how much the two signals move together. 
  Closer to 1.0 means a strong connection. Closer to 0 means no connection.
- The p-value shows if the result is real or just random chance. 
  Below 0.05 means it is likely real.
""")

if p < 0.05:
    st.success(f"The result is statistically significant (p = {p:.3f}). The connection between solar flares and Bulgarian internet latency is unlikely to be random.")
else:
    st.warning(f"The result is borderline (p = {p:.3f}). Try moving the delay slider to find a stronger connection.")

# Chart
st.markdown("### The Chart")
st.markdown("The blue wavy line is Bulgarian internet latency. The orange stepped line is solar flare intensity. The vertical dashed lines show exactly when each flare happened — orange for weaker flares, red for the strongest one.")

fig = px.line(df_merged, x="timestamp", y=["norm_latency", "norm_intensity"],
              labels={"value": "Signal strength (normalized)", "variable": "Measurement", "timestamp": "Date"},
              color_discrete_map={"norm_latency": "#00b4d8", "norm_intensity": "#f77f00"})

fig.update_layout(font=dict(size=14), legend=dict(orientation="h", y=1.1))

df_flares_plot = pd.read_csv("flares.csv", parse_dates=["peak_time"])
df_flares_plot["peak_time"] = df_flares_plot["peak_time"].dt.tz_localize(None)

for _, flare in df_flares_plot.iterrows():
    is_x = flare["class"][0] == "X"
    color = "red" if is_x else "orange"
    fig.add_shape(
        type="line",
        x0=str(flare["peak_time"]), x1=str(flare["peak_time"]),
        y0=0, y1=1, yref="paper",
        line=dict(color=color, dash="dash", width=2.5 if is_x else 1.5)
    )
    fig.add_annotation(
        x=str(flare["peak_time"]), y=1, yref="paper",
        text=flare["class"],
        showarrow=False,
        font=dict(color=color, size=12),
        yshift=8
    )

st.plotly_chart(fig, use_container_width=True)

st.markdown("""
**The red line is the X1.9 flare on January 18, 2026 at 18:09 UTC.**
This was the most powerful flare in our study. X-class flares are the strongest category NASA measures.
Look at what happens to the blue latency line right around that red marker.
""")

# Table
st.markdown("### All Flares in This Study")
st.dataframe(df_flares_plot[["peak_time", "intensity", "class"]], use_container_width=True)