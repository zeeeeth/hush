import streamlit as st

def render_route_card(route: dict, index: int, is_best: bool = False):
    """Render a route card with Linear aesthetic."""
    duration = route["duration_min"]
    distance = route["distance_km"]
    steps = route["steps"]
    quiet_score = route.get("quiet_score")

    transit_count = len([s for s in steps if s["type"] == "transit"])
    transfers = max(0, transit_count - 1)
    transfer_text = "Direct" if transfers == 0 else f"{transfers} transfer{'s' if transfers > 1 else ''}"

    steps_html = ""
    for step in steps:
        if step["type"] == "transit":
            line = step["line"]
            color = step.get("color", "#888888")
            steps_html += f'<div class="step-row"><span class="line-badge" style="background-color: {color};">{line}</span><span class="step-details">{step["departure"]} -> {step["arrival"]}</span><span class="step-meta">{step["num_stops"]} stops · {step["duration_min"]}m</span></div>'
        elif step["type"] == "walk":
            steps_html += f'<div class="step-row"><span class="walk-icon">-></span><span class="step-details">Walk {step["distance_m"]}m</span><span class="step-meta">{step["duration_min"]}m</span></div>'

    if quiet_score is not None:
        if quiet_score >= 7:
            quiet_html = f'<span class="quiet-badge-good">• Quiet {quiet_score}/10</span>'
        elif quiet_score >= 4:
            quiet_html = f'<span class="quiet-badge-pending">• Moderate {quiet_score}/10</span>'
        else:
            quiet_html = f'<span class="quiet-badge-bad">• Busy {quiet_score}/10</span>'
    else:
        quiet_html = '<span class="quiet-badge-pending">○ Score pending</span>'

    best_class = ' route-card-best' if is_best else ''
    best_badge = '<span class="best-route-badge">✨ QUIETEST</span>' if is_best else ''
    card_html = f'<div class="route-card{best_class}">{best_badge}<div class="route-header"><div style="display: flex; align-items: center;"><span class="duration-badge">{duration} min</span><span class="route-meta">{distance:.1f} km · {transfer_text}</span></div>{quiet_html}</div>{steps_html}</div>'

    st.markdown(card_html, unsafe_allow_html=True)
