"""Analysis history management view for StockPilot AI (Feature 9).

Persists and displays past investment screening sessions from SQLite,
allowing users to review previous parameters and results.
"""

from typing import Any
import streamlit as st
import pandas as pd
import json

from database.repository import get_analysis_history, get_analysis_by_id


def render_history() -> None:
    """Render the Analysis History page."""
    st.markdown("""
    <div style="margin-bottom: 12px;">
        <h1 style="font-size: 2rem; font-weight: 800; color: #FFFFFF; margin: 0 0 6px 0; display: flex; align-items: center; gap: 10px;">
            <span style="filter: drop-shadow(0 0 8px rgba(56, 189, 248, 0.4));">📜</span> Analysis History
        </h1>
        <p style="color: #CBD5E1; font-size: 0.95rem; margin: 0; line-height: 1.5;">
            Review previously executed investment screening runs, parameter configurations, and shortlisted candidate sets.
        </p>
    </div>
    """, unsafe_allow_html=True)

    records = get_analysis_history(limit=25)
    if not records:
        st.info("No prior analyses recorded. Run an analysis from the Dashboard to save your sessions automatically.")
        return

    # Table of past runs
    table_rows = []
    for r in records:
        syms = r.get("shortlisted_symbols", [])
        sym_str = ", ".join(syms) if isinstance(syms, list) else str(syms)
        table_rows.append({
            "Run ID": r["id"],
            "Timestamp": str(r.get("created_at", ""))[:19],
            "Budget (₹)": f"₹{r['budget']:,.2f}",
            "Horizon": r["duration"],
            "Risk Profile": r["risk_tolerance"],
            "Stock Preference": r["stock_preference"],
            "Strategy": r["investment_type"],
            "Shortlisted Tickers": sym_str,
        })

    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

    # Inspect specific past run
    st.markdown("### 🔎 Inspect Past Analysis Record")
    selected_id = st.selectbox(
        "Select Run ID to Inspect",
        options=[r["id"] for r in records],
        format_func=lambda rid: f"Run #{rid} — {next((r['created_at'] for r in records if r['id'] == rid), '')} (₹{next((r['budget'] for r in records if r['id'] == rid), 0):,.0f})",
    )

    if selected_id:
        record = get_analysis_by_id(selected_id)
        if record:
            st.markdown(f"#### Run #{record['id']} — Details")
            p_col1, p_col2, p_col3, p_col4 = st.columns(4)
            p_col1.metric("Budget", f"₹{record['budget']:,.2f}")
            p_col2.metric("Duration", record["duration"])
            p_col3.metric("Risk Profile", record["risk_tolerance"])
            p_col4.metric("Strategy", record["investment_type"])

            st.markdown("**Shortlisted Stocks:**")
            syms = record.get("shortlisted_symbols", [])
            st.write(syms)

            st.markdown("**Saved AI Synthesis Summary:**")
            st.markdown(
                f"<div style='background: rgba(30, 41, 59, 0.75); border: 1px solid rgba(71, 85, 105, 0.4); border-left: 4px solid #38BDF8; padding: 16px 20px; border-radius: 8px; color: #F1F5F9; font-size: 0.95rem; line-height: 1.6;'>"
                f"{record.get('summary_explanation') or 'No summary stored.'}"
                f"</div>",
                unsafe_allow_html=True,
            )

            # Option to load full payload back into dashboard
            full_data = record.get("full_payload_json", {})
            if full_data and st.button("🔄 Reopen this Analysis in Dashboard", key=f"reopen_{selected_id}", type="primary"):
                st.session_state["analysis_result"] = {
                    "status": "success",
                    "analysis_id": record["id"],
                    "summary": {
                        "budget": record["budget"],
                        "duration": record["duration"],
                        "risk_tolerance": record["risk_tolerance"],
                        "stock_preference": record["stock_preference"],
                        "investment_type": record["investment_type"],
                        "market": record.get("market_universe", "NSE"),
                        "candidates_analyzed": len(full_data.get("shortlisted", [])),
                        "shortlisted_count": len(full_data.get("shortlisted", [])),
                        "latest_data_date": full_data.get("latest_data_date", "Archived"),
                    },
                    "shortlisted": full_data.get("shortlisted", []),
                    "basket_allocation": full_data.get("basket_allocation"),
                    "comparison_table": full_data.get("comparison_table", []),
                    "news_by_symbol": {},
                    "synthesis_markdown": record.get("summary_explanation", ""),
                    "tool_logs": [],
                }
                st.session_state["current_page"] = "Dashboard"
                st.toast("Analysis reloaded into Dashboard!")
                st.rerun()
