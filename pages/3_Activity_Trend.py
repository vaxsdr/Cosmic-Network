import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from PIL import Image
from io import BytesIO

load_dotenv("api.env")

st.set_page_config(page_title="Activity Trend", layout="wide")

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

st.markdown("# 📈 Solar Activity Trend")
st.markdown("<div class='status-box'>Analyzing 30 days of NASA flare history to determine if solar activity is increasing or decreasing.</div>", unsafe_allow_html=True)
st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# Live Sun images
st.markdown("### 🌞 Current Sun — NASA SOHO Satellite")
st.markdown("<div class='status-box'>Source: NASA SOHO (Solar and Heliospheric Observatory) — approximately 17 hours behind real time.</div>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
headers = {"User-Agent": "Mozilla/5.0"}

with col1:
    try:
        r = requests.get("https://soho.nascom.nasa.gov/data/realtime/eit_195/512/latest.jpg", headers=headers, timeout=10)
        img = Image.open(BytesIO(r.content))
        st.image(img, caption="EIT 195 — Extreme Ultraviolet (shows corona and flare regions)", width=500)
    except Exception as e:
        st.markdown(f"<div class='status-box'>Image unavailable: {e}</div>", unsafe_allow_html=True)

with col2:
    try:
        r = requests.get("https://soho.nascom.nasa.gov/data/realtime/eit_284/512/latest.jpg", headers=headers, timeout=10)
        img = Image.open(BytesIO(r.content))
        st.image(img, caption="EIT 284 — Corona (shows magnetic field loops)", width=500)
    except Exception as e:
        st.markdown(f"<div class='status-box'>Image unavailable: {e}</div>", unsafe_allow_html=True)

with st.expander("What am I looking at?"):
    st.write("These are real images of the Sun taken by NASA's SOHO satellite.")
    st.write("**Left image:** Shows the Sun in extreme ultraviolet light. Bright spots are areas of intense plasma activity — these are where solar flares come from.")
    st.write("**Right image:** Shows the Sun's corona and magnetic field loops. When these loops become unstable, they can release a solar flare.")

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# Trend analysis
if st.button("🔄 Analyze 30-Day Trend"):
    with st.spinner("Fetching 30 days of NASA flare history..."):
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)

            response = requests.get("https://api.nasa.gov/DONKI/FLR", params={
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "api_key": os.getenv("NASA_API_KEY")
            })
            data = response.json()

            flares = []
            for f in data:
                try:
                    flares.append({
                        "date": pd.to_datetime(f["peakTime"]).date(),
                        "class": f["classType"],
                        "intensity": float(f["classType"][1:])
                    })
                except:
                    continue

            df = pd.DataFrame(flares)
            st.session_state["trend_data"] = df
            st.success(f"Loaded {len(df)} flare events from the last 30 days.")
        except Exception as e:
            st.error(f"NASA API error: {e}")
            st.stop()

if "trend_data" in st.session_state:
    df = st.session_state["trend_data"]

    if df.empty:
        st.markdown("<div class='alert-box'>No flares in the last 30 days. Sun is extremely quiet.</div>", unsafe_allow_html=True)
    else:
        df["date"] = pd.to_datetime(df["date"])
        midpoint = df["date"].max() - timedelta(days=15)
        first_half = df[df["date"] <= midpoint]
        second_half = df[df["date"] > midpoint]

        first_count = len(first_half)
        second_count = len(second_half)
        trend = second_count - first_count

        st.markdown("### 📊 30-Day Activity Summary")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total flares (30 days)", len(df))
        col2.metric("First 15 days", first_count)
        col3.metric("Last 15 days", second_count)
        col4.metric("Trend", f"{'↑ +' if trend > 0 else '↓ '}{trend}", delta=str(trend))

        if trend > 3:
            st.markdown("<div class='alert-box'>⚠ INCREASING ACTIVITY — Solar flares are becoming more frequent. Higher chance of network disruptions in coming days.</div>", unsafe_allow_html=True)
        elif trend < -3:
            st.markdown("<div class='status-box'>DECREASING ACTIVITY — Solar activity is calming down. Network disruption risk is falling.</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='status-box'>STABLE ACTIVITY — No significant change in solar flare frequency over the last 30 days.</div>", unsafe_allow_html=True)

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)

        daily = df.groupby("date").size().reset_index(name="flare_count")
        fig = px.bar(daily, x="date", y="flare_count",
                     title="Daily Flare Count — Last 30 Days",
                     labels={"date": "Date", "flare_count": "Number of Flares"},
                     color_discrete_sequence=["#f77f00"])
        fig.update_layout(
            paper_bgcolor="#0a0e1a", plot_bgcolor="#0d1b2a",
            font=dict(color="#e0e8ff", family="Courier New", size=13),
            xaxis=dict(gridcolor="#1e3a5f"), yaxis=dict(gridcolor="#1e3a5f")
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### ⚡ Strongest Flares This Month")
        top = df.sort_values("intensity", ascending=False).head(5)
        st.dataframe(top[["date", "class", "intensity"]], use_container_width=True)

else:
    st.markdown("<div class='status-box'>Press the button above to analyze the last 30 days of solar activity.</div>", unsafe_allow_html=True)