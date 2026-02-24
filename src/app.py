"""
MTA Sensory-Safe Router
A smart routing app for NYC subway with quiet score ratings.
Glassmorphism design with map overlay.
"""

import streamlit as st
import os
from dotenv import load_dotenv
from linear_css import inject_custom_css
from Components.MapComponent import MapComponent
from Components.Header import Header
from Components.SearchInputs import SearchInputs
from Components.SearchResults import SearchResults
from AppHelpers.station_data import load_station_coordinates, get_station_list, find_station_coords_by_name
from AppHelpers.routing import get_routes

def main():
    st.set_page_config(
        page_title="Hush",
        page_icon="🚇",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    inject_custom_css()
    
    # Load data
    coords = load_station_coordinates()
    stations = get_station_list()
    
    if not stations:
        st.markdown("""
        <div class="error-card">Failed to load station data.</div>
        """, unsafe_allow_html=True)
        return
    
    station_names = list(stations.keys())
    
    # Two-column layout
    left_col, right_col = st.columns([1, 2])
    
    with left_col:
        # Header
        Header()
        
        origin_name, destination_name, search_clicked = SearchInputs(station_names)
        SearchResults(
            search_clicked=search_clicked,
            origin_name=origin_name,
            destination_name=destination_name,
            stations=stations,
            coords=coords,
            get_routes=get_routes
        )
    
    with right_col:
        MapComponent(
            origin_name=origin_name,
            destination_name=destination_name,
            stations=stations,
            find_station_coords_by_name=find_station_coords_by_name
        )

if __name__ == "__main__":
    main()
