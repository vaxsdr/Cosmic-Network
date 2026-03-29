import requests
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

def fetch_nasa_flares():
    url = "https://api.nasa.gov/DONKI/FLR"
    params = {
        "startDate": "2026-01-15",
        "endDate": "2026-01-22",
        "api_key": os.getenv("NASA_API_KEY")
    }
    response = requests.get(url, params=params)
    print(response.status_code)
    print(response.json())
    data = response.json()

    flares = []
    for f in data:
        magnitude = float(f["classType"][1:])
        flares.append({
            "peak_time": pd.to_datetime(f["peakTime"]),
            "intensity": magnitude,
            "class": f["classType"]
        })
    return pd.DataFrame(flares).sort_values("peak_time")

df_flares = fetch_nasa_flares()
print(df_flares)


df_flares = fetch_nasa_flares()
df_flares.to_csv("flares.csv", index=False)
print("Saved!")
