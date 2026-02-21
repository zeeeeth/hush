"""
Deduplicate StopCoords
Creates a CSV with one coordinate per stop name (deduped).
"""
import pandas as pd

coords = pd.read_csv("../../data/processed/StopCoords.csv")
# Deduplicate by name, keeping the first occurrence, avoid N/S duplicates
deduped = coords.drop_duplicates(subset=["name"])
deduped.to_csv("../../data/processed/DedupedStopCoords.csv", index=False)
print(f"Wrote {len(deduped)} deduped stop coordinates to DedupedStopCoords.csv")
