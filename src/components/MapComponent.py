import streamlit as st
import pydeck as pdk

def MapComponent(
    origin_name,
    destination_name,
    stations,
    find_station_coords_by_name,
):
    """Render the interactive NYC Subway Map in the right column."""
    origin_data = stations.get(origin_name, {})
    dest_data = stations.get(destination_name, {})

    markers = []
    if origin_data.get("lat") and origin_data.get("lng"):
        markers.append({
            "name": origin_name,
            "lat": origin_data["lat"],
            "lon": origin_data["lng"],
            "color": [0, 255, 136, 255],
            "radius": 100,
            "type": "origin"
        })
    if dest_data.get("lat") and dest_data.get("lng"):
        markers.append({
            "name": destination_name,
            "lat": dest_data["lat"],
            "lon": dest_data["lng"],
            "color": [255, 68, 68, 255],
            "radius": 100,
            "type": "destination"
        })

    intermediate_stations = []
    best_route = st.session_state.get('best_route')
    if best_route and st.session_state.get('routes_found'):
        transit_steps = [s for s in best_route.get('steps', []) if s['type'] == 'transit']
        seen_coords = set()
        for step in transit_steps:
            dep_name = step['departure']
            if dep_name.lower() != origin_name.lower() and dep_name.lower() != destination_name.lower():
                dep_coords = find_station_coords_by_name(dep_name)
                if dep_coords:
                    coord_key = (round(dep_coords["lat"], 5), round(dep_coords["lng"], 5))
                    if coord_key not in seen_coords:
                        intermediate_stations.append({
                            "name": dep_coords["name"],
                            "lat": dep_coords["lat"],
                            "lon": dep_coords["lng"],
                            "color": [250, 204, 21, 255],
                            "radius": 100,
                            "type": "intermediate"
                        })
                        seen_coords.add(coord_key)
            arr_name = step['arrival']
            if arr_name.lower() != origin_name.lower() and arr_name.lower() != destination_name.lower():
                arr_coords = find_station_coords_by_name(arr_name)
                if arr_coords:
                    coord_key = (round(arr_coords["lat"], 5), round(arr_coords["lng"], 5))
                    if coord_key not in seen_coords:
                        intermediate_stations.append({
                            "name": arr_coords["name"],
                            "lat": arr_coords["lat"],
                            "lon": arr_coords["lng"],
                            "color": [250, 204, 21, 255],
                            "radius": 100,
                            "type": "intermediate"
                        })
                        seen_coords.add(coord_key)

    all_points = markers + intermediate_stations
    if all_points:
        center_lat = sum(m["lat"] for m in all_points) / len(all_points)
        center_lon = sum(m["lon"] for m in all_points) / len(all_points)
    else:
        center_lat, center_lon = 40.7580, -73.9855

    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=12,
        pitch=0,
        bearing=0
    )

    layers = []
    if intermediate_stations:
        intermediate_layer = pdk.Layer(
            "ScatterplotLayer",
            data=intermediate_stations,
            get_position=["lon", "lat"],
            get_color="color",
            get_radius="radius",
            pickable=True
        )
        layers.append(intermediate_layer)
    if markers:
        main_markers = pdk.Layer(
            "ScatterplotLayer",
            data=markers,
            get_position=["lon", "lat"],
            get_color="color",
            get_radius="radius",
            pickable=True
        )
        layers.append(main_markers)

    st.pydeck_chart(
        pdk.Deck(
            layers=layers,
            initial_view_state=view_state,
            map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
            tooltip={
                "html": "<b>{name}</b>",
                "style": {
                    "backgroundColor": "#111111",
                    "color": "white",
                    "border": "1px solid #333",
                    "borderRadius": "8px",
                    "padding": "8px 12px"
                }
            }
        ),
        height=700
    )

    st.markdown("""
    <div style="display: flex; gap: 20px; justify-content: center; margin-top: 12px; font-size: 0.75rem; color: rgba(255,255,255,0.6);">
        <span><span style="display: inline-block; width: 10px; height: 10px; background: #00ff88; border-radius: 50%; margin-right: 6px;"></span>Starting Station</span>
        <span><span style="display: inline-block; width: 10px; height: 10px; background: #ff4444; border-radius: 50%; margin-right: 6px;"></span>Final Station</span>
        <span><span style="display: inline-block; width: 10px; height: 10px; background: #facc15; border-radius: 50%; margin-right: 6px;"></span>Intermediate Station</span>
    </div>
    """, unsafe_allow_html=True)
