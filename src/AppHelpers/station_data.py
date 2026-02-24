import streamlit as st
import pandas as pd

# Load station coordinates
# For looking up coordinates by station ID, for routing & graph operations
@st.cache_data
def load_station_coordinates():
    try:
        df = pd.read_csv("data/processed/StopCoords.csv")
        return {row['stop_id']: {'lat': row['lat'], 'lng': row['lng'], 'name': row['name']} for _, row in df.iterrows()}
    except FileNotFoundError:
        return {}

# Load stop to coordinates mapping
# For looking up coordinates by station name. For searching and displaying information.
@st.cache_data
def load_DedupedStopCoords():
    try:
        df = pd.read_csv("data/processed/DedupedStopCoords.csv")
        return {row['name']: {'lat': row['lat'], 'lng': row['lng']} for _, row in df.iterrows()}
    except FileNotFoundError:
        return {}

# Sorted list of unique station names with IDs
def get_station_list():
    coords = load_station_coordinates()
    
    stations = {}
    for station_id, data in coords.items():
        name = data.get("name", "")
        # Avoid N and S variants
        if station_id.endswith("N") or station_id.endswith("S"):
            continue
        if name and name not in stations:
            stations[name] = {
                "id": station_id,
                "lat": data.get("lat"),
                "lng": data.get("lng")
            }
    
    return dict(sorted(stations.items()))

# Find station coordinates by name using DedupedStopCoords.csv
def find_station_coords_by_name(name: str) -> dict:
    DedupedStopCoords = load_DedupedStopCoords()
    name_stripped = name.strip()
    
    # Attempt 1: Exact match
    if name_stripped in DedupedStopCoords:
        data = DedupedStopCoords[name_stripped]
        return {"lat": data["lat"], "lng": data["lng"], "name": name_stripped}
    
    # Attempt 2: Case-insensitive exact match
    name_lower = name_stripped.lower()
    for station_name, data in DedupedStopCoords.items():
        if station_name.lower() == name_lower:
            return {"lat": data["lat"], "lng": data["lng"], "name": station_name}
    
    # Attempt 3: Partial match
    for station_name, data in DedupedStopCoords.items():
        station_lower = station_name.lower()
        if name_lower in station_lower or station_lower in name_lower:
            return {"lat": data["lat"], "lng": data["lng"], "name": station_name}
    
    # Attempt 4: Matching without suffixes like "St" and "Ave"
    name_clean = name_lower.replace(" st", "").replace(" ave", "").replace(" sq", "")
    for station_name, data in DedupedStopCoords.items():
        station_clean = station_name.lower().replace(" st", "").replace(" ave", "").replace(" sq", "")
        if name_clean in station_clean or station_clean in name_clean:
            return {"lat": data["lat"], "lng": data["lng"], "name": station_name}
    
    return None

# Get lat/lng coordinates for a station ID
def get_station_coords(station_id: str, coords: dict) -> dict:
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