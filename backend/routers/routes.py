from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
from services.station_data import load_station_coordinates, get_station_list, find_station_coords_by_name
from services.routing import get_routes

router = APIRouter()


@router.get("/stations")
def list_stations():
    """Return sorted list of all stations with id, name, lat, lng."""
    return get_station_list()


@router.get("/routes")
def find_routes(origin_id: str = Query(...), destination_id: str = Query(...)):
    """
    Find transit routes between two stations.
    Returns scored routes with quiet scores.
    """
    coords = load_station_coordinates()
    routes, error = get_routes(origin_id, destination_id, coords)

    if error:
        raise HTTPException(status_code=404, detail=error)

    # Mark recommended route
    if routes:
        best_idx = max(range(len(routes)), key=lambda i: routes[i].get("quiet_score", 0) or 0)
        for i, route in enumerate(routes):
            route["is_recommended"] = i == best_idx

    now = datetime.now()
    return {
        "routes": routes,
        "prediction_window": {
            "from": now.isoformat(),
            "to": (now + timedelta(hours=1)).isoformat(),
        },
    }


@router.get("/station-coords")
def station_coords_by_name(name: str = Query(...)):
    """Find station coordinates by name (fuzzy match)."""
    result = find_station_coords_by_name(name)
    if not result:
        raise HTTPException(status_code=404, detail=f"Station '{name}' not found")
    return result


@router.get("/health")
def health():
    return {"status": "ok"}
