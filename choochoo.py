"""
🚇 Sensory-Safe Router - TfL Accessibility App
A smart routing system that prioritizes mental wellbeing over speed.
Built for neurodiverse Londoners who need quieter, calmer journeys.
"""

import streamlit as st
import requests
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# ============================================================================
# CONFIGURATION
# ============================================================================

TFL_API_BASE = "https://api.tfl.gov.uk"
# Add your TfL API key here (get one from https://api-portal.tfl.gov.uk)
TFL_APP_KEY = "ac9b195ad9ed475289a2c67aac5a50e2"  # Optional but recommended for higher rate limits

# Sensory weighting factors
WEIGHTS = {
    "platform_wait": 1.0,    # Waiting on platform = highest stress
    "train_travel": 0.6,     # Inside train = medium stress
    "walking": 0.3,          # Walking in tunnels = lower stress
    "interchange": 0.8,      # Changing lines = high stress (crowds, navigation)
}

DELAY_PENALTY = 50  # Additional points for severe delays


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class StopPoint:
    """Represents a station/stop on the journey."""
    naptan_id: str
    name: str
    arrival_time: datetime
    crowding_score: float = 0.0  # 0.0 to 1.0
    line_id: Optional[str] = None


@dataclass
class RouteLeg:
    """A single leg of a journey (e.g., one tube line segment)."""
    mode: str
    line_name: str
    line_id: str
    duration_minutes: int
    stops: list[StopPoint]
    instruction: str
    departure_point: str
    arrival_point: str


@dataclass
class Route:
    """A complete journey from origin to destination."""
    legs: list[RouteLeg]
    total_duration: int
    departure_time: datetime
    arrival_time: datetime
    sensory_score: float = 0.0
    has_delays: bool = False
    delay_info: str = ""


# ============================================================================
# TFL API FUNCTIONS
# ============================================================================

def get_api_params() -> dict:
    """Get API parameters including key if available."""
    if TFL_APP_KEY:
        return {"app_key": TFL_APP_KEY}
    return {}


def search_station(query: str) -> list[dict]:
    """Search for stations matching a query string using StopPoint Search."""
    url = f"{TFL_API_BASE}/StopPoint/Search/{query}"
    params = get_api_params()
    params.update({
        "modes": "tube,dlr,overground,elizabeth-line,national-rail,bus",
        "maxResults": 10,
        "faresOnly": "false"
    })
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Format results for our UI
        results = []
        for match in data.get("matches", []):
            results.append({
                "id": match.get("icsId") or match.get("id", ""),
                "name": match.get("name", ""),
                "zone": match.get("zone", "")
            })
        return results
    except requests.RequestException as e:
        st.error(f"Error searching stations: {e}")
        return []


def get_journey_options(from_station: str, to_station: str, time: datetime = None) -> list[dict]:
    """
    Fetch journey options from TfL Journey Planner API.
    Returns top route options between two points.
    Uses station names directly which works more reliably.
    """
    # URL encode the station names
    from urllib.parse import quote
    from_encoded = quote(from_station, safe='')
    to_encoded = quote(to_station, safe='')
    
    url = f"{TFL_API_BASE}/Journey/JourneyResults/{from_encoded}/to/{to_encoded}"
    params = get_api_params()
    params.update({
        "mode": "tube,dlr,overground,elizabeth-line,bus,national-rail",
        "journeyPreference": "LeastTime",
        "alternativeCycle": "false",
        "alternativeWalking": "false"
    })
    
    if time:
        params["time"] = time.strftime("%H%M")
        params["date"] = time.strftime("%Y%m%d")
        params["timeIs"] = "Departing"
    
    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        
        # Check if TfL returns disambiguation options
        if "toLocationDisambiguation" in data or "fromLocationDisambiguation" in data:
            # TfL couldn't resolve the location uniquely
            # Try to use the first disambiguation option
            to_options = data.get("toLocationDisambiguation", {}).get("disambiguationOptions", [])
            from_options = data.get("fromLocationDisambiguation", {}).get("disambiguationOptions", [])
            
            # Get the first valid option for each
            new_from = from_station
            new_to = to_station
            
            if from_options and len(from_options) > 0:
                place = from_options[0].get("place", {})
                new_from = place.get("icsCode") or place.get("commonName") or from_station
            
            if to_options and len(to_options) > 0:
                place = to_options[0].get("place", {})
                new_to = place.get("icsCode") or place.get("commonName") or to_station
            
            # Retry with resolved names
            if new_from != from_station or new_to != to_station:
                from_encoded = quote(str(new_from), safe='')
                to_encoded = quote(str(new_to), safe='')
                url = f"{TFL_API_BASE}/Journey/JourneyResults/{from_encoded}/to/{to_encoded}"
                response = requests.get(url, params=params, timeout=15)
                data = response.json()
        
        response.raise_for_status()
        return data.get("journeys", [])[:5]  # Top 5 routes
    except requests.RequestException as e:
        st.error(f"Error fetching journeys: {e}")
        return []


def get_crowding_data(naptan_id: str) -> dict:
    """
    Get crowding/capacity data for a station.
    Returns hourly crowding percentages.
    """
    url = f"{TFL_API_BASE}/crowding/{naptan_id}"
    params = get_api_params()
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 404:
            # Station doesn't have crowding data
            return {"percentageOfBaseline": 0.5}  # Default to 50%
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return {"percentageOfBaseline": 0.5}  # Default fallback


def get_line_status() -> dict[str, dict]:
    """
    Get current status for all tube/rail lines.
    Returns a dict of line_id -> status info.
    """
    url = f"{TFL_API_BASE}/Line/Mode/tube,dlr,overground,elizabeth-line/Status"
    params = get_api_params()
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        status_map = {}
        for line in data:
            line_id = line.get("id", "")
            statuses = line.get("lineStatuses", [])
            
            # Check for disruptions
            has_severe = any(
                s.get("statusSeverity", 10) <= 5 
                for s in statuses
            )
            
            status_desc = statuses[0].get("statusSeverityDescription", "Unknown") if statuses else "Unknown"
            reason = statuses[0].get("reason", "") if statuses else ""
            
            status_map[line_id] = {
                "has_severe_delays": has_severe,
                "status": status_desc,
                "reason": reason
            }
        
        return status_map
    except requests.RequestException as e:
        st.warning(f"Could not fetch line status: {e}")
        return {}


def get_crowding_for_time(naptan_id: str, arrival_time: datetime) -> float:
    """
    Get the crowding level for a specific station at a specific time.
    Returns a value between 0.0 (empty) and 1.0 (packed).
    """
    crowding_data = get_crowding_data(naptan_id)
    
    # Try to get time-specific data
    if "timeBands" in crowding_data:
        hour = arrival_time.hour
        for band in crowding_data.get("timeBands", []):
            if band.get("hour") == hour:
                return min(band.get("percentageOfBaseline", 50) / 100, 1.0)
    
    # Fallback: use general percentage or estimate based on time
    if "percentageOfBaseline" in crowding_data:
        return min(crowding_data["percentageOfBaseline"] / 100, 1.0)
    
    # Estimate based on typical patterns
    hour = arrival_time.hour
    day = arrival_time.weekday()
    
    if day >= 5:  # Weekend
        return 0.4
    elif 7 <= hour <= 9 or 17 <= hour <= 19:  # Peak hours
        return 0.85
    elif 10 <= hour <= 16:  # Midday
        return 0.5
    else:  # Early morning / late evening
        return 0.3


# ============================================================================
# ROUTE PARSING & SCORING
# ============================================================================

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


def calculate_sensory_score(route: Route, line_status: dict[str, dict]) -> Route:
    """
    Calculate the sensory/stress score for a route.
    Lower score = better for sensory-sensitive travelers.
    
    Formula: S = Σ(C_stop × W_type) + P_penalty
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


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def create_crowding_chart(route: Route) -> go.Figure:
    """Create a visualization of crowding levels along the route."""
    stops = []
    crowding_levels = []
    times = []
    
    for leg in route.legs:
        for stop in leg.stops:
            stops.append(stop.name[:20])  # Truncate long names
            crowding_levels.append(stop.crowding_score * 100)
            times.append(stop.arrival_time.strftime("%H:%M"))
    
    if not stops:
        return None
    
    df = pd.DataFrame({
        "Station": stops,
        "Crowding %": crowding_levels,
        "Time": times
    })
    
    fig = px.bar(
        df, 
        x="Station", 
        y="Crowding %",
        color="Crowding %",
        color_continuous_scale=["green", "yellow", "orange", "red"],
        range_color=[0, 100],
        title="Expected Crowding Along Your Route"
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=400,
        showlegend=False
    )
    
    return fig


def create_hourly_prediction(naptan_id: str) -> go.Figure:
    """Show predicted crowding for the next few hours at a station."""
    now = datetime.now()
    hours = []
    predictions = []
    
    for h in range(6):
        future_time = now + timedelta(hours=h)
        hours.append(future_time.strftime("%H:00"))
        crowding = get_crowding_for_time(naptan_id, future_time) * 100
        predictions.append(crowding)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hours,
        y=predictions,
        mode='lines+markers',
        fill='tozeroy',
        line=dict(color='rgb(100, 149, 237)', width=3),
        marker=dict(size=10)
    ))
    
    fig.update_layout(
        title="Predicted Crowding - Next 6 Hours",
        xaxis_title="Time",
        yaxis_title="Crowding %",
        yaxis_range=[0, 100],
        height=300
    )
    
    return fig


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


# ============================================================================
# STREAMLIT UI
# ============================================================================

def main():
    st.set_page_config(
        page_title="🚇 Sensory-Safe Router",
        page_icon="🚇",
        layout="wide"
    )
    
    # Header
    st.title("🚇 Sensory-Safe Router")
    st.markdown("""
    **A smarter way to navigate London for neurodiverse travelers.**  
    We don't just find the fastest route—we find the *calmest* one.
    """)
    
    st.divider()
    
    # Sidebar for input
    with st.sidebar:
        st.header("🗺️ Plan Your Journey")
        
        # Origin
        origin_query = st.text_input("From (Station Name)", placeholder="e.g., Kings Cross")
        origin_options = []
        origin_id = None
        
        if origin_query and len(origin_query) >= 3:
            origin_options = search_station(origin_query)
            if origin_options:
                origin_names = [s.get("name", "") for s in origin_options]
                selected_origin = st.selectbox("Select origin station:", origin_names)
                origin_id = selected_origin  # Use station name directly
                origin_name = selected_origin
        
        # Destination
        dest_query = st.text_input("To (Station Name)", placeholder="e.g., Waterloo")
        dest_options = []
        dest_id = None
        dest_name = None
        
        if dest_query and len(dest_query) >= 3:
            dest_options = search_station(dest_query)
            if dest_options:
                dest_names = [s.get("name", "") for s in dest_options]
                selected_dest = st.selectbox("Select destination station:", dest_names)
                dest_id = selected_dest  # Use station name directly
                dest_name = selected_dest
        
        # Time selection
        st.subheader("⏰ When?")
        travel_option = st.radio("Departure time:", ["Now", "Custom time"])
        
        if travel_option == "Now":
            travel_time = datetime.now()
        else:
            col1, col2 = st.columns(2)
            with col1:
                travel_date = st.date_input("Date", datetime.now())
            with col2:
                travel_hour = st.time_input("Time", datetime.now())
            travel_time = datetime.combine(travel_date, travel_hour)
        
        st.divider()
        
        # Search button
        search_clicked = st.button("🔍 Find Calm Routes", type="primary", use_container_width=True)
    
    # Main content area
    if search_clicked and origin_id and dest_id:
        with st.spinner("🔄 Analyzing routes and crowding levels..."):
            # Fetch data
            journeys = get_journey_options(origin_id, dest_id, travel_time)
            line_status = get_line_status()
            
            if not journeys:
                st.error("❌ No routes found. Please check your stations and try again.")
                return
            
            # Parse and score routes
            routes = []
            for journey in journeys:
                route = parse_journey(journey, travel_time)
                route = calculate_sensory_score(route, line_status)
                routes.append(route)
            
            # Rank by sensory score
            ranked_routes = rank_routes(routes)
        
        # Display results
        st.header("🎯 Route Options (Ranked by Calmness)")
        
        # Recommendation banner
        recommendation = get_recommendation(ranked_routes)
        if recommendation:
            st.info(recommendation)
        
        # Display each route
        for i, route in enumerate(ranked_routes):
            stress_emoji = get_stress_level_emoji(route.sensory_score)
            is_recommended = i == 0
            
            with st.expander(
                f"{'⭐ RECOMMENDED: ' if is_recommended else ''}"
                f"Route {i+1} — {route.total_duration} mins | {stress_emoji} (Score: {route.sensory_score})",
                expanded=is_recommended
            ):
                # Route summary columns
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("⏱️ Total Time", f"{route.total_duration} mins")
                
                with col2:
                    st.metric("🧠 Sensory Score", f"{route.sensory_score}")
                
                with col3:
                    st.metric("🔄 Changes", f"{len(route.legs) - 1}")
                
                # Delay warning
                if route.has_delays:
                    st.warning(f"⚠️ **Delays detected:** {route.delay_info}")
                
                # Journey steps
                st.subheader("📍 Journey Steps")
                for j, leg in enumerate(route.legs):
                    mode_emoji = {
                        "tube": "🚇",
                        "bus": "🚌",
                        "walking": "🚶",
                        "dlr": "🚈",
                        "overground": "🚆",
                        "elizabeth-line": "🟣"
                    }.get(leg.mode.lower(), "🚃")
                    
                    st.markdown(f"""
                    **{j+1}. {mode_emoji} {leg.line_name}** ({leg.duration_minutes} mins)  
                    {leg.departure_point} → {leg.arrival_point}  
                    *{leg.instruction}*
                    """)
                
                # Crowding visualization
                chart = create_crowding_chart(route)
                if chart:
                    st.plotly_chart(chart, use_container_width=True)
        
        # Hourly prediction for destination
        st.divider()
        st.header("📈 Crowding Forecast")
        st.markdown("See predicted crowding at your destination over the next few hours.")
        
        if dest_id:
            prediction_chart = create_hourly_prediction(dest_id)
            st.plotly_chart(prediction_chart, use_container_width=True)
    
    elif search_clicked:
        st.warning("⚠️ Please select both origin and destination stations.")
    
    else:
        # Welcome / instruction state
        st.markdown("""
        ### 👋 Welcome!
        
        This app helps you find the **calmest route** through London's transport network.
        
        **How it works:**
        1. Enter your start and end stations
        2. We fetch multiple route options from TfL
        3. For each route, we analyze:
           - 📊 **Real-time crowding** at every station
           - ⚠️ **Service disruptions** and delays
           - 🔄 **Number of interchanges** (stressful!)
        4. We calculate a **Sensory Score** and rank routes
        
        **Why does this matter?**
        
        > *"For 20% of Londoners, the fastest route is the wrong route.  
        > Anxiety and sensory overload make the Tube inaccessible."*
        
        ---
        
        👈 **Enter your journey details in the sidebar to get started!**
        """)
        
        # Show live line status
        st.header("🚦 Current Line Status")
        with st.spinner("Fetching live status..."):
            status = get_line_status()
            
            if status:
                cols = st.columns(4)
                for i, (line_id, info) in enumerate(status.items()):
                    col = cols[i % 4]
                    with col:
                        if info["has_severe_delays"]:
                            st.error(f"**{line_id.title()}**\n{info['status']}")
                        else:
                            st.success(f"**{line_id.title()}**\n{info['status']}")


# ============================================================================
# RUN THE APP
# ============================================================================

if __name__ == "__main__":
    main()
