"""
Assign ComplexNodes during training
Creates a mapping from complex IDs to node indices for GNN input.
"""
import pandas as pd

stop_complex = pd.read_csv("../../data/processed/StopComplex.csv")
complex_ids = sorted(stop_complex["station_complex_id"].unique())
complex_to_node = {cid: idx for idx, cid in enumerate(complex_ids)}

mapping_df = pd.DataFrame([{"complex_id": cid, "node_id": node_id} for cid, node_id in complex_to_node.items()])
mapping_df.to_csv("../../data/processed/ComplexNodes.csv", index=False)
print(f"Wrote {len(mapping_df)} complex-node mappings to ComplexNodes.csv")
