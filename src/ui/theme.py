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

    /* Tighten block spacing only outside expanders */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        margin-bottom: -0.25rem;
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
        letter-spacing: 0.04em;
        font-size: 0.75rem;
        color: #8B949E;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    /* Expander summary row — prevent collapse */
    div[data-testid="stExpander"] summary {
        min-height: 2rem;
        padding: 0.5rem 1rem;
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

    /* ── Active/solving metric (orange highlight) ───── */
    .metric-solving div[data-testid="stMetric"] {
        border-top: 3px solid #FF6B35 !important;
        background: #FF6B3508 !important;
        box-shadow: 0 0 0 1px #FF6B3530, 0 2px 12px #FF6B3518;
    }
    .metric-solving div[data-testid="stMetric"] label {
        color: #FF9A6C !important;
    }
    .metric-solving div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #FF6B35 !important;
    }

    /* ── Sidebar redesign ────────────────────────────── */
    section[data-testid="stSidebar"] {
        background-color: #080D12;
        border-right: 1px solid #21262D;
    }
    section[data-testid="stSidebar"] > div {
        padding-top: 1rem !important;
    }

    /* Sidebar brand header */
    .sidebar-brand {
        display: flex;
        align-items: flex-start;
        gap: 0.65rem;
        padding-bottom: 0.9rem;
        border-bottom: 1px solid #21262D;
        margin-bottom: 0.9rem;
    }
    .sidebar-brand-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #00D4AA;
        box-shadow: 0 0 8px #00D4AA88, 0 0 18px #00D4AA44;
        flex-shrink: 0;
        margin-top: 3px;
    }
    .sidebar-brand-name {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #E6EDF3;
        line-height: 1.3;
    }
    .sidebar-brand-tag {
        display: block;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.55rem;
        letter-spacing: 0.06em;
        color: #00D4AA;
        margin-top: 0.2rem;
    }

    /* Control group wrapper */
    .ctrl-group {
        background: #0D1117;
        border: 1px solid #21262D;
        border-radius: 8px;
        padding: 0.65rem 0.75rem 0.55rem 0.75rem;
        margin-bottom: 0.6rem;
    }
    .ctrl-group-label {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.58rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #6E7681;
        margin-bottom: 0.4rem;
    }

    /* Mode description inside ctrl-group */
    .mode-desc {
        display: block;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.62rem;
        color: #FF6B35;
        background: #FF6B3514;
        border: 1px solid #FF6B3540;
        border-radius: 4px;
        padding: 0.25rem 0.5rem;
        margin-top: 0.45rem;
        line-height: 1.45;
    }

    /* Sidebar selectbox label */
    section[data-testid="stSidebar"] .stSelectbox label p {
        font-size: 0.72rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #8B949E !important;
    }

    /* Sidebar toggle label */
    section[data-testid="stSidebar"] .stToggle p {
        font-size: 0.72rem;
        color: #8B949E;
    }

    /* Sidebar status footer */
    .sidebar-status {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        border-top: 1px solid #21262D;
        padding-top: 0.7rem;
        margin-top: 0.4rem;
    }
    .sidebar-status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: #00D4AA;
        box-shadow: 0 0 4px #00D4AA88;
        flex-shrink: 0;
        animation: pulse 2.5s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; box-shadow: 0 0 4px #00D4AA88; }
        50% { opacity: 0.5; box-shadow: 0 0 2px #00D4AA44; }
    }
    .sidebar-status-text {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.58rem;
        color: #6E7681;
        line-height: 1.4;
    }
    .sidebar-phase-badge {
        display: inline-block;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.55rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        color: #58A6FF;
        background: #58A6FF14;
        border: 1px solid #58A6FF40;
        border-radius: 3px;
        padding: 0.1rem 0.35rem;
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

    /* ── Physics reference card ────────────────────── */
    .physics-card {
        background: #161B22;
        border: 1px solid #30363D;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        border-left: 3px solid #30363D;
    }
    .physics-title {
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        font-size: 0.7rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #8B949E;
        margin-bottom: 0.6rem;
        padding-bottom: 0.3rem;
        border-bottom: 1px solid #30363D;
    }

    /* Equation groups */
    .eq-group {
        margin-bottom: 0.6rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #1C2128;
    }
    .eq-group:last-child {
        margin-bottom: 0;
        padding-bottom: 0;
        border-bottom: none;
    }
    .eq-label {
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        font-size: 0.7rem;
        color: #58A6FF;
        letter-spacing: 0.03em;
        margin-bottom: 0.2rem;
    }
    .eq-formula {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        color: #E6EDF3;
        padding: 0.25rem 0;
        line-height: 1.5;
    }
    .eq-formula sub {
        font-size: 0.65rem;
        color: #8B949E;
    }
    .eq-sub {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        color: #8B949E;
        padding-left: 0.5rem;
        line-height: 1.4;
    }
    .eq-result {
        color: #00D4AA;
        font-weight: 600;
    }
    .eq-note {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.65rem;
        color: #6E7681;
        font-style: italic;
        margin-top: 0.15rem;
    }

    /* Variable glossary table */
    .var-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 0.2rem;
    }
    .var-table tr {
        border-bottom: 1px solid #1C2128;
    }
    .var-table tr:last-child {
        border-bottom: none;
    }
    .var-table td {
        padding: 0.3rem 0.3rem;
        vertical-align: middle;
    }
    .var-sym {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #E6EDF3;
        font-weight: 600;
        white-space: nowrap;
        width: 3.5rem;
    }
    .var-sym sub {
        font-size: 0.6rem;
        color: #8B949E;
    }
    .var-desc {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.68rem;
        color: #8B949E;
    }
    .var-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: #00D4AA;
        font-weight: 600;
        white-space: nowrap;
        text-align: right;
        width: 5rem;
    }
    .var-control {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.62rem;
        font-style: italic;
        color: #6E7681;
        padding-left: 0.4rem;
    }
    .var-footnote {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.6rem;
        color: #6E7681;
        margin-top: 0.5rem;
        padding-top: 0.4rem;
        border-top: 1px solid #1C2128;
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
