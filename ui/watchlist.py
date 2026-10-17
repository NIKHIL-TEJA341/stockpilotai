"""Watchlist management view for StockPilot AI (Feature 9).

Persists user-saved stocks in SQLite and displays refreshed prices,
fundamentals, and quick analysis access.
"""

import streamlit as st
import pandas as pd

from database.repository import get_watchlist, remove_from_watchlist, add_to_watchlist
from services.market_data_service import get_stock_data, normalize_symbol
from services.stock_screener import load_stock_universe


def render_watchlist() -> None:
    """Render the Watchlist view."""
    st.markdown("""
    <div style="margin-bottom: 12px;">
        <h1 style="font-size: 2rem; font-weight: 800; color: #FFFFFF; margin: 0 0 6px 0; display: flex; align-items: center; gap: 10px;">
            <span style="filter: drop-shadow(0 0 8px rgba(56, 189, 248, 0.4));">⭐</span> My Stock Watchlist
        </h1>
        <p style="color: #CBD5E1; font-size: 0.95rem; margin: 0; line-height: 1.5;">
            Track saved Indian equity candidates with live price updates and historical metrics.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 1. Quick Add Section
    with st.expander("➕ Add Stock to Watchlist", expanded=False):
        universe = load_stock_universe()
        sym_options = [s["symbol"] for s in universe]
        sym_map = {s["symbol"]: f"{s['symbol']} — {s['name']}" for s in universe}

        w_col1, w_col2 = st.columns([3, 1])
        with w_col1:
            picked_sym = st.selectbox("Select from Universe", options=sym_options, format_func=lambda s: sym_map.get(s, s))
        with w_col2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("Add Symbol", use_container_width=True, type="primary"):
                # Find details
                found = next((s for s in universe if s["symbol"] == picked_sym), None)
                if found:
                    add_to_watchlist(found["symbol"], found["name"], found.get("sector", "General"), found.get("market_cap_category", "Large-cap"))
                    st.toast(f"Added {picked_sym} to watchlist!")
                    st.rerun()

    # 2. Retrieve watchlist
    watchlist_items = get_watchlist()
    if not watchlist_items:
        st.info("Your watchlist is currently empty. Add stocks from the Investment Dashboard or the selector above!")
        return

    st.markdown(f"**Total Tracked Equities ({len(watchlist_items)}):**")

    # Fetch live quotes for watchlist items
    rows = []
    for item in watchlist_items:
        sym = item["symbol"]
        market_res = get_stock_data(sym, period="1mo")
        curr_price = market_res.get("current_price") if market_res.get("status") == "success" else None
        pe = market_res.get("pe_ratio")
        high52 = market_res.get("fifty_two_week_high")
        low52 = market_res.get("fifty_two_week_low")

        rows.append({
            "Symbol": sym,
            "Company": item["name"],
            "Sector": item.get("sector", "General"),
            "Market Cap": item.get("market_cap_category", "Large-cap"),
            "Price (₹)": f"₹{curr_price:,.2f}" if curr_price else "N/A",
            "52W High (₹)": f"₹{high52:,.2f}" if high52 else "N/A",
            "52W Low (₹)": f"₹{low52:,.2f}" if low52 else "N/A",
            "P/E Ratio": f"{pe:.1f}" if pe else "N/A",
            "Added Date": str(item.get("added_at", ""))[:10],
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # 3. Actions per item
    st.markdown("##### Manage Watchlist Items")
    action_cols = st.columns(min(4, len(watchlist_items)))
    for idx, item in enumerate(watchlist_items):
        sym = item["symbol"]
        col_idx = idx % len(action_cols)
        with action_cols[col_idx]:
            if st.button(f"🗑️ Remove {sym}", key=f"del_{sym}", use_container_width=True):
                remove_from_watchlist(sym)
                st.toast(f"Removed {sym} from watchlist.")
                st.rerun()
