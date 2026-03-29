from ripe.atlas.cousteau import AtlasResultsRequest, ProbeRequest
import pandas as pd
from datetime import datetime

def fetch_bulgaria_latency():
    # Find active probes in Bulgaria
    filters = {"country_code": "BG", "status": 1}
    probes = ProbeRequest(**filters)
    bg_ids = [p['id'] for p in probes]
    print(f"Found {len(bg_ids)} Bulgarian probes")

    # Fetch pings around the X1.9 flare (Jan 18, 18:09 UTC)
    kwargs = {
        "msm_id": 1004,
        # In FetchingPings.py, change the time window to cover ALL your flares
        "start": datetime(2026, 1, 16, 0, 0, 0),   # start of your flare data
        "stop":  datetime(2026, 1, 21, 23, 59, 0),  # end of your flare data   # 3hrs after
        "probe_ids": bg_ids[:50]
    }
    is_success, results = AtlasResultsRequest(**kwargs).create()
    print(f"Success: {is_success}")

    pings = []
    if is_success:
        for r in results:
            if r.get('min') is not None:
                pings.append({
                    "timestamp": pd.to_datetime(r['timestamp'], unit='s'),
                    "latency": r['min']
                })

    df = pd.DataFrame(pings).sort_values("timestamp")
    print(df.head())
    return df

df_pings = fetch_bulgaria_latency()
df_pings.to_csv("pings.csv", index=False)
print("Saved!")