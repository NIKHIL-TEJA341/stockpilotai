"""Market Data Service for StockPilot AI.

Responsible for retrieving, normalizing, and caching historical stock data
from Yahoo Finance for Indian market equities.
"""

from datetime import datetime, timedelta
from typing import Any
import pandas as pd
import yfinance as yf


# In-memory session cache for stock data to avoid duplicate API calls
_MARKET_DATA_CACHE: dict[str, dict[str, Any]] = {}
CACHE_EXPIRY_MINUTES = 15


def normalize_symbol(symbol: str, exchange: str = "NSE") -> str:
    """Normalize Indian stock tickers with appropriate Yahoo Finance exchange suffix.

    e.g., 'RELIANCE' on 'NSE' -> 'RELIANCE.NS'
          'TCS.NS' -> 'TCS.NS'
          '500325' on 'BSE' -> '500325.BO'
    """
    cleaned = symbol.strip().upper()
    if cleaned.endswith(".NS") or cleaned.endswith(".BO"):
        return cleaned

    if exchange.upper() == "BSE":
        return f"{cleaned}.BO"
    return f"{cleaned}.NS"


def get_stock_data(
    symbol: str,
    period: str = "1y",
    exchange: str = "NSE",
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Retrieve historical daily price series and basic fundamentals for a stock ticker.

    Returns a clean dictionary with:
    - current_price
    - previous_close
    - currency
    - history (DataFrame or list of records)
    - company_info (name, sector, market_cap)
    - data_date
    - status ('success' or 'error')
    """
    ticker_sym = normalize_symbol(symbol, exchange)
    cache_key = f"{ticker_sym}_{period}"

    # Check cache
    if not force_refresh and cache_key in _MARKET_DATA_CACHE:
        cached = _MARKET_DATA_CACHE[cache_key]
        cache_time = cached.get("_cached_at")
        if cache_time and (datetime.now() - cache_time) < timedelta(minutes=CACHE_EXPIRY_MINUTES):
            return cached["data"]

    try:
        ticker = yf.Ticker(ticker_sym)
        # Fetch historical OHLCV data
        hist = ticker.history(period=period)

        if hist.empty or len(hist) < 2:
            return {
                "status": "error",
                "symbol": ticker_sym,
                "message": f"No historical price data found for {ticker_sym}. Check ticker or exchange.",
            }

        # Extract info
        info = {}
        try:
            info = ticker.info or {}
        except Exception:
            info = {}

        current_price = None
        if "regularMarketPrice" in info and info["regularMarketPrice"] is not None:
            current_price = float(info["regularMarketPrice"])
        elif "currentPrice" in info and info["currentPrice"] is not None:
            current_price = float(info["currentPrice"])
        else:
            current_price = float(hist["Close"].iloc[-1])

        # Historical series
        hist_records = []
        for date_idx, row in hist.iterrows():
            date_str = date_idx.strftime("%Y-%m-%d") if hasattr(date_idx, "strftime") else str(date_idx)[:10]
            hist_records.append({
                "date": date_str,
                "open": round(float(row.get("Open", 0)), 2),
                "high": round(float(row.get("High", 0)), 2),
                "low": round(float(row.get("Low", 0)), 2),
                "close": round(float(row.get("Close", 0)), 2),
                "volume": int(row.get("Volume", 0)),
            })

        closing_prices = [r["close"] for r in hist_records]
        latest_date = hist_records[-1]["date"]

        result = {
            "status": "success",
            "symbol": ticker_sym,
            "short_name": info.get("shortName") or info.get("longName") or ticker_sym,
            "currency": info.get("currency", "INR"),
            "current_price": round(current_price, 2),
            "latest_data_date": latest_date,
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "sector": info.get("sector", "General"),
            "summary": info.get("longBusinessSummary", ""),
            "history": hist_records,
            "closing_prices": closing_prices,
            "data_points": len(closing_prices),
        }

        # Store in cache
        _MARKET_DATA_CACHE[cache_key] = {
            "_cached_at": datetime.now(),
            "data": result,
        }

        return result

    except Exception as e:
        return {
            "status": "error",
            "symbol": ticker_sym,
            "message": f"Failed to fetch market data for {ticker_sym}: {str(e)}",
        }
