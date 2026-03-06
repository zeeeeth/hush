"""
Loads pre-built stop sequences from data/processed/StopSequences.json to resolve
intermediate stops between a departure and arrival on a given subway line.
Run training/preprocessing/build_gtfs_sequences.py once to generate the JSON.
"""

import re
import json
from functools import lru_cache


def _normalize(name: str) -> str:
    """Lowercase, strip, collapse whitespace, remove hyphens."""
    return re.sub(r"[\s\-]+", " ", name.lower().strip())


@lru_cache(maxsize=1)
def load_gtfs_lookup() -> dict[str, list[list[str]]]:
    """
    Load and return the pre-built GTFS sequences lookup: { route_id: [ [stop_name, stop_name, ...], ... ] }
    Cached for the lifetime of the app process.
    """
    with open("data/processed/StopSequences.json") as f:
        return json.load(f)


def get_intermediate_stops(
    lookup: dict[str, list[list[str]]],
    route_id: str,
    departure_name: str,
    arrival_name: str,
) -> list[str]:
    """
    Return intermediate stop names between departure and arrival on a given route.
    Returns [] if not found.

    Args:
        lookup: result of load_gtfs_lookup()
        route_id: subway line short name, e.g. "A", "1"
        departure_name: departure stop name from Google Routes API
        arrival_name: arrival stop name from Google Routes API
    """
    # Lookup all known stop sequences for this route_id
    sequences = lookup.get(route_id.upper(), [])
    if not sequences:
        return []

    dep_norm = _normalize(departure_name)
    arr_norm = _normalize(arrival_name)

    best: list[str] = []

    # For each sequence, match departure and arrival names, slice sequence between them
    for seq in sequences:
        norm_seq = [_normalize(s) for s in seq]

        # Find best match indices for departure and arrival
        dep_idx = _fuzzy_index(dep_norm, norm_seq)
        arr_idx = _fuzzy_index(arr_norm, norm_seq)

        if dep_idx is None or arr_idx is None:
            continue

        # Ensure correct direction
        if dep_idx >= arr_idx:
            continue

        intermediates = seq[dep_idx + 1 : arr_idx]

        # Prefer longer intermediate list (more specific match)
        if len(intermediates) > len(best):
            best = intermediates

    return best


def _fuzzy_index(query: str, norm_seq: list[str]) -> int | None:
    """
    Find the index in norm_seq that best matches query.
    Priority: exact -> substring -> first-word.
    """
    # 1. Exact match
    for i, name in enumerate(norm_seq):
        if query == name:
            return i

    # 2. Substring match (either direction)
    for i, name in enumerate(norm_seq):
        if query in name or name in query:
            return i

    # 3. First-word match
    query_word = query.split()[0] if query.split() else ""
    for i, name in enumerate(norm_seq):
        name_word = name.split()[0] if name.split() else ""
        if query_word and query_word == name_word:
            return i

    return None
