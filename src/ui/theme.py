"""Precision Instrument dark theme CSS for Streamlit.

Injected via st.markdown(unsafe_allow_html=True).
Colors, typography, metric cards, layout refinements.
"""

GOOGLE_FONTS = """
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=DM+Sans:ital,wght@0,400;0,500;0,700;1,400&display=swap" rel="stylesheet">
"""

CUSTOM_CSS = """
<style>
    /* ── Global ────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=DM+Sans:ital,wght@0,400;0,500;0,700;1,400&display=swap');

    .stApp {
        font-family: 'DM Sans', sans-serif;
    }

    /* Tighten default Streamlit block spacing */
    div[data-testid="stVerticalBlock"] > div {
        padding-top: 0;
        padding-bottom: 0;
    }

    /* ── Panel containers ──────────────────────────── */
    div[data-testid="stExpander"] {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 8px;
        margin-bottom: 0.4rem;
    }
    div[data-testid="stExpander"] details {
        border: none !important;
    }
    div[data-testid="stExpander"] summary span {
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 0.8rem;
        color: #8B949E;
    }
    /* Compact expander content padding */
    div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
        padding: 0.5rem 1rem 0.75rem 1rem;
    }

    /* ── Metric cards ──────────────────────────────── */
    div[data-testid="stMetric"] {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-top: 3px solid #00D4AA;
        border-radius: 8px;
        padding: 0.75rem 0.75rem;
    }
    div[data-testid="stMetric"] label {
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-size: 0.65rem;
        color: #8B949E;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        font-size: 1.25rem;
        color: #E6EDF3;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
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
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stRadio label {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #8B949E;
    }

    /* ── Title bar ─────────────────────────────────── */
    .main-title {
        font-family: 'DM Sans', sans-serif;
        font-weight: 700;
        font-size: 1.2rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #E6EDF3;
        padding: 0.4rem 0;
        border-bottom: 2px solid #30363D;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .main-title::before {
        content: '';
        display: inline-block;
        width: 8px;
        height: 8px;
        background: #00D4AA;
        border-radius: 50%;
        box-shadow: 0 0 6px #00D4AA88;
    }

    /* ── Section headers ───────────────────────────── */
    .section-header {
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        font-size: 0.75rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #8B949E;
        border-bottom: 1px solid #30363D;
        padding-bottom: 0.3rem;
        margin-bottom: 0.5rem;
        margin-top: 0.25rem;
    }

    /* ── Number inputs (JetBrains Mono) ────────────── */
    input[type="number"], div[data-testid="stNumberInput"] input {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
    }

    /* ── Disabled inputs visual feedback ───────────── */
    div[data-testid="stNumberInput"] input:disabled {
        opacity: 0.4;
        border-color: #00D4AA44;
        background-color: #00D4AA08;
    }

    /* ── Solved-for indicator badge ─────────────────── */
    .solved-badge {
        display: inline-block;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.6rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        color: #00D4AA;
        background: #00D4AA18;
        border: 1px solid #00D4AA44;
        border-radius: 4px;
        padding: 0.1rem 0.4rem;
        margin-left: 0.3rem;
        vertical-align: middle;
    }

    /* ── Unit labels ───────────────────────────────── */
    .unit-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #58A6FF;
    }

    /* ── Utilization bar ───────────────────────────── */
    .util-bar-track {
        background: #30363D;
        border-radius: 4px;
        height: 6px;
        width: 100%;
        margin-top: 0.3rem;
    }
    .util-bar-fill {
        border-radius: 4px;
        height: 6px;
        transition: width 0.3s ease;
    }

    /* ── Compact number input labels ───────────────── */
    div[data-testid="stNumberInput"] label p {
        font-size: 0.8rem;
    }

    /* ── Hide Streamlit branding ───────────────────── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {background: #0D1117;}
</style>
"""


def inject_theme():
    """Call this at the top of app.py to apply the Precision Instrument theme."""
    import streamlit as st
    st.markdown(GOOGLE_FONTS, unsafe_allow_html=True)
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
