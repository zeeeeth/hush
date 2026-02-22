def inject_custom_css():
    import streamlit as st
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Root variables */
    :root {
        --bg-primary: #0a0a0a;
        --bg-secondary: #111111;
        --bg-elevated: #161616;
        --border-subtle: rgba(255, 255, 255, 0.08);
        --border-default: rgba(255, 255, 255, 0.1);
        --text-primary: #ffffff;
        --text-secondary: rgba(255, 255, 255, 0.6);
        --text-tertiary: rgba(255, 255, 255, 0.4);
        --accent-green: #00ff88;
        --accent-green-dim: rgba(0, 255, 136, 0.15);
        --accent-red: #ff4444;
        --accent-red-dim: rgba(255, 68, 68, 0.15);
        --accent-yellow: #ffd700;
        --accent-yellow-dim: rgba(255, 215, 0, 0.15);
        --accent-purple: #8b5cf6;
    }
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Pure black background */
    .stApp {
        background: var(--bg-primary);
    }
    
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }
    
    /* Card with glow effect */
    .linear-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        position: relative;
        transition: all 0.2s ease;
    }
    
    .linear-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        border-radius: 12px;
        background: radial-gradient(ellipse at top, rgba(0, 255, 136, 0.03) 0%, transparent 50%);
        pointer-events: none;
    }
    
    .linear-card:hover {
        border-color: var(--border-default);
        background: var(--bg-elevated);
    }
    
    /* Search container */
    .search-container {
        background: var(--bg-secondary);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 16px;
    }
    
    /* Map container with glow */
    .map-container {
        background: var(--bg-secondary);
        border: 1px solid var(--border-subtle);
        border-radius: 16px;
        height: 85vh;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        position: relative;
        overflow: hidden;
    }
    
    .map-container::before {
        content: '';
        position: absolute;
        top: -50%;
        left: 50%;
        transform: translateX(-50%);
        width: 80%;
        height: 50%;
        background: radial-gradient(ellipse, rgba(0, 255, 136, 0.08) 0%, transparent 70%);
        pointer-events: none;
    }
    
    /* Typography */
    .app-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 4px;
        letter-spacing: -0.5px;
    }
    
    .app-subtitle {
        font-size: 0.9rem;
        color: var(--text-tertiary);
        margin-bottom: 24px;
    }
    
    .section-label {
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--text-tertiary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }
    
    /* Override Streamlit selectbox */
    .stSelectbox > div > div {
        background: var(--bg-primary) !important;
        border: 1px solid var(--border-default) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
    }
    
    .stSelectbox > div > div:hover {
        border-color: rgba(255, 255, 255, 0.2) !important;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: var(--accent-green) !important;
        box-shadow: 0 0 0 1px var(--accent-green) !important;
    }
    
    .stSelectbox label {
        color: var(--text-secondary) !important;
    }
    
    /* Primary button - neon green */
    .stButton > button {
        background: var(--accent-green) !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        transition: all 0.15s ease !important;
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.3) !important;
    }
    
    .stButton > button:hover {
        background: #00cc6a !important;
        box-shadow: 0 0 30px rgba(0, 255, 136, 0.5) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Route card */
    .route-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 16px 20px;
        margin: 8px 0;
        transition: all 0.15s ease;
        position: relative;
    }
    
    .route-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0, 255, 136, 0.3), transparent);
        opacity: 0;
        transition: opacity 0.15s ease;
    }
    
    .route-card:hover {
        border-color: var(--border-default);
        background: var(--bg-elevated);
    }
    
    .route-card:hover::before {
        opacity: 1;
    }
    
    /* Best route styling */
    .route-card-best {
        border-color: var(--accent-green) !important;
        box-shadow: 0 0 30px rgba(0, 255, 136, 0.15);
        position: relative;
    }
    
    .route-card-best::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        border-radius: 12px;
        background: radial-gradient(ellipse at top, rgba(0, 255, 136, 0.08) 0%, transparent 60%);
        pointer-events: none;
    }
    
    .best-route-badge {
        position: absolute;
        top: -10px;
        right: 20px;
        background: var(--accent-green);
        color: #000;
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        z-index: 10;
    }
    
    /* Duration badge */
    .duration-badge {
        background: var(--bg-primary);
        color: var(--text-primary);
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.875rem;
        border: 1px solid var(--border-default);
        display: inline-block;
    }
    
    /* Quiet score - neon green for good, red for bad */
    .quiet-badge-good {
        background: var(--accent-green-dim);
        color: var(--accent-green);
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
        border: 1px solid rgba(0, 255, 136, 0.2);
    }
    
    .quiet-badge-bad {
        background: var(--accent-red-dim);
        color: var(--accent-red);
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
        border: 1px solid rgba(255, 68, 68, 0.2);
    }
    
    .quiet-badge-pending {
        background: var(--accent-yellow-dim);
        color: var(--accent-yellow);
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: 500;
        font-size: 0.8rem;
        border: 1px solid var(--border-subtle);
    }
    
    /* Line badge */
    .line-badge {
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.8rem;
        color: white;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 36px;
    }
    
    /* Step row */
    .step-row {
        display: flex;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid var(--border-subtle);
        color: var(--text-primary);
        font-size: 0.875rem;
    }
    
    .step-row:last-child {
        border-bottom: none;
        padding-bottom: 0;
    }
    
    .step-details {
        flex: 1;
        margin-left: 12px;
        color: var(--text-secondary);
    }
    
    .step-meta {
        color: var(--text-tertiary);
        font-size: 0.8rem;
    }
    
    /* Walk icon */
    .walk-icon {
        width: 36px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        color: var(--text-tertiary);
    }
    
    /* Route header */
    .route-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--border-subtle);
    }
    
    .route-meta {
        color: var(--text-tertiary);
        font-size: 0.8rem;
        margin-left: 12px;
    }
    
    /* Results header */
    .results-header {
        color: var(--text-tertiary);
        font-size: 0.8rem;
        margin: 16px 0 8px 0;
    }
    
    /* Prediction time banner */
    .prediction-banner {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(0, 255, 136, 0.1) 100%);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 10px;
        padding: 14px 18px;
        margin: 16px 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .prediction-icon {
        font-size: 1.5rem;
    }
    
    .prediction-text {
        flex: 1;
    }
    
    .prediction-label {
        font-size: 0.7rem;
        font-weight: 500;
        color: var(--accent-purple);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 2px;
    }
    
    .prediction-time {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .prediction-hint {
        font-size: 0.75rem;
        color: var(--text-tertiary);
        margin-top: 2px;
    }
    
    /* Error state */
    .error-card {
        background: var(--accent-red-dim);
        border: 1px solid rgba(255, 68, 68, 0.2);
        border-radius: 8px;
        padding: 16px;
        color: var(--accent-red);
        text-align: center;
    }
    
    /* Warning/spinner overrides */
    .stSpinner > div {
        border-color: var(--accent-green) !important;
    }
    
    .stWarning {
        background: var(--bg-elevated) !important;
        color: var(--text-secondary) !important;
    }
    
    /* Animated Loading State */
    .loading-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40px 20px;
        gap: 16px;
    }
    
    .loading-dots {
        display: flex;
        gap: 8px;
    }
    
    .loading-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: var(--accent-green);
        animation: loadingPulse 1.4s ease-in-out infinite;
    }
    
    .loading-dot:nth-child(1) {
        animation-delay: 0s;
    }
    
    .loading-dot:nth-child(2) {
        animation-delay: 0.2s;
    }
    
    .loading-dot:nth-child(3) {
        animation-delay: 0.4s;
    }
    
    @keyframes loadingPulse {
        0%, 80%, 100% {
            transform: scale(0.6);
            opacity: 0.4;
        }
        40% {
            transform: scale(1);
            opacity: 1;
        }
    }
    
    .loading-text {
        color: var(--text-secondary);
        font-size: 0.9rem;
        animation: loadingTextPulse 2s ease-in-out infinite;
    }
    
    @keyframes loadingTextPulse {
        0%, 100% { opacity: 0.5; }
        50% { opacity: 1; }
    }
    
    .loading-subtext {
        color: var(--text-tertiary);
        font-size: 0.75rem;
        margin-top: -8px;
    }
    
    .loading-train {
        font-size: 1.5rem;
        animation: trainMove 2s ease-in-out infinite;
    }
    
    @keyframes trainMove {
        0% { transform: translateX(-20px); }
        50% { transform: translateX(20px); }
        100% { transform: translateX(-20px); }
    }
    </style>
    """, unsafe_allow_html=True)