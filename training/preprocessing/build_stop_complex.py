"""
Build StopComplex from yearly ridership CSVs
Creates a CSV mapping stop names to complex IDs using ridership data.
"""
import pandas as pd
import glob

# Use stop-complex mappings from all years 2020-2024
files = glob.glob("../../data/raw/202*.csv")
frames = [pd.read_csv(f) for f in files]
df = pd.concat(frames, ignore_index=True)

if "stop_name" in df.columns and "station_complex_id" in df.columns:
    stop_complex = df[["stop_name", "station_complex_id"]].drop_duplicates()
    stop_complex.to_csv("../../data/processed/StopComplex.csv", index=False)
    print(f"Wrote {len(stop_complex)} stop-complex mappings to StopComplex.csv")
else:
    print("stop_name or station_complex_id not found in input files.")
