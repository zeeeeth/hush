from .config import WEIGHTS, DELAY_PENALTY
from .tfl_api import get_crowding_for_time
from .models import Route


def calculate_sensory_score(route: Route, line_status: dict[str, dict]) -> Route:
    """
    Calculate the sensory/stress score for a route.
    Lower score = better for sensory-sensitive travelers.
    """
    total_score = 0.0
    has_delays = False
    delay_reasons = []

    for leg in route.legs:
        # Determine weight based on travel mode
        if leg.mode.lower() == "walking":
            weight = WEIGHTS["walking"]
        elif leg.mode.lower() in ["tube", "dlr", "overground", "elizabeth-line"]:
            weight = WEIGHTS["train_travel"]
        else:
            weight = WEIGHTS["train_travel"]

        # Score each stop on this leg
        for stop in leg.stops:
            crowding = get_crowding_for_time(stop.naptan_id, stop.arrival_time)
            stop.crowding_score = crowding
            total_score += crowding * weight * 10  # Scale up for readability

        # Add interchange penalty (changing lines is stressful)
        if len(route.legs) > 1:
            total_score += WEIGHTS["interchange"] * 5

        # Check for delays on this line
        if leg.line_id and leg.line_id in line_status:
            status = line_status[leg.line_id]
            if status["has_severe_delays"]:
                has_delays = True
                total_score += DELAY_PENALTY
                delay_reasons.append(f"{leg.line_name}: {status['status']}")

    route.sensory_score = round(total_score, 1)
    route.has_delays = has_delays
    route.delay_info = "; ".join(delay_reasons)

    return route


def rank_routes(routes: list[Route]) -> list[Route]:
    """Rank routes by sensory score (lowest = best)."""
    return sorted(routes, key=lambda r: r.sensory_score)


def get_stress_level_emoji(score: float) -> str:
    """Return an emoji and label based on stress score."""
    if score < 30:
        return "🟢 Low Stress"
    elif score < 60:
        return "🟡 Moderate"
    elif score < 80:
        return "🟠 High Stress"
    else:
        return "🔴 Very High Stress"


def get_recommendation(routes: list[Route]) -> str:
    """Generate a recommendation message comparing routes."""
    if len(routes) < 2:
        return ""

    fastest = min(routes, key=lambda r: r.total_duration)
    calmest = min(routes, key=lambda r: r.sensory_score)

    if fastest == calmest:
        return "✅ **Great news!** The fastest route is also the calmest option."

    time_diff = calmest.total_duration - fastest.total_duration
    stress_diff = fastest.sensory_score - calmest.sensory_score
    stress_reduction = (stress_diff / fastest.sensory_score * 100) if fastest.sensory_score > 0 else 0

    return f"""
    💡 **Recommendation:** Take the calmer route!  
    It costs **{time_diff} extra minutes** but reduces sensory load by **{stress_reduction:.0f}%**.
    """
