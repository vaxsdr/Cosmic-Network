import pandas as pd
from scipy import stats

# Load your saved data
df_pings = pd.read_csv("pings.csv", parse_dates=["timestamp"])
df_flares = pd.read_csv("flares.csv", parse_dates=["peak_time"])

# Fix timezone mismatch
df_flares["peak_time"] = df_flares["peak_time"].dt.tz_localize(None)

# Resample pings into 10-minute averages
df_pings = df_pings.set_index("timestamp").resample("10min").mean().reset_index()

# Align pings with nearest flare
df_merged = pd.merge_asof(
    df_pings,
    df_flares,
    left_on="timestamp",
    right_on="peak_time",
    direction="nearest",
    tolerance=pd.Timedelta("2hours")
).fillna(0)

# Calculate correlation
r, p_value = stats.pearsonr(df_merged["latency"], df_merged["intensity"])

print(f"Pearson r = {r:.3f}")
print(f"P-value   = {p_value:.3f}")
print(df_merged[["timestamp", "latency", "intensity"]].head(10))

