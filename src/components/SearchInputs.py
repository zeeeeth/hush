import streamlit as st

def SearchInputs(station_names):
    st.markdown('<div class="section-label">From</div>', unsafe_allow_html=True)
    origin_name = st.selectbox(
        "Origin",
        station_names,
        index=station_names.index("Times Sq-42 St") if "Times Sq-42 St" in station_names else 0,
        key="origin",
        label_visibility="collapsed"
    )
    st.markdown('<div class="section-label" style="margin-top: 16px;">To</div>', unsafe_allow_html=True)
    destination_name = st.selectbox(
        "Destination",
        station_names,
        index=station_names.index("Bowling Green") if "Bowling Green" in station_names else 1,
        key="destination",
        label_visibility="collapsed"
    )
    search_clicked = st.button("Find routes", use_container_width=True)
    return origin_name, destination_name, search_clicked
