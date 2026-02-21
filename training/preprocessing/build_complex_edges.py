"""
Build ComplexEdges from stop_times.csv
Creates a CSV of edges between station complexes based on stop sequence.
"""
import pandas as pd

stop_times = pd.read_csv("../../data/raw/stop_times.csv")
stops = stop_times.sort_values(["trip_id", "stop_sequence"])

# Build edges between consecutive stops in the same trip
edges = set()
for trip_id, group in stops.groupby("trip_id"):
    stop_seq = group["stop_id"].tolist()
    for i in range(len(stop_seq) - 1):
        edges.add((stop_seq[i], stop_seq[i+1]))

edges_df = pd.DataFrame(list(edges), columns=["from_stop_id", "to_stop_id"])
edges_df.to_csv("../../data/processed/ComplexEdges.csv", index=False)
print(f"Wrote {len(edges_df)} edges to ComplexEdges.csv")
