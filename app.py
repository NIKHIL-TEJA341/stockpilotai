"""StockPilot AI — Indian Equity Analysis & Decision Support Platform.

Main Streamlit Application Entrypoint.
Complies with PRD requirements for model selection (Groq openai/gpt-oss-120b),
rich dark-mode financial aesthetics, multi-page sidebar navigation, and statutory disclaimers.
"""

import streamlit as st

# Set page configuration must be first Streamlit command
st.set_page_config(
    page_title="StockPilot AI — Smart Indian Stock Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

from config.settings import settings
from database.db import init_db
from ui.dashboard import render_dashboard
from ui.comparison import render_comparison
from ui.watchlist import render_watchlist
from ui.history import render_history

# Initialize database tables on application boot
init_db()

# ---------------------------------------------------------------------
# Custom Premium Financial Dashboard CSS Styling (Dark Slate & Neon Cyan)
# ---------------------------------------------------------------------
st.markdown("""
<style>
    /* Global Page Background & Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: linear-gradient(180deg, #0B0F19 0%, #0F172A 100%);
        color: #F8FAFC;
    }

    /* Streamlit Top Header Styling - Transparent Blur */
    header[data-testid="stHeader"] {
        background: rgba(11, 15, 25, 0.85) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-bottom: 1px solid rgba(51, 65, 85, 0.4) !important;
    }
    header[data-testid="stHeader"] * {
        color: #F8FAFC !important;
    }

    /* Custom Scrollbars */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #0B0F19;
    }
    ::-webkit-scrollbar-thumb {
        background: #334155;
        border-radius: 4px;
    }

    /* All Headings Light, Crisp & High Contrast */
    h1, h2, h3, h4, h5, h6,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4,
    [data-testid="stMarkdownContainer"] h5,
    [data-testid="stMarkdownContainer"] h6 {
        color: #F8FAFC !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em !important;
    }

    h1, [data-testid="stMarkdownContainer"] h1 {
        color: #FFFFFF !important;
        font-size: 2.1rem !important;
    }

    h2, [data-testid="stMarkdownContainer"] h2 {
        color: #FFFFFF !important;
        font-size: 1.65rem !important;
    }

    h3, [data-testid="stMarkdownContainer"] h3 {
        color: #F1F5F9 !important;
        font-size: 1.35rem !important;
    }

    h4, [data-testid="stMarkdownContainer"] h4 {
        color: #E2E8F0 !important;
        font-size: 1.15rem !important;
    }

    h5, [data-testid="stMarkdownContainer"] h5 {
        color: #38BDF8 !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
    }

    /* Paragraphs and Markdown Text Light Contrast */
    div[data-testid="stMarkdownContainer"] p {
        color: #CBD5E1 !important;
        line-height: 1.6 !important;
    }
    div[data-testid="stMarkdownContainer"] strong,
    div[data-testid="stMarkdownContainer"] b {
        color: #F8FAFC !important;
        font-weight: 700 !important;
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.7) !important;
        border: 1px solid rgba(71, 85, 105, 0.5) !important;
        padding: 14px 18px !important;
        border-radius: 10px !important;
        backdrop-filter: blur(8px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
        transition: transform 0.2s ease, border-color 0.2s ease !important;
    }
    div[data-testid="stMetric"]:hover {
        border-color: rgba(56, 189, 248, 0.6) !important;
        transform: translateY(-2px);
    }
    div[data-testid="stMetricLabel"] > div,
    div[data-testid="stMetricLabel"] p {
        color: #CBD5E1 !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
    }
    div[data-testid="stMetricValue"] > div {
        color: #F8FAFC !important;
        font-weight: 800 !important;
        font-size: 1.45rem !important;
    }

    /* Expanders - High Contrast Dark Slate with Light Text */
    div[data-testid="stExpander"] {
        background: rgba(15, 23, 42, 0.85) !important;
        border: 1px solid rgba(71, 85, 105, 0.55) !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
        margin-bottom: 20px !important;
    }
    div[data-testid="stExpander"] details {
        background: transparent !important;
    }
    div[data-testid="stExpander"] summary {
        background: linear-gradient(90deg, #1E293B 0%, #0F172A 100%) !important;
        color: #F8FAFC !important;
        padding: 12px 18px !important;
        border-bottom: 1px solid rgba(71, 85, 105, 0.4) !important;
        transition: background 0.2s ease !important;
    }
    div[data-testid="stExpander"] summary:hover {
        background: #253347 !important;
    }
    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] summary span {
        color: #F8FAFC !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
    }
    div[data-testid="stExpander"] summary svg {
        color: #38BDF8 !important;
        fill: #38BDF8 !important;
    }
    div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
        background: rgba(15, 23, 42, 0.85) !important;
        padding: 20px !important;
    }

    /* Buttons - Sleek Dark Slate with Crisp Light Text */
    .stButton > button {
        background: #1E293B !important;
        color: #F1F5F9 !important;
        border: 1px solid rgba(71, 85, 105, 0.6) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 8px 16px !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background: #334155 !important;
        color: #38BDF8 !important;
        border-color: #38BDF8 !important;
        box-shadow: 0 0 14px rgba(56, 189, 248, 0.3) !important;
        transform: translateY(-1px);
    }
    .stButton > button:active {
        transform: translateY(0);
    }

    /* Primary Accent Button (Glow Cyan / Blue) */
    button[kind="primary"],
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0284C7 0%, #2563EB 100%) !important;
        border: 1px solid rgba(56, 189, 248, 0.6) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 16px rgba(2, 132, 199, 0.4) !important;
    }
    button[kind="primary"]:hover,
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #0369A1 0%, #1D4ED8 100%) !important;
        box-shadow: 0 6px 22px rgba(56, 189, 248, 0.55) !important;
        border-color: #38BDF8 !important;
    }

    /* Form Widget Labels - Bright Light Text */
    label[data-testid="stWidgetLabel"],
    label[data-testid="stWidgetLabel"] p,
    label[data-testid="stWidgetLabel"] span,
    .stSlider label,
    .stSelectbox label,
    .stNumberInput label,
    .stTextInput label,
    .stMultiSelect label,
    .stRadio label {
        color: #E2E8F0 !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        letter-spacing: 0.2px !important;
    }
    label[data-testid="stWidgetLabel"] svg {
        color: #94A3B8 !important;
    }

    /* Form Input Controls - Dark Slate Background with Bright Light Text */
    div[data-baseweb="input"],
    div[data-baseweb="input"] > div,
    div[data-baseweb="base-input"] {
        background-color: #1E293B !important;
        border: 1px solid rgba(71, 85, 105, 0.6) !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #38BDF8 !important;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.25) !important;
    }
    div[data-baseweb="input"] input {
        color: #F8FAFC !important;
        background-color: transparent !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }
    div[data-baseweb="input"] button {
        color: #CBD5E1 !important;
    }

    /* Selectbox / Dropdowns */
    div[data-baseweb="select"] > div {
        background-color: #1E293B !important;
        border: 1px solid rgba(71, 85, 105, 0.6) !important;
        color: #F8FAFC !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div {
        color: #F8FAFC !important;
        font-weight: 500 !important;
    }
    div[data-baseweb="select"] svg {
        color: #38BDF8 !important;
        fill: #38BDF8 !important;
    }
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] ul,
    ul[role="listbox"] {
        background-color: #1E293B !important;
        border: 1px solid rgba(71, 85, 105, 0.6) !important;
        border-radius: 8px !important;
    }
    li[role="option"] {
        color: #F1F5F9 !important;
        background-color: #1E293B !important;
    }
    li[role="option"]:hover,
    li[role="option"][aria-selected="true"] {
        background-color: #334155 !important;
        color: #38BDF8 !important;
    }

    /* MultiSelect Tags */
    span[data-baseweb="tag"] {
        background-color: #334155 !important;
        border: 1px solid rgba(56, 189, 248, 0.4) !important;
        border-radius: 6px !important;
    }
    span[data-baseweb="tag"] span {
        color: #38BDF8 !important;
        font-weight: 600 !important;
    }

    /* Radio Strategy Options */
    div[role="radiogroup"] label p,
    div[role="radiogroup"] label span {
        color: #E2E8F0 !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
    }

    /* Sliders */
    div[data-testid="stSlider"] div[data-baseweb="slider"] {
        color: #38BDF8 !important;
    }
    div[data-testid="stSlider"] div[data-testid="stTickBar"] span {
        color: #CBD5E1 !important;
        font-weight: 600 !important;
    }
    div[data-testid="stSlider"] div[data-testid="stThumbValue"] {
        color: #38BDF8 !important;
        font-weight: 700 !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0E131F !important;
        border-right: 1px solid rgba(51, 65, 85, 0.5) !important;
    }

    /* Sidebar Navigation Menu Radio Styling */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] {
        background: transparent !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div {
        gap: 6px !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label {
        background: rgba(30, 41, 59, 0.55) !important;
        border: 1px solid rgba(71, 85, 105, 0.4) !important;
        border-radius: 8px !important;
        padding: 9px 14px !important;
        margin-bottom: 4px !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
        display: flex !important;
        align-items: center !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {
        background: rgba(56, 189, 248, 0.15) !important;
        border-color: #38BDF8 !important;
        transform: translateX(3px) !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-checked="true"],
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) {
        background: linear-gradient(90deg, rgba(56, 189, 248, 0.22) 0%, rgba(30, 41, 59, 0.85) 100%) !important;
        border-color: #38BDF8 !important;
        box-shadow: 0 0 14px rgba(56, 189, 248, 0.2) !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label p,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label span,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[data-testid="stMarkdownContainer"] p {
        color: #F8FAFC !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.2px !important;
    }

    /* Dataframe tables */
    div[data-testid="stDataFrame"] {
        background: rgba(15, 23, 42, 0.7) !important;
        border: 1px solid rgba(71, 85, 105, 0.5) !important;
        border-radius: 8px !important;
        overflow: hidden;
    }

    /* Dividers */
    hr {
        border-color: rgba(71, 85, 105, 0.4) !important;
        margin: 20px 0 !important;
    }

    /* Spinner & Status */
    div[data-testid="stStatusWidget"],
    div.stSpinner > div {
        color: #38BDF8 !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Sidebar Branding & Navigation
# ---------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 24px; padding: 4px 0;">
        <span style="font-size: 2.2rem; filter: drop-shadow(0 0 10px rgba(56, 189, 248, 0.4));">🚀</span>
        <div>
            <h2 style="margin: 0; font-size: 1.45rem; font-weight: 800; background: linear-gradient(90deg, #38BDF8, #818CF8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                StockPilot AI
            </h2>
            <p style="margin: 0; font-size: 0.8rem; color: #94A3B8; font-weight: 500;">Indian Market Intelligence</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.8px; color: #94A3B8; font-weight: 700; margin-bottom: 10px; padding-left: 2px;">
        Navigation Menu
    </div>
    """, unsafe_allow_html=True)

    # Navigation Menu
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Dashboard"

    nav_options = [
        "📊 Dashboard",
        "⚖️ Compare Stocks",
        "⭐ Watchlist",
        "📜 Analysis History",
    ]

    # Find matching index
    current_idx = 0
    for i, opt in enumerate(nav_options):
        if st.session_state["current_page"] in opt:
            current_idx = i

    selected_nav = st.radio(
        "Navigation",
        options=nav_options,
        index=current_idx,
        label_visibility="collapsed",
    )

    clean_page = selected_nav.split(" ", 1)[-1]
    st.session_state["current_page"] = clean_page

# ---------------------------------------------------------------------
# Page Routing
# ---------------------------------------------------------------------
page = st.session_state["current_page"]

if page == "Dashboard":
    render_dashboard()
elif page == "Compare Stocks":
    render_comparison()
elif page == "Watchlist":
    render_watchlist()
elif page == "Analysis History":
    render_history()

# ---------------------------------------------------------------------
# Statutory Financial Disclaimer Banner (PRD Section 12 & FR-16)
# ---------------------------------------------------------------------
st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
st.markdown("""
<div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(71, 85, 105, 0.3); border-radius: 8px; padding: 14px 18px; margin-top: 30px;">
    <div style="font-size: 0.8rem; font-weight: 700; color: #F59E0B; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
        <span>⚠️</span> Statutory Financial Disclaimer & Responsible Output Notice
    </div>
    <p style="font-size: 0.78rem; color: #CBD5E1; margin: 0; line-height: 1.55;">
        StockPilot AI provides AI-generated analysis based on available financial data and historical information. It is intended for informational and educational purposes and is <b>not personalized investment advice</b>. Stock prices and data may be delayed, incomplete, or inaccurate. Historical performance does not guarantee future results, and returns are not guaranteed. Investments in securities are subject to market risks, including the possible loss of capital. Users should independently verify information and consider their financial circumstances before making investment decisions.
    </p>
</div>
""", unsafe_allow_html=True)
