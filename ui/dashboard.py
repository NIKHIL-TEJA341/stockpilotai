"""Main Investment Analysis Dashboard for StockPilot AI.

Implements Feature 1 (Preferences Form), Feature 6 (Interactive Dashboard),
and Feature 7 (Tool Execution Transparency) with high-end financial UI styling.
"""

from typing import Any
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from services.analysis_service import run_full_investment_analysis
from database.repository import add_to_watchlist, is_in_watchlist


def render_dashboard() -> None:
    """Render the primary StockPilot AI investment analysis dashboard."""
    st.markdown("""
    <div style="margin-bottom: 12px;">
        <h1 style="font-size: 2rem; font-weight: 800; color: #FFFFFF; margin: 0 0 6px 0; display: flex; align-items: center; gap: 10px;">
            <span style="filter: drop-shadow(0 0 8px rgba(56, 189, 248, 0.4));">📊</span> AI-Powered Investment Analysis
        </h1>
        <p style="color: #CBD5E1; font-size: 0.95rem; margin: 0; line-height: 1.5;">
            Data-grounded Indian equity screening powered by <b style="color: #38BDF8;">StockPilot AI Intelligence</b>, deterministic financial formulas, and verified market tools.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 1. Investment Preference Form (Feature 1)
    # -------------------------------------------------------------
    with st.expander("⚙️ Investment Preferences & Constraints", expanded="analysis_result" not in st.session_state):
        col1, col2 = st.columns([1, 1], gap="medium")

        with col1:
            st.markdown("<h4 style='color: #38BDF8; font-size: 1.1rem; font-weight: 700; margin: 0 0 12px 0;'>1. Capital & Horizon</h4>", unsafe_allow_html=True)
            
            # Quick-select budget buttons
            quick_cols = st.columns(4)
            selected_preset = None
            if quick_cols[0].button("₹5,000", use_container_width=True):
                st.session_state["budget_input"] = 5000.0
            if quick_cols[1].button("₹10,000", use_container_width=True):
                st.session_state["budget_input"] = 10000.0
            if quick_cols[2].button("₹25,000", use_container_width=True):
                st.session_state["budget_input"] = 25000.0
            if quick_cols[3].button("₹50,000", use_container_width=True):
                st.session_state["budget_input"] = 50000.0

            default_budget = st.session_state.get("budget_input", 10000.0)
            budget = st.number_input(
                "Investment Budget (INR ₹)",
                min_value=500.0,
                max_value=10000000.0,
                value=float(default_budget),
                step=1000.0,
                format="%.2f",
                help="Total capital available for this investment allocation.",
            )

            duration = st.selectbox(
                "Investment Duration",
                options=["Short term", "Medium term", "Long term", "Very long term"],
                index=1,
                help="Short (<1y), Medium (1-3y), Long (3-5y), Very Long (>5y)",
            )

            risk_tolerance = st.select_slider(
                "Risk Tolerance",
                options=["Low", "Moderate", "High"],
                value="Moderate",
                help="Conservative (capital preservation), Moderate (balanced), High (growth/momentum)",
            )

        with col2:
            st.markdown("<h4 style='color: #38BDF8; font-size: 1.1rem; font-weight: 700; margin: 0 0 12px 0;'>2. Screening Scope & Structure</h4>", unsafe_allow_html=True)

            stock_preference = st.selectbox(
                "Stock Preference (Market Cap)",
                options=["No preference", "Large-cap stocks", "Mid-cap stocks", "Small-cap stocks"],
                index=0,
                help="Filter candidate universe by market capitalization tier.",
            )

            investment_type = st.radio(
                "Investment Strategy Type",
                options=["Individual stock candidates", "Diversified stock basket"],
                index=0,
                horizontal=True,
                help="Top 3 individual picks vs an allocated 4-stock balanced basket.",
            )

            market = st.selectbox(
                "Exchange Universe",
                options=["NSE", "BSE"],
                index=0,
                help="Default Indian stock exchange universe.",
            )

        submit_btn = st.button("🚀 Analyze My Investment", type="primary", use_container_width=True)

    # -------------------------------------------------------------
    # 2. Trigger Analysis Process
    # -------------------------------------------------------------
    if submit_btn:
        with st.spinner("Analyzing candidate universe, computing mathematical models, and generating market intelligence..."):
            result = run_full_investment_analysis(
                budget=budget,
                duration=duration,
                risk_tolerance=risk_tolerance,
                stock_preference=stock_preference,
                investment_type=investment_type,
                market=market,
            )
            st.session_state["analysis_result"] = result

    # -------------------------------------------------------------
    # 3. Display Analysis Results (Feature 6 & 7)
    # -------------------------------------------------------------
    if "analysis_result" in st.session_state:
        res = st.session_state["analysis_result"]
        if res.get("status") != "success":
            st.error(f"⚠️ Analysis could not complete: {res.get('message')}")
            return

        summary = res["summary"]
        shortlisted = res["shortlisted"]
        tool_logs = res.get("tool_logs", [])

        st.markdown("---")

        # Summary Metric Cards
        s_col1, s_col2, s_col3, s_col4, s_col5, s_col6 = st.columns(6)
        s_col1.metric("Budget", f"₹{summary['budget']:,.0f}")
        s_col2.metric("Screened", summary["candidates_analyzed"])
        s_col3.metric("Shortlisted", summary["shortlisted_count"])
        s_col4.metric("Horizon", summary["duration"])
        s_col5.metric("Risk Profile", summary["risk_tolerance"])
        s_col6.metric("Data Date", summary["latest_data_date"])

        # ---------------------------------------------------------
        # Diversified Basket Allocation Card (if applicable)
        # ---------------------------------------------------------
        basket_data = res.get("basket_allocation")
        if basket_data and basket_data.get("status") == "success":
            st.markdown("### 🧺 Diversified Basket Allocation")
            b_col1, b_col2, b_col3 = st.columns([1, 1, 2])
            b_col1.metric("Total Invested", f"₹{basket_data.get('total_invested'):,.2f}")
            b_col2.metric("Remaining Cash", f"₹{basket_data.get('cash_remaining'):,.2f}")
            b_col3.caption(f"💡 {basket_data.get('note')}")

            basket_df = pd.DataFrame(basket_data.get("basket", []))
            if not basket_df.empty:
                st.dataframe(
                    basket_df.rename(columns={
                        "symbol": "Ticker",
                        "share_price": "Price (₹)",
                        "target_weight_pct": "Target Weight (%)",
                        "allocated_budget": "Target Allocation (₹)",
                        "affordable_shares": "Allocated Shares",
                        "cost": "Total Value (₹)",
                    }),
                    use_container_width=True,
                    hide_index=True,
                )

        # ---------------------------------------------------------
        # Shortlisted Candidate Cards
        # ---------------------------------------------------------
        st.markdown("### 🏆 Shortlisted Stock Candidates")

        for idx, stock in enumerate(shortlisted):
            sym = stock["symbol"]
            with st.container():
                st.markdown(f"""
                <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(71, 85, 105, 0.5); border-radius: 12px; padding: 18px; margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div>
                            <span style="font-size: 1.3rem; font-weight: 700; color: #38BDF8;">{stock['short_name']}</span>
                            <span style="background: #334155; color: #E2E8F0; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; margin-left: 8px;">{stock['symbol']}</span>
                            <span style="color: #94A3B8; font-size: 0.85rem; margin-left: 8px;">• {stock['sector']} • {stock['market_cap_category']}</span>
                        </div>
                        <div style="text-align: right;">
                            <span style="background: rgba(16, 185, 129, 0.2); border: 1px solid #10B981; color: #34D399; font-weight: 700; padding: 4px 12px; border-radius: 20px; font-size: 0.95rem;">
                                Score: {stock['screening_score']}/100
                            </span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                card_c1, card_c2, card_c3, card_c4, card_c5 = st.columns(5)
                card_c1.metric("Current Price", f"₹{stock['current_price']:,.2f}")
                card_c2.metric("Return", f"{'+' if (stock.get('return_pct') or 0) > 0 else ''}{stock.get('return_pct')}%")
                card_c3.metric("RSI (14)", f"{stock.get('rsi')}", delta=stock.get("rsi_zone"))
                card_c4.metric("Volatility (Ann.)", f"{stock.get('annualized_volatility_pct')}%")
                card_c5.metric("Affordable Shares", f"{stock.get('affordable_shares')} shares", delta=f"₹{stock.get('total_cost'):,.0f} spent")

                # Strengths, Cautions & Actions
                det_c1, det_c2 = st.columns([1, 1], gap="medium")
                with det_c1:
                    st.markdown("**✅ Observed Strengths:**")
                    for r in stock.get("key_reasons", []):
                        st.markdown(f"- <span style='color: #A7F3D0;'>{r}</span>", unsafe_allow_html=True)

                with det_c2:
                    st.markdown("**⚠️ Key Risks & Cautions:**")
                    for c in stock.get("key_cautions", []):
                        st.markdown(f"- <span style='color: #FCA5A5;'>{c}</span>", unsafe_allow_html=True)

                # Watchlist action
                w_col1, w_col2 = st.columns([1, 4])
                in_list = is_in_watchlist(sym)
                btn_label = "⭐ In Watchlist" if in_list else "➕ Add to Watchlist"
                if w_col1.button(btn_label, key=f"wl_btn_{sym}", disabled=in_list):
                    add_to_watchlist(sym, stock["short_name"], stock["sector"], stock["market_cap_category"])
                    st.toast(f"Added {sym} to your Watchlist!")
                    st.rerun()

                # Interactive Price Chart
                history = stock.get("history", [])
                if history and len(history) > 1:
                    hist_df = pd.DataFrame(history)
                    hist_df["date"] = pd.to_datetime(hist_df["date"])

                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=hist_df["date"],
                        y=hist_df["close"],
                        mode="lines",
                        name="Close Price (₹)",
                        line=dict(color="#38BDF8", width=2.5),
                        fill="tozeroy",
                        fillcolor="rgba(56, 189, 248, 0.08)",
                    ))
                    fig.update_layout(
                        title=f"{stock['short_name']} ({sym}) — Historical Price Trend",
                        xaxis_title="Date",
                        yaxis_title="Price (INR ₹)",
                        template="plotly_dark",
                        height=280,
                        margin=dict(l=10, r=10, t=35, b=10),
                        paper_bgcolor="rgba(15, 23, 42, 0.4)",
                        plot_bgcolor="rgba(15, 23, 42, 0.4)",
                    )
                    st.plotly_chart(fig, use_container_width=True)

                st.markdown("<hr style='border: 0.5px solid rgba(71, 85, 105, 0.3); margin: 25px 0;'>", unsafe_allow_html=True)

        # ---------------------------------------------------------
        # Side-by-side Candidate Comparison Table (Feature 6.D)
        # ---------------------------------------------------------
        st.markdown("### 📋 Multi-Metric Comparison Table")
        comp_df = pd.DataFrame(res.get("comparison_table", []))
        if not comp_df.empty:
            st.dataframe(comp_df, use_container_width=True, hide_index=True)

        # ---------------------------------------------------------
        # AI Executive Synthesis Rationale (Groq openai/gpt-oss-120b)
        # ---------------------------------------------------------
        st.markdown("### 🧠 AI Investment Rationale & Risk Synthesis")
        st.markdown(
            "<div style='background: rgba(30, 41, 59, 0.75); border: 1px solid rgba(71, 85, 105, 0.5); border-left: 4px solid #38BDF8; padding: 18px 22px; border-radius: 8px; margin-bottom: 20px; color: #F1F5F9; font-size: 0.95rem; line-height: 1.65; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);'>"
            f"{res.get('synthesis_markdown')}"
            "</div>",
            unsafe_allow_html=True,
        )

        # ---------------------------------------------------------
        # Supporting Financial News (Feature 6.E)
        # ---------------------------------------------------------
        st.markdown("### 📰 Recent Verified Financial News")
        news_dict = res.get("news_by_symbol", {})
        has_news = False
        for sym, articles in news_dict.items():
            if articles:
                has_news = True
                st.markdown(f"**{sym} Headlines:**")
                n_cols = st.columns(min(3, len(articles)))
                for i, art in enumerate(articles[:3]):
                    with n_cols[i]:
                        st.markdown(f"""
                        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(71, 85, 105, 0.4); border-radius: 8px; padding: 12px; height: 160px; display: flex; flex-direction: column; justify-content: space-between;">
                            <div>
                                <span style="font-size: 0.75rem; color: #38BDF8; background: #1E293B; padding: 2px 6px; border-radius: 4px;">{art.get('source', 'Web')}</span>
                                <span style="font-size: 0.75rem; color: #94A3B8; margin-left: 6px;">{str(art.get('date', ''))[:10]}</span>
                                <div style="font-size: 0.85rem; font-weight: 600; color: #F1F5F9; margin-top: 6px; line-height: 1.3;">
                                    <a href="{art.get('link', '#')}" target="_blank" style="color: #F1F5F9; text-decoration: none;">{art.get('title')[:75]}...</a>
                                </div>
                            </div>
                            <div style="font-size: 0.75rem; color: #94A3B8;">{art.get('snippet', '')[:80]}...</div>
                        </div>
                        """, unsafe_allow_html=True)
        if not has_news:
            st.info("No recent news articles were found for the shortlisted candidates. Financial analysis proceeded with live market metrics.")

        # ---------------------------------------------------------
        # Tool Execution Transparency (Feature 7)
        # ---------------------------------------------------------
        st.markdown("---")
        with st.expander(f"🔍 Agent Activity & Tool Execution Records ({len(tool_logs)} tools verified)", expanded=False):
            st.markdown(
                "<p style='color: #94A3B8; font-size: 0.85rem; margin-bottom: 12px;'>"
                "StockPilot AI maintains complete transparency. Only tools that actually executed during this analysis appear below with verified results."
                "</p>",
                unsafe_allow_html=True,
            )

            if tool_logs:
                for idx, log in enumerate(tool_logs):
                    status = log.get("status", "success")
                    badge_color = "#10B981" if status == "success" else ("#F59E0B" if status == "warning" else "#EF4444")
                    st.markdown(f"""
                    <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(51, 65, 85, 0.6); border-radius: 6px; padding: 10px 14px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="color: #94A3B8; font-family: monospace; font-size: 0.8rem;">[{log.get('timestamp')}]</span>
                            <span style="color: #38BDF8; font-weight: 700; font-size: 0.9rem; margin-left: 8px;">{log.get('tool_name')}</span>
                            <span style="color: #CBD5E1; font-size: 0.85rem; margin-left: 10px;">— {log.get('task')}</span>
                            <div style="color: #94A3B8; font-size: 0.8rem; margin-top: 3px; margin-left: 70px;">{log.get('summary')}</div>
                        </div>
                        <div>
                            <span style="background: rgba(255, 255, 255, 0.05); border: 1px solid {badge_color}; color: {badge_color}; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;">
                                {status}
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.write("No execution logs recorded.")
