"""Stock screening service for StockPilot AI.

Filters candidate stocks from the defined Indian equity universe
based on the user's investment budget, risk tolerance, market cap preference,
and investment duration.
"""

from pathlib import Path
from typing import Any
import pandas as pd
from config.settings import settings


def load_stock_universe() -> list[dict[str, Any]]:
    """Load the curated Indian equity universe from CSV."""
    csv_path = settings.STOCK_UNIVERSE_PATH
    if not csv_path.exists():
        # Fallback minimal universe if CSV not found
        return [
            {"symbol": "RELIANCE.NS", "name": "Reliance Industries Ltd", "sector": "Energy & Conglomerate", "market_cap_category": "Large-cap", "exchange": "NSE"},
            {"symbol": "TCS.NS", "name": "Tata Consultancy Services Ltd", "sector": "Information Technology", "market_cap_category": "Large-cap", "exchange": "NSE"},
            {"symbol": "HDFCBANK.NS", "name": "HDFC Bank Ltd", "sector": "Financial Services", "market_cap_category": "Large-cap", "exchange": "NSE"},
            {"symbol": "INFY.NS", "name": "Infosys Ltd", "sector": "Information Technology", "market_cap_category": "Large-cap", "exchange": "NSE"},
            {"symbol": "ITC.NS", "name": "ITC Ltd", "sector": "Consumer Goods", "market_cap_category": "Large-cap", "exchange": "NSE"},
        ]
    
    df = pd.read_csv(csv_path)
    return df.to_dict(orient="records")


def screen_candidates(
    stock_preference: str = "No preference",
    risk_tolerance: str = "Moderate",
    investment_type: str = "Individual stock candidates",
    market: str = "NSE",
    max_candidates: int = 8,
) -> list[dict[str, Any]]:
    """Screen candidate stocks matching user investment preferences.

    Filters by:
    - Market Cap Category (Large-cap, Mid-cap, Small-cap)
    - Risk Profile alignment
    - Exchange (NSE / BSE)
    """
    universe = load_stock_universe()
    
    # 1. Filter by exchange
    filtered = [s for s in universe if s.get("exchange", "NSE").upper() == market.upper()]
    if not filtered:
        filtered = universe

    # 2. Filter by stock preference (market cap)
    pref_lower = stock_preference.lower()
    if "large" in pref_lower:
        matched = [s for s in filtered if "large" in s.get("market_cap_category", "").lower()]
    elif "mid" in pref_lower:
        matched = [s for s in filtered if "mid" in s.get("market_cap_category", "").lower()]
    elif "small" in pref_lower:
        matched = [s for s in filtered if "small" in s.get("market_cap_category", "").lower()]
    else:
        # No preference: filter based on risk tolerance
        risk_lower = risk_tolerance.lower()
        if "low" in risk_lower or "conservative" in risk_lower:
            # Low risk: favor Large-cap
            large_caps = [s for s in filtered if "large" in s.get("market_cap_category", "").lower()]
            matched = large_caps
        elif "high" in risk_lower or "aggressive" in risk_lower:
            # High risk: blend Mid-caps and Small-caps with growth large caps
            mid_small = [s for s in filtered if any(c in s.get("market_cap_category", "").lower() for c in ["mid", "small"])]
            matched = mid_small if len(mid_small) >= 4 else filtered
        else:
            # Moderate: broad blend across market caps
            matched = filtered

    if not matched:
        matched = filtered

    # 3. If diversified basket, ensure sector diversity
    if "basket" in investment_type.lower():
        seen_sectors = set()
        diverse_pool = []
        for stock in matched:
            sector = stock.get("sector", "Other")
            if sector not in seen_sectors:
                diverse_pool.append(stock)
                seen_sectors.add(sector)
            if len(diverse_pool) >= max_candidates:
                break
        
        # If pool too small, backfill from remaining
        if len(diverse_pool) < max_candidates:
            for stock in matched:
                if stock not in diverse_pool:
                    diverse_pool.append(stock)
                if len(diverse_pool) >= max_candidates:
                    break
        return diverse_pool

    # For individual candidates, return top matching pool up to max_candidates
    return matched[:max_candidates]
