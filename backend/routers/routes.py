from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from services.station_data import load_station_coordinates, get_station_list, find_station_coords_by_name
from services.routing import get_routes

routes_bp = Blueprint("routes", __name__)


@routes_bp.get("/stations")
def list_stations():
    """Return sorted list of all stations with id, name, lat, lng."""
    return jsonify(get_station_list())


@routes_bp.get("/routes")
def find_routes():
    """
    Find transit routes between two stations.
    Returns scored routes with quiet scores.
    """
    origin_id = request.args.get("origin_id")
    destination_id = request.args.get("destination_id")

    if not origin_id or not destination_id:
        return jsonify({"error": "origin_id and destination_id are required"}), 400

    coords = load_station_coordinates()
    routes, error = get_routes(origin_id, destination_id, coords)

    if error:
        return jsonify({"error": error}), 404

    # Mark recommended route
    if routes:
        best_idx = max(range(len(routes)), key=lambda i: routes[i].get("quiet_score", 0) or 0)
        for i, route in enumerate(routes):
            route["is_recommended"] = i == best_idx

    now = datetime.now()
    return jsonify({
        "routes": routes,
        "prediction_window": {
            "from": now.isoformat(),
            "to": (now + timedelta(hours=1)).isoformat(),
        },
    })


@routes_bp.get("/station-coords")
def station_coords_by_name():
    """Find station coordinates by name. For displaying markers on the map."""
    name = request.args.get("name", "")
    result = find_station_coords_by_name(name)
    if not result:
        return jsonify({"error": f"Station '{name}' not found"}), 404
    return jsonify(result)


@routes_bp.get("/health")
def health():
    return jsonify({"status": "ok"})
