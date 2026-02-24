import requests
import os
from dotenv import load_dotenv
from .gnn_loader import calculate_route_quiet_scores
from .station_data import get_station_coords

load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv("ROUTES_API_KEY")

"""
Get transit routes between two stations using Google Routes API.
Returns top 3 fastest routes with subway/rail only.
"""
def get_routes(origin_id: str, destination_id: str, coords: dict):
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
                    
                    # Subway
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
            
            # Merge consecutive walks and filter out 0-minute walks
            steps = []
            for step in raw_steps:
                if step["type"] == "walk":
                    if step["duration_min"] < 1:
                        continue
                    # Most recently added step is a walk, merge
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
        # Create a unique signature based on the lines and stops used
        def get_route_signature(route):
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