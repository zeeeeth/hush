from datetime import timedelta, datetime
from .models import StopPoint, RouteLeg, Route


def parse_journey(journey_data: dict, start_time: datetime) -> Route:
    """Parse TfL journey JSON into our Route data structure."""
    legs = []
    current_time = start_time

    for leg_data in journey_data.get("legs", []):
        mode = leg_data.get("mode", {}).get("name", "unknown")
        duration = leg_data.get("duration", 0)

        # Get line info
        route_options = leg_data.get("routeOptions", [{}])
        line_name = route_options[0].get("name", "Walking") if route_options else "Walking"
        line_id = route_options[0].get("lineIdentifier", {}).get("id", "") if route_options else ""

        # Parse stops
        stops = []
        path = leg_data.get("path", {}).get("stopPoints", [])
        for i, stop_data in enumerate(path):
            # Estimate arrival time at each stop
            stop_time = current_time + timedelta(minutes=i * (duration / max(len(path), 1)))

            stop = StopPoint(
                naptan_id=stop_data.get("id", ""),
                name=stop_data.get("name", "Unknown"),
                arrival_time=stop_time,
                line_id=line_id
            )
            stops.append(stop)

        instruction = leg_data.get("instruction", {}).get("summary", "")
        departure = leg_data.get("departurePoint", {}).get("commonName", "")
        arrival = leg_data.get("arrivalPoint", {}).get("commonName", "")

        leg = RouteLeg(
            mode=mode,
            line_name=line_name,
            line_id=line_id,
            duration_minutes=duration,
            stops=stops,
            instruction=instruction,
            departure_point=departure,
            arrival_point=arrival
        )
        legs.append(leg)
        current_time += timedelta(minutes=duration)

    total_duration = journey_data.get("duration", 0)

    return Route(
        legs=legs,
        total_duration=total_duration,
        departure_time=start_time,
        arrival_time=start_time + timedelta(minutes=total_duration)
    )
