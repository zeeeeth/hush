# ============================================================================
# GNN PREDICTION & CONGESTION SCORING
# ============================================================================
import streamlit as st
import pandas as pd
from datetime import datetime
from gnn_inference import get_predictor
from congestion_scorer import CongestionScorer

# Default score for routes with no prediction available
DEFAULT_QUIET_SCORE = 5

# Load GNN predictor, cache it
@st.cache_resource
def load_gnn_predictor():
    return get_predictor()

# Get current tap-in predictions from GNN
# Randomly sample one entry per station from 2024.csv matching the current DOW and hour.
# Cache for 5 min
@st.cache_data(ttl=300, show_spinner=False)
def get_tap_in_predictions():
    try:
        # Load 2024 ridership data only
        ridership_df = pd.read_csv("data/raw/2024.csv",
                                   parse_dates=["transit_timestamp"],
                                   date_format="%m/%d/%Y %I:%M:%S %p",
                                   low_memory=False)
        # Get current hour and DOW
        current_time = datetime.now()
        current_hour = current_time.hour
        current_dow = current_time.weekday()

        # Extract hour and DOW from timestamps
        ridership_df['hour'] = ridership_df['transit_timestamp'].dt.hour
        ridership_df["dow"] = ridership_df["transit_timestamp"].dt.dayofweek

        # Filter to matching hour and day of week
        matching_hour = ridership_df[(ridership_df["hour"] == current_hour) & (ridership_df["dow"] == current_dow)]

        # Fallback 1: Same weekday, any hour
        if len(matching_hour) == 0:
            matching_hour = ridership_df[ridership_df["dow"] == current_dow]
        # Fallback 2: Any day, any hour
        if len(matching_hour) == 0:
            matching_hour = ridership_df

        # Clean ridership data - convert to int, set stations with no entry to 0
        matching_hour = matching_hour.copy()
        matching_hour['ridership'] = pd.to_numeric(
            matching_hour['ridership'].astype(str).str.replace(',', ''),
            errors='coerce'
        ).fillna(0)

        # Randomly sample one entry per station_complex_id
        current_ridership = (
            matching_hour
            .groupby('station_complex_id')
            .sample(n=1, random_state=None)  # random_state=None for true randomness
            [['station_complex_id', 'ridership']]
            .reset_index(drop=True)
        )

        # Run GNN inference
        predictor = load_gnn_predictor()
        predictions = predictor.predict(current_ridership, current_time)
        return predictions
    except Exception as e:
        st.warning(f"Could not load GNN predictions: {e}")
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
            route['quiet_score'] = DEFAULT_QUIET_SCORE
        return routes
    
    scorer = CongestionScorer(predictions)
    
    for route in routes:
        quiet_score = scorer.calculate_route_quiet_score(route)
        route['quiet_score'] = quiet_score
    
    return routes