"""
Preprocessing pipeline for GNN training.
1. Load, clean and aggregate yearly CSVs (2020.csv–2024.csv)
2. Apply train/val/test split
3. Compute normalization stats from train data only
4. Build station_complex_id -> node_id mapping from train data
5. Add features and save splits

Split logic:
  - 2020–2022: train
  - 2023     : val
  - 2024     : test

Outputs (in data/processed/):
  - stats.csv           : per-station mean & std (from train only)
  - ComplexNodes.csv    : station_complex_id -> node_id mapping
  - ComplexEdges.csv    : graph edges (unchanged, validation only)
  - train.parquet       : training data
  - val.parquet         : validation data
  - test.parquet        : test data
"""

import os
import sys
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw")
PROC_DIR = os.path.join(ROOT, "data", "processed")
EDGES_PATH = os.path.join(PROC_DIR, "ComplexEdges.csv")
YEAR_FILES = [f"{y}.csv" for y in range(2020, 2025)]

# Load a single year's CSV in chunks to handle large files without running out of memory
def load_year(year: int) -> pd.DataFrame:
    path = os.path.join(RAW_DIR, f"{year}.csv")
    if not os.path.exists(path):
        print(f"  WARNING: {path} not found, skipping")
        return pd.DataFrame()

    total_rows = 0
    chunks = []
    for chunk in pd.read_csv(
        path,
        parse_dates=["transit_timestamp"],
        date_format="%m/%d/%Y %I:%M:%S %p",
        dtype={"station_complex_id": str, "ridership": str, "transfers": str},
        low_memory=True,
        chunksize=200000,
    ):
        chunks.append(chunk)
        total_rows += len(chunk)
    df = pd.concat(chunks, ignore_index=True)
    print(f"  {year}.csv: {total_rows:>12,} rows")
    return df

# Clean and aggregate ridership data
def clean(df: pd.DataFrame) -> pd.DataFrame:
    # Keep subway only
    if "transit_mode" in df.columns:
        df = df[df["transit_mode"] == "subway"].copy()

    # Clean ridership: handle commas, convert to int
    if df["ridership"].dtype == object:
        df["ridership"] = df["ridership"].str.replace(",", "").astype(int)
    else:
        df["ridership"] = df["ridership"].astype(int)

    # Clean transfers: convert to int, fill missing with 0
    if "transfers" in df.columns:
        # Remove commas, fill missing, convert to int
        if df["transfers"].dtype == object:
            df["transfers"] = df["transfers"].str.replace(",", "")
        df["transfers"] = df["transfers"].fillna(0)
        # Coerce to numeric, set errors to NaN, fill NaN with 0
        df["transfers"] = pd.to_numeric(df["transfers"], errors="coerce").fillna(0).astype(int)

    # Convert station_complex_id to int
    df["station_complex_id"] = df["station_complex_id"].astype(int)

    # Aggregate duplicates per (timestamp, station)
    df = (
        df.groupby(["transit_timestamp", "station_complex_id"], as_index=False)
        .agg({"ridership": "sum"})
    )

    df = df.sort_values(["transit_timestamp", "station_complex_id"]).reset_index(drop=True)
    return df

# Split data by year: 2020–2022 train, 2023 val, 2024 test
def split_data(df: pd.DataFrame):
    year = df["transit_timestamp"].dt.year
    train_df = df[year <= 2022].copy()
    val_df   = df[year == 2023].copy()
    test_df  = df[year == 2024].copy()
    return train_df, val_df, test_df

# Compute per-station mean and std from training data, for normalization
def compute_stats(train_df: pd.DataFrame) -> pd.DataFrame:
    stats = (
        train_df.groupby("station_complex_id")["ridership"]
        .agg(["mean", "std"])
        .reset_index()
    )
    # Fill NaN std (stations with single observation) with 1.0
    stats["std"] = stats["std"].fillna(1.0)
    return stats

# Build station_complex_id -> node_id mapping from training data
def build_node_mapping(train_df: pd.DataFrame) -> dict:
    all_stations = sorted(train_df["station_complex_id"].unique())
    mapping = {station: idx for idx, station in enumerate(all_stations)}
    return mapping

# Add features: normalized ridership, time features, and node_id. Filter to stations in ComplexNodes.
# Hour and day of week are cyclical -> sin/cos encoding to help model see that ends wrap around.
def add_features(df: pd.DataFrame, stats: pd.DataFrame, ComplexNodes: dict) -> pd.DataFrame:
    # Merge stats
    df = df.merge(stats, on="station_complex_id", how="left")

    # Stations not in training stats get default values
    df["mean"] = df["mean"].fillna(0)
    df["std"] = df["std"].fillna(1)

    # Normalize
    df["ridership_norm"] = (df["ridership"] - df["mean"]) / (df["std"] + 1e-6)

    # Time features
    df["hour"] = df["transit_timestamp"].dt.hour
    df["sin_hour"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["cos_hour"] = np.cos(2 * np.pi * df["hour"] / 24)

    # Node ID (filter to known stations)
    df = df[df["station_complex_id"].isin(ComplexNodes)].copy()
    df["node_id"] = df["station_complex_id"].map(ComplexNodes)

    df["dow"] = df["transit_timestamp"].dt.dayofweek
    df["sin_dow"] = np.sin(2 * np.pi * df["dow"] / 7)
    df["cos_dow"] = np.cos(2 * np.pi * df["dow"] / 7)

    return df

# Validate that edges only connect stations that are in the ComplexNodes mapping
def validate_edges(ComplexNodes: dict):
    """Check how many edges are valid for the node mapping."""
    edges = pd.read_csv(EDGES_PATH)
    valid = 0
    total = len(edges)
    for _, row in edges.iterrows():
        if row["from_complex_id"] in ComplexNodes and row["to_complex_id"] in ComplexNodes:
            valid += 1
    print(f"  Edges: {valid}/{total} valid for current node mapping")


def main():
    print("=" * 60)
    print("PREPROCESSING PIPELINE")
    print("=" * 60)

    # 1. Load, clean and aggregate yearly CSVs
    print("\n1. Loading, cleaning and aggregating yearly CSVs...")
    dfs = []
    total_raw_rows = 0
    for year in range(2020, 2025):
        year_df = load_year(year)
        if len(year_df) > 0:
            print(f"  Cleaning {year}...")
            year_df = clean(year_df)
            dfs.append(year_df)
            total_raw_rows += len(year_df)

    if not dfs:
        print("ERROR: No data files found. Place 2020.csv–2024.csv in data/raw/")
        sys.exit(1)

    df = pd.concat(dfs, ignore_index=True)
    print(f"  Total cleaned rows: {len(df):,}")
    print(f"  Unique stations: {df['station_complex_id'].nunique()}")
    print(f"  Date range: {df['transit_timestamp'].min()} -> {df['transit_timestamp'].max()}")

    # 2. Split data into train/val/test
    print("\n2. Splitting data...")
    train_df, val_df, test_df = split_data(df)
    total = len(train_df) + len(val_df) + len(test_df)
    print(f"  Train: {len(train_df):>12,} rows ({len(train_df)/total*100:.1f}%)")
    print(f"  Val:   {len(val_df):>12,} rows ({len(val_df)/total*100:.1f}%)")
    print(f"  Test:  {len(test_df):>12,} rows ({len(test_df)/total*100:.1f}%)")

    # 3. Compute stats from training data only to avoid data leakage
    print("\n3. Computing normalization stats...")
    stats = compute_stats(train_df)
    stats.to_csv(os.path.join(PROC_DIR, "stats.csv"), index=False)
    print(f"  Saved stats for {len(stats)} stations")

    # 4. Build node mapping from training data to avoid unseen stations in val/test
    print("\n4. Building node mapping...")
    ComplexNodes = build_node_mapping(train_df)
    mapping_df = pd.DataFrame([
        {"complex_id": k, "node_id": v} for k, v in ComplexNodes.items()
    ])
    mapping_df.to_csv(os.path.join(PROC_DIR, "ComplexNodes.csv"), index=False)
    print(f"  {len(ComplexNodes)} stations -> node IDs 0–{len(ComplexNodes)-1}")

    # Validate edges
    validate_edges(ComplexNodes)

    # 5. Add features and save splits
    print("\n5. Adding features and saving splits...")
    for name, split_df in [("train", train_df), ("val", val_df), ("test", test_df)]:
        processed = add_features(split_df, stats, ComplexNodes)
        out_path = os.path.join(PROC_DIR, f"{name}.parquet")
        processed.to_parquet(out_path, index=False)
        print(f"  {name}: {len(processed):,} rows -> {out_path}")

    # Summary
    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)
    print(f"\nOutputs in {PROC_DIR}/:")
    print("  stats.csv          - normalization stats")
    print("  ComplexNodes.csv   - station -> node ID mapping")
    print("  train.parquet      - training data")
    print("  val.parquet        - validation data")
    print("  test.parquet       - test data")
    print("\nData is ready for GNN training")

if __name__ == "__main__":
    main()
