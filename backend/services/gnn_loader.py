"""
GNN Prediction & Congestion Scoring
Replaces Streamlit caching with TTL-based caching.
"""

# ============================================================================
# GNN PREDICTION & CONGESTION SCORING
# ============================================================================

import logging
import time
import pandas as pd
from datetime import datetime
from .gnn_inference import get_predictor
from .congestion_scorer import CongestionScorer

logger = logging.getLogger(__name__)

# Default score for routes with no prediction available
DEFAULT_QUIET_SCORE = 5

# TTL cache state
_predictions_cache = None
_predictions_cache_time = 0
_PREDICTIONS_TTL = 300  # 5 minutes


def get_tap_in_predictions() -> dict:
    """
    Get current tap-in predictions from GNN, cached for 5 minutes.
    Reads from the pre-aggregated ridership_by_hour.csv instead of raw 2024.csv.
    """
    global _predictions_cache, _predictions_cache_time

    now = time.time()
    if _predictions_cache is not None and (now - _predictions_cache_time) < _PREDICTIONS_TTL:
        return _predictions_cache

    try:
        ridership_df = pd.read_csv("data/processed/ridership_by_hour.csv")

        current_time = datetime.now()
        current_hour = current_time.hour
        current_dow = current_time.weekday()

        # Filter to matching hour and day of week
        matching = ridership_df[
            (ridership_df["hour"] == current_hour) & (ridership_df["dow"] == current_dow)
        ]

        # Fallback 1: same DOW, any hour
        if len(matching) == 0:
            matching = ridership_df[ridership_df["dow"] == current_dow]
        # Fallback 2: any row
        if len(matching) == 0:
            matching = ridership_df

        current_ridership = (
            matching[["station_complex_id", "mean_ridership"]]
            .rename(columns={"mean_ridership": "ridership"})
            .reset_index(drop=True)
        )

        # Run GNN inference
        predictor = get_predictor()
        predictions = predictor.predict(current_ridership, current_time)

        _predictions_cache = predictions
        _predictions_cache_time = now

        return predictions
    except Exception as e:
        logger.warning(f"Could not load GNN predictions: {e}")
        return {}


def calculate_route_quiet_scores(routes: list) -> list:
    """
    Add quiet scores to routes based on GNN predictions.
    List of route dicts -> routes with 'quiet_score' field
    """
    predictions = get_tap_in_predictions()

    # No predictions, return default score
    if not predictions:
        for route in routes:
            route["quiet_score"] = DEFAULT_QUIET_SCORE
        return routes

    scorer = CongestionScorer(predictions)

    for route in routes:
        quiet_score = scorer.calculate_route_quiet_score(route)
        route["quiet_score"] = quiet_score

    return routes
