"""
Build GTFS stop sequences lookup.
Reads stop_times.csv + stops.csv and produces data/processed/StopSequences.json.

Output:
{
  "A": [["stop1", "stop2", "stop3"], ...],
  "1": [["Van Cortlandt Park-242 St", "238 St", ...], ...],
  ...
}

Each inner list is a unique ordered stop-name sequence for that route.
"""

import json
import re
import os
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STOPS_PATH = os.path.join(ROOT, "data", "raw", "stops.csv")
STOP_TIMES_PATH = os.path.join(ROOT, "data", "raw", "stop_times.csv")
OUTPUT_PATH = os.path.join(ROOT, "data", "processed", "StopSequences.json")

ROUTE_RE = re.compile(r"_([A-Z0-9]+)\.\.")

# Extract route ID from trip_ID using regex
def extract_route(trip_id: str) -> str | None:
    m = ROUTE_RE.search(trip_id)
    return m.group(1) if m else None


def main():
    # Build a lookup of stop_id -> stop_name from stops.csv
    print("Loading stops...")
    stops_df = pd.read_csv(STOPS_PATH, usecols=["stop_id", "stop_name"], dtype=str)
    stop_name_map = dict(zip(stops_df["stop_id"], stops_df["stop_name"]))

    # Extract route_id from each trip_id, map stop_id -> stop_name, drop rows with missing data
    print("Loading stop_times...")
    st_df = pd.read_csv(
        STOP_TIMES_PATH,
        usecols=["trip_id", "stop_id", "stop_sequence"],
        dtype={"trip_id": str, "stop_id": str},
    )
    st_df["stop_sequence"] = pd.to_numeric(st_df["stop_sequence"], errors="coerce")
    st_df["route_id"] = st_df["trip_id"].map(extract_route)
    st_df = st_df.dropna(subset=["route_id"])
    st_df["stop_name"] = st_df["stop_id"].map(stop_name_map)
    st_df = st_df.dropna(subset=["stop_name"])

    # Group rows by (route, trip), each group is one train journey
    # Sort stops by stop_sequence to get them in travel order
    # Deduplicate - many trips on the same route share the same stop sequence
    print("Building sequences...")
    lookup: dict[str, set] = {}
    for (route, trip), grp in st_df.groupby(["route_id", "trip_id"]):
        seq = tuple(grp.sort_values("stop_sequence")["stop_name"].tolist())
        lookup.setdefault(route, set()).add(seq)

    # Serialise to JSON
    output = {route: [list(seq) for seq in seqs] for route, seqs in sorted(lookup.items())}

    print(f"Writing {OUTPUT_PATH}...")
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f)

    total_seqs = sum(len(v) for v in output.values())
    print(f"Done. {len(output)} routes, {total_seqs} unique sequences.")


if __name__ == "__main__":
    main()
