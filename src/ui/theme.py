"""Precision Instrument dark theme CSS for Streamlit.

Injected via st.markdown(unsafe_allow_html=True).
Colors, typography, and metric card styling.
"""

GOOGLE_FONTS = """
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=DM+Sans:wght@400;500;700&display=swap" rel="stylesheet">
"""

CUSTOM_CSS = """
<style>
    /* ── Global ────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=DM+Sans:wght@400;500;700&display=swap');

    .stApp {
        font-family: 'DM Sans', sans-serif;
    }

    /* ── Panel containers ──────────────────────────── */
    div[data-testid="stExpander"] {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }
    div[data-testid="stExpander"] summary span {
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 0.85rem;
        color: #8B949E;
    }

    /* ── Metric cards ──────────────────────────────── */
    div[data-testid="stMetric"] {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-top: 3px solid #00D4AA;
        border-radius: 8px;
        padding: 1rem;
    }
    div[data-testid="stMetric"] label {
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-size: 0.75rem;
        color: #8B949E;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        font-size: 1.6rem;
        color: #E6EDF3;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: #58A6FF;
    }

    /* ── Warning metric (amber top border) ─────────── */
    .metric-warning div[data-testid="stMetric"] {
        border-top-color: #F0A830;
    }

    /* ── Error metric (red top border) ─────────────── */
    .metric-error div[data-testid="stMetric"] {
        border-top-color: #F85149;
    }

    /* ── Sidebar styling ───────────────────────────── */
    section[data-testid="stSidebar"] {
        background-color: #0D1117;
        border-right: 1px solid #30363D;
    }

    /* ── Title bar ─────────────────────────────────── */
    .main-title {
        font-family: 'DM Sans', sans-serif;
        font-weight: 700;
        font-size: 1.3rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #E6EDF3;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #30363D;
        margin-bottom: 1rem;
    }

    /* ── Number inputs (JetBrains Mono) ────────────── */
    input[type="number"], div[data-testid="stNumberInput"] input {
        font-family: 'JetBrains Mono', monospace;
    }

    /* ── Unit labels ───────────────────────────────── */
    .unit-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: #58A6FF;
    }

    /* ── Hide Streamlit branding ───────────────────── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""


def inject_theme():
    """Call this at the top of app.py to apply the Precision Instrument theme."""
    import streamlit as st
    st.markdown(GOOGLE_FONTS, unsafe_allow_html=True)
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
