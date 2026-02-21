"""
Build StopCoords from stops.csv
Creates a CSV of stop coordinates (lat/lng) for each stop.
"""
import pandas as pd

stops = pd.read_csv("../../data/raw/stops.csv")
coords_df = stops[["stop_id", "stop_name", "lat", "lon"]].copy()
coords_df.to_csv("../../data/processed/StopCoords.csv", index=False)
print(f"Wrote {len(coords_df)} stop coordinates to StopCoords.csv")
