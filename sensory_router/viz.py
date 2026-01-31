from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .tfl_api import get_crowding_for_time
from .models import Route


def create_crowding_chart(route: Route) -> go.Figure | None:
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
