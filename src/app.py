"""
MTA Sensory-Safe Router
A smart routing app for NYC subway with quiet score ratings.
Glassmorphism design with map overlay.
"""

import streamlit as st
import requests
import json
import os
import sys
import pydeck as pdk
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from linear_css import inject_custom_css
from components.MapComponent import MapComponent
from components.Header import Header
from components.SearchInputs import SearchInputs
from components.SearchResults import SearchResults
from components.RouteCard import render_route_card

# Add src directory to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Import GNN modules
from gnn_inference import get_predictor
from congestion_scorer import CongestionScorer

# ============================================================================
# CONFIGURATION
# ============================================================================

load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv("ROUTES_API_KEY")

# NYC center coordinates
NYC_CENTER = [40.7580, -73.9855]  # Midtown Manhattan

# ============================================================================
# GNN PREDICTION & CONGESTION SCORING
# ============================================================================

@st.cache_resource
def load_gnn_predictor():
    """Load GNN predictor (cached)."""
    return get_predictor()


@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
def get_tap_in_predictions():
    """
    Get current tap-in predictions from GNN.
    Randomly samples one entry per station from 2024.csv matching the current hour.
    """
    try:
        # Load 2024 ridership data only
        ridership_df = pd.read_csv("data/raw/2024.csv",
                                   parse_dates=["transit_timestamp"],
                                   date_format="%m/%d/%Y %I:%M:%S %p",
                                   low_memory=False)
        # Get current time
        current_time = datetime.now()
        current_hour = current_time.hour

        # Extract hour from timestamps
        ridership_df['hour'] = ridership_df['transit_timestamp'].dt.hour

        # Filter to matching hour
        matching_hour = ridership_df[ridership_df['hour'] == current_hour]

        if len(matching_hour) == 0:
            # Fallback if no data for current hour
            matching_hour = ridership_df

        # Clean ridership data
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
    
    Args:
        routes: List of route dicts
    
    Returns:
        Routes with 'quiet_score' field populated
    """
    predictions = get_tap_in_predictions()
    
    if not predictions:
        # If no predictions, return routes with default scores
        for route in routes:
            route['quiet_score'] = 5
        return routes
    
    scorer = CongestionScorer(predictions)
    
    for route in routes:
        quiet_score = scorer.calculate_route_quiet_score(route)
        route['quiet_score'] = quiet_score
    
    return routes

# ============================================================================
# STATION DATA
# ============================================================================

@st.cache_data
def load_station_coordinates():
    """Load station coordinates. For looking up coordinates by station ID, for routing, graph operations."""
    try:
        df = pd.read_csv("data/processed/StopCoords.csv")
        return {row['stop_id']: {'lat': row['lat'], 'lng': row['lng'], 'name': row['name']} for _, row in df.iterrows()}
    except FileNotFoundError:
        return {}


@st.cache_data
def load_DedupedStopCoords():
    """Load stop to coordinates mapping. For looking up coordinates by station name, for searching and displaying."""
    try:
        df = pd.read_csv("data/processed/DedupedStopCoords.csv")
        return {row['name']: {'lat': row['lat'], 'lng': row['lng']} for _, row in df.iterrows()}
    except FileNotFoundError:
        return {}


def get_station_list():
    """Get a sorted list of unique station names with their IDs."""
    coords = load_station_coordinates()
    
    stations = {}
    for station_id, data in coords.items():
        name = data.get("name", "")
        if station_id.endswith("N") or station_id.endswith("S"):
            continue
        if name and name not in stations:
            stations[name] = {
                "id": station_id,
                "lat": data.get("lat"),
                "lng": data.get("lng")
            }
    
    return dict(sorted(stations.items()))


def find_station_coords_by_name(name: str) -> dict:
    """Find station coordinates by name using DedupedStopCoords.csv."""
    DedupedStopCoords = load_DedupedStopCoords()
    name_stripped = name.strip()
    
    # First try exact match
    if name_stripped in DedupedStopCoords:
        data = DedupedStopCoords[name_stripped]
        return {"lat": data["lat"], "lng": data["lng"], "name": name_stripped}
    
    # Try case-insensitive exact match
    name_lower = name_stripped.lower()
    for station_name, data in DedupedStopCoords.items():
        if station_name.lower() == name_lower:
            return {"lat": data["lat"], "lng": data["lng"], "name": station_name}
    
    # Try partial match
    for station_name, data in DedupedStopCoords.items():
        station_lower = station_name.lower()
        if name_lower in station_lower or station_lower in name_lower:
            return {"lat": data["lat"], "lng": data["lng"], "name": station_name}
    
    # Try matching without suffixes like "St", "Ave", etc.
    name_clean = name_lower.replace(" st", "").replace(" ave", "").replace(" sq", "")
    for station_name, data in DedupedStopCoords.items():
        station_clean = station_name.lower().replace(" st", "").replace(" ave", "").replace(" sq", "")
        if name_clean in station_clean or station_clean in name_clean:
            return {"lat": data["lat"], "lng": data["lng"], "name": station_name}
    
    return None


def get_station_coords(station_id: str, coords: dict) -> dict:
    """Get lat/lng coordinates for a GTFS station ID."""
    if station_id in coords:
        return {
            "latitude": coords[station_id]["lat"],
            "longitude": coords[station_id]["lng"]
        }
    
    # Try without N/S suffix
    base_id = station_id.rstrip("NS")
    if base_id in coords:
        return {
            "latitude": coords[base_id]["lat"],
            "longitude": coords[base_id]["lng"]
        }
    
    # Try with N suffix
    if f"{base_id}N" in coords:
        return {
            "latitude": coords[f"{base_id}N"]["lat"],
            "longitude": coords[f"{base_id}N"]["lng"]
        }
    
    return None


# ============================================================================
# ROUTING
# ============================================================================

def get_routes(origin_id: str, destination_id: str, coords: dict):
    """
    Get transit routes between two MTA stations using Google Routes API.
    Returns top 3 fastest routes with subway/rail only.
    """
    origin_coords = get_station_coords(origin_id, coords)
    dest_coords = get_station_coords(destination_id, coords)
    
    if not origin_coords or not dest_coords:
        return None, "Could not find coordinates for stations"
    
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": ",".join([
            "routes.duration",
            "routes.distanceMeters",
            "routes.legs.steps.transitDetails",
            "routes.legs.steps.travelMode",
            "routes.legs.steps.staticDuration",
            "routes.legs.steps.distanceMeters"
        ])
    }
    
    body = {
        "origin": {"location": {"latLng": origin_coords}},
        "destination": {"location": {"latLng": dest_coords}},
        "travelMode": "TRANSIT",
        "computeAlternativeRoutes": True,
        "transitPreferences": {
            "allowedTravelModes": ["SUBWAY", "RAIL"]
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=body, timeout=15)
        data = response.json()
        
        if "error" in data:
            return None, data["error"].get("message", "API Error")
        
        routes = data.get("routes", [])
        if not routes:
            return None, "No subway routes found"
        
        # Process routes
        processed_routes = []
        
        for route in routes:
            duration_str = route.get("duration", "0s")
            duration_sec = int(duration_str.rstrip("s"))
            duration_min = duration_sec // 60
            distance = route.get("distanceMeters", 0)
            
            # Extract steps
            raw_steps = []
            for leg in route.get("legs", []):
                for step in leg.get("steps", []):
                    mode = step.get("travelMode", "?")
                    duration = step.get("staticDuration", "?")
                    dur_sec = int(duration.rstrip("s")) if duration != "?" else 0
                    
                    if mode == "TRANSIT":
                        transit = step.get("transitDetails", {})
                        stopDetails = transit.get("stopDetails", {})
                        departure = stopDetails.get("departureStop", {}).get("name", "?")
                        arrival = stopDetails.get("arrivalStop", {}).get("name", "?")
                        line = transit.get("transitLine", {})
                        line_name = line.get("nameShort") or line.get("name", "?")
                        line_color = line.get("color", "#888888")
                        num_stops = transit.get("stopCount", "?")
                        
                        raw_steps.append({
                            "type": "transit",
                            "line": line_name,
                            "color": line_color,
                            "departure": departure,
                            "arrival": arrival,
                            "num_stops": num_stops,
                            "duration_min": dur_sec // 60
                        })
                    
                    elif mode == "WALK":
                        step_dist = step.get("distanceMeters", 0)
                        raw_steps.append({
                            "type": "walk",
                            "distance_m": step_dist,
                            "duration_min": dur_sec // 60
                        })
            
            # Merge consecutive walks and filter 0-minute walks
            steps = []
            for step in raw_steps:
                if step["type"] == "walk":
                    if step["duration_min"] < 1:
                        continue
                    if steps and steps[-1]["type"] == "walk":
                        steps[-1]["distance_m"] += step["distance_m"]
                        steps[-1]["duration_min"] += step["duration_min"]
                    else:
                        steps.append(step)
                else:
                    steps.append(step)
            
            processed_routes.append({
                "duration_min": duration_min,
                "distance_km": distance / 1000,
                "steps": steps,
                "quiet_score": None  # Placeholder for later
            })
        
        # Deduplicate routes based on the sequence of transit lines used
        def get_route_signature(route):
            """Create a unique signature based on the lines used."""
            transit_steps = [s for s in route["steps"] if s["type"] == "transit"]
            return tuple((s["line"], s["departure"], s["arrival"]) for s in transit_steps)
        
        seen_signatures = set()
        unique_routes = []
        for route in processed_routes:
            sig = get_route_signature(route)
            if sig not in seen_signatures:
                seen_signatures.add(sig)
                unique_routes.append(route)
        
        # Sort by duration and return top 3
        unique_routes.sort(key=lambda r: r["duration_min"])
        top_routes = unique_routes[:3]
        
        # Calculate quiet scores
        top_routes = calculate_route_quiet_scores(top_routes)
        
        return top_routes, None
        
    except requests.RequestException as e:
        return None, f"Network error: {e}"

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    st.set_page_config(
        page_title="Hush",
        page_icon="🚇",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    inject_custom_css()
    
    # Load data
    coords = load_station_coordinates()
    stations = get_station_list()
    
    if not stations:
        st.markdown("""
        <div class="error-card">Failed to load station data.</div>
        """, unsafe_allow_html=True)
        return
    
    station_names = list(stations.keys())
    
    # Two-column layout
    left_col, right_col = st.columns([1, 2])
    
    with left_col:
        # Header
        Header()
        
        origin_name, destination_name, search_clicked = SearchInputs(station_names)
        SearchResults(
            search_clicked=search_clicked,
            origin_name=origin_name,
            destination_name=destination_name,
            stations=stations,
            coords=coords,
            get_routes=get_routes
        )
    
    with right_col:
        MapComponent(
            origin_name=origin_name,
            destination_name=destination_name,
            stations=stations,
            find_station_coords_by_name=find_station_coords_by_name
        )


if __name__ == "__main__":
    main()
