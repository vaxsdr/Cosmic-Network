import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Solar Forecast", layout="wide")

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

st.markdown("# ☀️ Solar Activity Forecast")
st.markdown("<div class='status-box'>Data source: NOAA Space Weather Prediction Center — updated every 30 minutes.</div>", unsafe_allow_html=True)
st.markdown("<hr class='divider'>", unsafe_allow_html=True)

if st.button("🔄 Fetch NOAA Forecast"):
    with st.spinner("Contacting NOAA..."):
        try:
            # Fetch 3-day solar flare probability forecast
            url = "https://services.swpc.noaa.gov/json/solar_probabilities.json"
            response = requests.get(url)
            data = response.json()

            df = pd.DataFrame(data)
            st.session_state["noaa_data"] = df
            st.success("NOAA forecast loaded successfully.")
        except Exception as e:
            st.error(f"NOAA API error: {e}")
            st.stop()

if "noaa_data" in st.session_state:
    df = st.session_state["noaa_data"]

    st.markdown("### 📡 3-Day Solar Flare Probability")
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # Show latest forecast
    latest = df.iloc[-1]

    col1, col2, col3 = st.columns(3)
    col1.metric("C-class flare chance", f"{latest.get('c_class_1_day', 'N/A')}%", help="Weak flare — unlikely to affect networks")
    col2.metric("M-class flare chance", f"{latest.get('m_class_1_day', 'N/A')}%", help="Moderate flare — may cause minor disruptions")
    col3.metric("X-class flare chance", f"{latest.get('x_class_1_day', 'N/A')}%", help="Powerful flare — most likely to affect Bulgarian internet")

    # Risk level
    x_prob = int(latest.get('x_class_1_day', 0))
    m_prob = int(latest.get('m_class_1_day', 0))

    if x_prob >= 10:
        st.markdown("<div class='alert-box'>⚠ HIGH RISK — X-class flare probability is significant. Bulgarian internet infrastructure may experience disruptions in the next 24 hours.</div>", unsafe_allow_html=True)
    elif m_prob >= 40:
        st.markdown("<div class='status-box'>MODERATE RISK — M-class activity likely. Minor network timing disruptions possible.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='status-box'>LOW RISK — Solar activity is calm. No significant network disruptions expected.</div>", unsafe_allow_html=True)

    with st.expander("What do these probabilities mean?"):
        st.write("NOAA calculates these percentages based on the current state of active sunspot regions on the Sun.")
        st.write("**C-class** flares are weak and rarely affect ground infrastructure.")
        st.write("**M-class** flares are moderate and can cause minor disruptions to GPS and satellite systems.")
        st.write("**X-class** flares are the most powerful and are most likely to affect internet timing systems.")

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown("### 🗂 Full Forecast Data")
    st.dataframe(df, use_container_width=True)

else:
    st.markdown("<div class='status-box'>Press the button above to fetch the latest NOAA solar forecast.</div>", unsafe_allow_html=True)