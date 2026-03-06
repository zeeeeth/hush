"""
Aggregate 2024 ridership data for runtime use.

Reduces data/raw/2024.csv (1.3 GB) to a small lookup table:
    (dow, hour, station_complex_id) -> mean_ridership

Output: data/processed/ridership_by_hour.csv (~200 KB)
Run once: python training/preprocessing/aggregate_ridership.py
"""

import pandas as pd
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = REPO_ROOT / "data" / "raw" / "2024.csv"
OUT_PATH = REPO_ROOT / "data" / "processed" / "ridership_by_hour.csv"


def main():
    print(f"Loading {RAW_PATH} ...")
    df = pd.read_csv(
        RAW_PATH,
        parse_dates=["transit_timestamp"],
        date_format="%m/%d/%Y %I:%M:%S %p",
        low_memory=False,
        usecols=["transit_timestamp", "station_complex_id", "ridership"],
    )

    df["hour"] = df["transit_timestamp"].dt.hour
    df["dow"] = df["transit_timestamp"].dt.dayofweek

    # Clean ridership (commas, non-numeric)
    df["ridership"] = (
        pd.to_numeric(
            df["ridership"].astype(str).str.replace(",", ""),
            errors="coerce",
        ).fillna(0)
    )

    agg = (
        df.groupby(["dow", "hour", "station_complex_id"], as_index=False)["ridership"]
        .mean()
        .rename(columns={"ridership": "mean_ridership"})
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    agg.to_csv(OUT_PATH, index=False)
    print(f"Saved {len(agg):,} rows → {OUT_PATH}  ({OUT_PATH.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
