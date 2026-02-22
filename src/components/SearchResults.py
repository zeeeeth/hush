import streamlit as st
from datetime import datetime, timedelta
from .RouteCard import render_route_card

def SearchResults(search_clicked, origin_name, destination_name, stations, coords, get_routes):
    if search_clicked:
        if origin_name == destination_name:
            st.warning("Select different stations")
        else:
            origin_id = stations[origin_name]["id"]
            dest_id = stations[destination_name]["id"]
            loading_placeholder = st.empty()
            loading_placeholder.markdown("""
            <div class="loading-container">
                <div class="loading-train">🚇</div>
                <div class="loading-dots">
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                </div>
                <div class="loading-text">Analyzing routes...</div>
                <div class="loading-subtext">Predicting congestion for the next hour</div>
            </div>
            """, unsafe_allow_html=True)
            routes, error = get_routes(origin_id, dest_id, coords)
            loading_placeholder.empty()
            if error:
                st.markdown(f"""
                <div class="error-card">❌ {error}</div>
                """, unsafe_allow_html=True)
            elif routes:
                now = datetime.now()
                one_hour_later = now + timedelta(hours=1)
                st.markdown(f"""
                <div class="prediction-banner">
                    <span class="prediction-icon">🔮</span>
                    <div class="prediction-text">
                        <div class="prediction-label">AI Congestion Forecast</div>
                        <div class="prediction-time">{now.strftime('%H:%M')} -> {one_hour_later.strftime('%H:%M')}</div>
                        <div class="prediction-hint">Scores reflect predicted crowding for the next hour</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                best_route = max(routes, key=lambda r: r.get('quiet_score', 0) or 0)
                best_idx = routes.index(best_route)
                st.session_state['best_route'] = best_route
                st.session_state['routes_found'] = True
                st.markdown(f"""
                <div class="results-header">
                    {len(routes)} route{'s' if len(routes) > 1 else ''} found · Route {best_idx + 1} recommended
                </div>
                """, unsafe_allow_html=True)
                for i, route in enumerate(routes):
                    render_route_card(route, i, is_best=(i == best_idx))
            else:
                st.markdown("""
                <div class="error-card">No routes found</div>
                """, unsafe_allow_html=True)
