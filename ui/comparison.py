"""Stock Comparison View for StockPilot AI (Feature 8).

Enables side-by-side comparison of 2 or more Indian equities with normalized
price performance overlay charts, deterministic technical indicators, and volatility metrics.
"""

from typing import Any
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from services.market_data_service import get_stock_data, normalize_symbol
from services.stock_screener import load_stock_universe
from tools.analysis_tools import (
    calculate_historical_returns,
    calculate_sma,
    calculate_rsi,
    calculate_volatility,
)


def render_comparison() -> None:
    """Render the Stock Comparison page."""
    st.markdown("""
    <div style="margin-bottom: 12px;">
        <h1 style="font-size: 2rem; font-weight: 800; color: #FFFFFF; margin: 0 0 6px 0; display: flex; align-items: center; gap: 10px;">
            <span style="filter: drop-shadow(0 0 8px rgba(56, 189, 248, 0.4));">⚖️</span> Compare Stocks
        </h1>
        <p style="color: #CBD5E1; font-size: 0.95rem; margin: 0; line-height: 1.5;">
            Directly compare multiple Indian equities side-by-side with normalized performance charts and consistent mathematical metrics.
        </p>
    </div>
    """, unsafe_allow_html=True)

    universe = load_stock_universe()
    all_symbols = [s["symbol"] for s in universe]
    symbol_names = {s["symbol"]: f"{s['symbol']} ({s['name']})" for s in universe}

    col1, col2 = st.columns([3, 1], gap="medium")
    with col1:
        default_picks = ["RELIANCE.NS", "TCS.NS"] if "RELIANCE.NS" in all_symbols and "TCS.NS" in all_symbols else all_symbols[:2]
        selected_symbols = st.multiselect(
            "Select Stocks to Compare (2 or more)",
            options=all_symbols,
            default=default_picks,
            format_func=lambda s: symbol_names.get(s, s),
            max_selections=5,
        )

    with col2:
        period = st.selectbox(
            "Historical Period",
            options=["3mo", "6mo", "1y", "2y", "5y"],
            index=2,
            help="Common historical window for all compared stocks.",
        )

    if len(selected_symbols) < 2:
        st.info("💡 Please select at least 2 stocks above to begin side-by-side comparison.")
        return

    # Fetch and compute data for each selected stock
    stocks_data = []
    with st.spinner("Fetching market data and computing comparison metrics..."):
        for sym in selected_symbols:
            norm_sym = normalize_symbol(sym)
            data = get_stock_data(norm_sym, period=period)
            if data.get("status") == "success":
                closing = data["closing_prices"]
                ret = calculate_historical_returns(closing, period_name=period)
                sma = calculate_sma(closing, fast_period=20, slow_period=50)
                rsi = calculate_rsi(closing, period=14)
                vol = calculate_volatility(closing)

                stocks_data.append({
                    "symbol": norm_sym,
                    "name": data.get("short_name", norm_sym),
                    "sector": data.get("sector", "General"),
                    "price": data.get("current_price", 0.0),
                    "return_pct": ret.get("return_pct"),
                    "rsi": rsi.get("rsi"),
                    "rsi_zone": rsi.get("zone"),
                    "trend": sma.get("trend"),
                    "volatility_ann": vol.get("annualized_volatility_pct"),
                    "vol_risk": vol.get("risk_category"),
                    "history": data.get("history", []),
                })

    if len(stocks_data) < 2:
        st.error("Could not retrieve sufficient historical data for the selected stocks.")
        return

    # -------------------------------------------------------------
    # 1. Normalized Performance Chart (Base 100)
    # -------------------------------------------------------------
    st.markdown("### 📈 Normalized Performance Comparison (Base = 100)")
    st.caption("All stock prices are indexed to 100 at the start of the period for direct relative performance comparison.")

    palette = ["#38BDF8", "#34D399", "#F472B6", "#FBBF24", "#A78BFA"]
    fig = go.Figure()

    for i, s in enumerate(stocks_data):
        hist = s.get("history", [])
        if hist and len(hist) > 1:
            df = pd.DataFrame(hist)
            df["date"] = pd.to_datetime(df["date"])
            base_price = df["close"].iloc[0]
            if base_price > 0:
                df["normalized"] = (df["close"] / base_price) * 100.0

                fig.add_trace(go.Scatter(
                    x=df["date"],
                    y=df["normalized"],
                    mode="lines",
                    name=f"{s['name']} ({s['symbol']})",
                    line=dict(color=palette[i % len(palette)], width=2.5),
                ))

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Normalized Value (Base 100)",
        template="plotly_dark",
        height=380,
        margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        paper_bgcolor="rgba(15, 23, 42, 0.4)",
        plot_bgcolor="rgba(15, 23, 42, 0.4)",
    )
    st.plotly_chart(fig, use_container_width=True)

    # -------------------------------------------------------------
    # 2. Side-by-Side Comparison Table
    # -------------------------------------------------------------
    st.markdown("### 📊 Metrics Side-by-Side")

    comp_rows = []
    for s in stocks_data:
        comp_rows.append({
            "Stock": f"{s['name']} ({s['symbol']})",
            "Sector": s["sector"],
            "Current Price (₹)": f"₹{s['price']:,.2f}",
            f"Return ({period})": f"{'+' if (s.get('return_pct') or 0) > 0 else ''}{s.get('return_pct')}%",
            "RSI (14)": f"{s.get('rsi')} ({s.get('rsi_zone', '').split(' ')[0]})",
            "SMA Trend": s.get("trend", "Neutral"),
            "Annual Volatility": f"{s.get('volatility_ann')}%",
        })

    comp_table_df = pd.DataFrame(comp_rows)
    st.dataframe(comp_table_df, use_container_width=True, hide_index=True)

    # -------------------------------------------------------------
    # 3. Key Observations & Trade-offs
    # -------------------------------------------------------------
    st.markdown("### 💡 Analytical Takeaways")
    c_cols = st.columns(len(stocks_data))
    for idx, s in enumerate(stocks_data):
        with c_cols[idx]:
            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(71, 85, 105, 0.4); border-radius: 8px; padding: 14px;">
                <h5 style="color: {palette[idx % len(palette)]}; margin-bottom: 8px;">{s['name']}</h5>
                <p style="font-size: 0.85rem; color: #CBD5E1; margin: 4px 0;"><b>Momentum:</b> {s.get('rsi_zone')}</p>
                <p style="font-size: 0.85rem; color: #CBD5E1; margin: 4px 0;"><b>Trend:</b> {s.get('trend')}</p>
                <p style="font-size: 0.85rem; color: #CBD5E1; margin: 4px 0;"><b>Risk Category:</b> {s.get('vol_risk')}</p>
            </div>
            """, unsafe_allow_html=True)
