"""
Preprocessing pipeline for GNN training.

Loads yearly CSVs (2020.csv–2024.csv), applies the train/val/test split,
computes normalization stats from train data only, and saves processed
artifacts used by train.py and evaluate.py.

Split logic:
  - 2020–2022: 100% train
  - 2023–2024: stratified random split to achieve 75% train, 5% val, 20% test overall

Outputs (in data/processed/):
  - stats.csv           : per-station mean & std (from train only)
  - ComplexNodes.csv   : station_complex_id -> node_id mapping
  - ComplexEdges.csv   : graph edges (unchanged, just validated)
  - train.parquet       : preprocessed training data
  - val.parquet         : preprocessed validation data
  - test.parquet        : preprocessed test data
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


def load_year(year: int) -> pd.DataFrame:
    """Load a single year's CSV."""
    path = os.path.join(RAW_DIR, f"{year}.csv")
    if not os.path.exists(path):
        print(f"  WARNING: {path} not found, skipping")
        return pd.DataFrame()

    chunk_size = 200000  # Adjust as needed for your system
    total_rows = 0
    chunks = []
    for chunk in pd.read_csv(
        path,
        parse_dates=["transit_timestamp"],
        date_format="%m/%d/%Y %I:%M:%S %p",
        dtype={"station_complex_id": str, "ridership": str, "transfers": str},
        low_memory=True,
        chunksize=chunk_size,
    ):
        chunks.append(chunk)
        total_rows += len(chunk)
    df = pd.concat(chunks, ignore_index=True)
    print(f"  {year}.csv: {total_rows:>12,} rows (loaded in chunks)")
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and aggregate ridership data."""
    # Keep subway only
    if "transit_mode" in df.columns:
        df = df[df["transit_mode"] == "subway"].copy()

    # Clean ridership (handle commas)
    if df["ridership"].dtype == object:
        df["ridership"] = df["ridership"].str.replace(",", "").astype(int)
    else:
        df["ridership"] = df["ridership"].astype(int)

    # Clean transfers (convert to int, fill missing with 0)
    if "transfers" in df.columns:
        # Remove commas, fill missing, convert to int
        if df["transfers"].dtype == object:
            df["transfers"] = df["transfers"].str.replace(",", "")
        df["transfers"] = df["transfers"].fillna(0)
        # If any non-numeric, coerce to NaN then fill with 0
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


def split_data(df: pd.DataFrame):
    """
    Split into train/val/test.

    2020–2022: all train
    2023–2024: stratified random split to achieve 75% train, 5% val, 20% test overall
    """
    year = df["transit_timestamp"].dt.year
    is_early_year = year <= 2022
    is_late_year = (year >= 2023) & (year <= 2024)

    # 2020-2022: all train
    train_mask = is_early_year

    # 2023-2024: stratified random split
    late_df = df[is_late_year].copy()
    n = len(late_df)
    n_train = int(n * 0.375)  # 3/8 of late years = 75% overall
    n_val = int(n * 0.025)    # 1/40 of late years = 5% overall
    n_test = n - n_train - n_val

    late_df = late_df.sample(frac=1, random_state=42).reset_index(drop=True)
    train_late = late_df.iloc[:n_train]
    val_late = late_df.iloc[n_train:n_train+n_val]
    test_late = late_df.iloc[n_train+n_val:]

    train_df = pd.concat([df[train_mask], train_late], ignore_index=True)
    val_df = val_late
    test_df = test_late

    return train_df, val_df, test_df


def compute_stats(train_df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-station mean and std from training data only."""
    stats = (
        train_df.groupby("station_complex_id")["ridership"]
        .agg(["mean", "std"])
        .reset_index()
    )
    # Fill NaN std (stations with single observation) with 1.0
    stats["std"] = stats["std"].fillna(1.0)
    return stats


def build_node_mapping(train_df: pd.DataFrame) -> dict:
    """Build station_complex_id -> node_id mapping from training data."""
    all_stations = sorted(train_df["station_complex_id"].unique())
    mapping = {station: idx for idx, station in enumerate(all_stations)}
    return mapping


def add_features(df: pd.DataFrame, stats: pd.DataFrame, ComplexNodes: dict) -> pd.DataFrame:
    """Add normalized ridership, time features, and node_id."""
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

    return df


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

    # ------------------------------------------------------------------
    # 1. Load all years
    # ------------------------------------------------------------------
    print("\n1. Loading yearly CSVs...")
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
        print("ERROR: No data files found. Place 2020.csv–2025.csv in data/raw/")
        sys.exit(1)

    df = pd.concat(dfs, ignore_index=True)
    print(f"  Total cleaned rows: {len(df):,}")
    print(f"  Unique stations: {df['station_complex_id'].nunique()}")
    print(f"  Date range: {df['transit_timestamp'].min()} -> {df['transit_timestamp'].max()}")

    # ------------------------------------------------------------------
    # 3. Split
    # ------------------------------------------------------------------
    print("\n3. Splitting data...")
    train_df, val_df, test_df = split_data(df)
    total = len(train_df) + len(val_df) + len(test_df)
    print(f"  Train: {len(train_df):>12,} rows ({len(train_df)/total*100:.1f}%)")
    print(f"  Val:   {len(val_df):>12,} rows ({len(val_df)/total*100:.1f}%)")
    print(f"  Test:  {len(test_df):>12,} rows ({len(test_df)/total*100:.1f}%)")

    # ------------------------------------------------------------------
    # 4. Compute stats from train only
    # ------------------------------------------------------------------
    print("\n4. Computing normalization stats (train only)...")
    stats = compute_stats(train_df)
    stats.to_csv(os.path.join(PROC_DIR, "stats.csv"), index=False)
    print(f"  Saved stats for {len(stats)} stations")

    # ------------------------------------------------------------------
    # 5. Build node mapping from train
    # ------------------------------------------------------------------
    print("\n5. Building node mapping...")
    ComplexNodes = build_node_mapping(train_df)
    mapping_df = pd.DataFrame([
        {"complex_id": k, "node_id": v} for k, v in ComplexNodes.items()
    ])
    mapping_df.to_csv(os.path.join(PROC_DIR, "ComplexNodes.csv"), index=False)
    print(f"  {len(ComplexNodes)} stations -> node IDs 0–{len(ComplexNodes)-1}")

    # Validate edges
    validate_edges(ComplexNodes)

    # ------------------------------------------------------------------
    # 6. Add features and save splits
    # ------------------------------------------------------------------
    print("\n6. Adding features and saving splits...")

    for name, split_df in [("train", train_df), ("val", val_df), ("test", test_df)]:
        processed = add_features(split_df, stats, ComplexNodes)
        out_path = os.path.join(PROC_DIR, f"{name}.parquet")
        processed.to_parquet(out_path, index=False)
        print(f"  {name}: {len(processed):,} rows -> {out_path}")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)
    print(f"\nOutputs in {PROC_DIR}/:")
    print("  stats.csv          - normalization stats (train only)")
    print("  ComplexNodes.csv   - station -> node ID mapping")
    print("  train.parquet      - training data")
    print("  val.parquet        - validation data")
    print("  test.parquet       - test data")
    print("\nNext: python training/train.ipynb")


if __name__ == "__main__":
    main()
