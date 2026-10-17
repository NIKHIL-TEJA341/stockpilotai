"""Deterministic financial calculation tools for StockPilot AI.

All mathematical formulas follow standard financial practices as specified
in the StockPilot AI PRD (Section Feature 4).
"""

from typing import Any
import math
import numpy as np
import pandas as pd


def calculate_historical_returns(
    closing_prices: list[float] | pd.Series,
    period_name: str = "selected period",
) -> dict[str, Any]:
    """Calculate historical price returns over a period.

    Formula: Return (%) = ((Ending Price - Starting Price) / Starting Price) * 100
    """
    if closing_prices is None or len(closing_prices) < 2:
        return {
            "status": "error",
            "message": "At least 2 price points required to calculate return.",
            "period": period_name,
            "return_pct": None,
        }

    prices = list(closing_prices)
    start_price = float(prices[0])
    end_price = float(prices[-1])

    if start_price <= 0:
        return {
            "status": "error",
            "message": "Starting price must be positive.",
            "period": period_name,
            "return_pct": None,
        }

    return_pct = round(((end_price - start_price) / start_price) * 100, 2)
    abs_change = round(end_price - start_price, 2)

    return {
        "status": "success",
        "period": period_name,
        "start_price": round(start_price, 2),
        "end_price": round(end_price, 2),
        "absolute_change": abs_change,
        "return_pct": return_pct,
        "disclaimer": "Historical returns are for information only and do not guarantee future performance.",
    }


def calculate_sma(
    closing_prices: list[float] | pd.Series,
    fast_period: int = 20,
    slow_period: int = 50,
) -> dict[str, Any]:
    """Calculate Simple Moving Averages (fast and slow periods).

    Formula: SMA(n) = Sum of latest n closing prices / n
    """
    if closing_prices is None:
        return {"status": "error", "message": "No price data provided."}

    series = pd.Series(closing_prices).dropna()
    total_points = len(series)

    results: dict[str, Any] = {
        "status": "success",
        "total_data_points": total_points,
        "current_price": round(float(series.iloc[-1]), 2) if total_points > 0 else None,
        "smas": {},
        "trend": "insufficient_data",
        "disclaimer": "Moving averages reflect past price patterns and do not predict future direction.",
    }

    if total_points >= fast_period:
        fast_sma = float(series.iloc[-fast_period:].mean())
        results["smas"][f"SMA_{fast_period}"] = round(fast_sma, 2)
    else:
        results["smas"][f"SMA_{fast_period}"] = None

    if total_points >= slow_period:
        slow_sma = float(series.iloc[-slow_period:].mean())
        results["smas"][f"SMA_{slow_period}"] = round(slow_sma, 2)
    else:
        results["smas"][f"SMA_{slow_period}"] = None

    # Determine trend if both SMAs and current price are available
    curr = results["current_price"]
    fast = results["smas"].get(f"SMA_{fast_period}")
    slow = results["smas"].get(f"SMA_{slow_period}")

    if curr is not None and fast is not None and slow is not None:
        if curr > fast > slow:
            results["trend"] = "Strong Bullish (Price > Fast SMA > Slow SMA)"
        elif curr > fast:
            results["trend"] = "Moderate Bullish (Price > Fast SMA)"
        elif curr < fast < slow:
            results["trend"] = "Strong Bearish (Price < Fast SMA < Slow SMA)"
        elif curr < fast:
            results["trend"] = "Moderate Bearish (Price < Fast SMA)"
        else:
            results["trend"] = "Neutral / Consolidating"
    elif curr is not None and fast is not None:
        results["trend"] = "Above Fast SMA" if curr > fast else "Below Fast SMA"

    return results


def calculate_rsi(
    closing_prices: list[float] | pd.Series,
    period: int = 14,
) -> dict[str, Any]:
    """Calculate Relative Strength Index (RSI) using Wilder's smoothing technique.

    Formula: RSI = 100 - (100 / (1 + RS))
    Where RS = Average Gain / Average Loss over the period.
    """
    if closing_prices is None:
        return {"status": "error", "message": "No price data provided."}

    series = pd.Series(closing_prices).dropna().astype(float)
    if len(series) < period + 1:
        return {
            "status": "error",
            "message": f"Insufficient data for RSI-{period}. Required: {period + 1}, Available: {len(series)}.",
            "rsi": None,
            "period": period,
        }

    deltas = series.diff().dropna()
    gains = deltas.clip(lower=0)
    losses = -deltas.clip(upper=0)

    # First average: simple average of first 'period' values
    avg_gain = gains.iloc[:period].mean()
    avg_loss = losses.iloc[:period].mean()

    # Wilder's smoothing for subsequent values
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains.iloc[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses.iloc[i]) / period

    if avg_loss == 0:
        rsi_val = 100.0
    elif avg_gain == 0:
        rsi_val = 0.0
    else:
        rs = avg_gain / avg_loss
        rsi_val = 100.0 - (100.0 / (1.0 + rs))

    rsi_val = round(float(rsi_val), 2)

    # Qualitative interpretation
    if rsi_val >= 70:
        zone = "Overbought (Potential consolidation/pullback risk)"
    elif rsi_val <= 30:
        zone = "Oversold (Potential rebound watch)"
    else:
        zone = "Neutral Range (30-70)"

    return {
        "status": "success",
        "period": period,
        "rsi": rsi_val,
        "zone": zone,
        "disclaimer": "RSI is a momentum oscillator. Overbought/oversold levels are not standalone buy/sell signals.",
    }


def calculate_volatility(
    closing_prices: list[float] | pd.Series,
    trading_days: int = 252,
) -> dict[str, Any]:
    """Calculate historical daily and annualized volatility from daily returns.

    Daily Volatility = StdDev(Daily Returns)
    Annualized Volatility = Daily Volatility * sqrt(trading_days)
    """
    if closing_prices is None:
        return {"status": "error", "message": "No price data provided."}

    series = pd.Series(closing_prices).dropna().astype(float)
    if len(series) < 10:
        return {
            "status": "error",
            "message": f"Insufficient data for volatility calculation. Available: {len(series)}, Required: at least 10.",
            "daily_volatility_pct": None,
            "annualized_volatility_pct": None,
        }

    daily_returns = series.pct_change().dropna()
    daily_vol = float(daily_returns.std())
    annualized_vol = float(daily_vol * math.sqrt(trading_days))

    daily_vol_pct = round(daily_vol * 100, 2)
    ann_vol_pct = round(annualized_vol * 100, 2)

    # Risk level classification based on Indian market benchmark ranges
    if ann_vol_pct < 18.0:
        risk_category = "Low Volatility (Relatively stable price action)"
    elif ann_vol_pct <= 32.0:
        risk_category = "Moderate Volatility (Typical broad-market range)"
    else:
        risk_category = "High Volatility (Elevated price fluctuations)"

    return {
        "status": "success",
        "lookback_trading_days": len(daily_returns),
        "daily_volatility_pct": daily_vol_pct,
        "annualized_volatility_pct": ann_vol_pct,
        "risk_category": risk_category,
        "disclaimer": "Volatility measures historical price variability and is not a comprehensive measure of total investment risk.",
    }


def calculate_affordability(
    budget: float,
    share_price: float,
    stock_symbol: str = "",
) -> dict[str, Any]:
    """Calculate the number of whole shares affordable within the user's budget.

    Formula: Affordable Shares = Floor(Budget / Share Price)
    """
    if budget <= 0:
        return {
            "status": "error",
            "message": "Budget must be greater than zero.",
            "affordable_shares": 0,
            "total_cost": 0.0,
            "remaining_budget": 0.0,
        }

    if share_price <= 0:
        return {
            "status": "error",
            "message": "Share price must be greater than zero.",
            "affordable_shares": 0,
            "total_cost": 0.0,
            "remaining_budget": round(budget, 2),
        }

    affordable_shares = int(math.floor(budget / share_price))
    total_cost = round(affordable_shares * share_price, 2)
    remaining_budget = round(budget - total_cost, 2)

    return {
        "status": "success",
        "symbol": stock_symbol,
        "budget": round(budget, 2),
        "share_price": round(share_price, 2),
        "affordable_shares": affordable_shares,
        "total_cost": total_cost,
        "remaining_budget": remaining_budget,
        "utilization_pct": round((total_cost / budget) * 100, 2) if budget > 0 else 0.0,
        "note": "Excludes brokerage fees, STT, exchange transaction charges, GST, and SEBI turnover charges.",
    }


def calculate_basket_affordability(
    budget: float,
    allocations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Calculate whole-share quantities for a diversified basket of stocks.

    Each item in allocations should have:
    - 'symbol': str
    - 'share_price': float
    - 'target_weight': float (0.0 to 1.0)
    """
    if budget <= 0:
        return {"status": "error", "message": "Budget must be positive."}

    if not allocations:
        return {"status": "error", "message": "No stock allocations provided."}

    total_weight = sum(item.get("target_weight", 0.0) for item in allocations)
    if total_weight <= 0:
        total_weight = 1.0

    basket_results = []
    total_spent = 0.0

    for item in allocations:
        symbol = item.get("symbol", "UNKNOWN")
        price = float(item.get("share_price", 0.0))
        weight = float(item.get("target_weight", 1.0 / len(allocations)))
        norm_weight = weight / total_weight

        allocated_budget = budget * norm_weight
        shares = int(math.floor(allocated_budget / price)) if price > 0 else 0
        spent = round(shares * price, 2)
        total_spent += spent

        basket_results.append({
            "symbol": symbol,
            "share_price": round(price, 2),
            "target_weight_pct": round(norm_weight * 100, 1),
            "allocated_budget": round(allocated_budget, 2),
            "affordable_shares": shares,
            "cost": spent,
        })

    remaining_cash = round(budget - total_spent, 2)

    return {
        "status": "success",
        "total_budget": round(budget, 2),
        "total_invested": round(total_spent, 2),
        "cash_remaining": remaining_cash,
        "basket": basket_results,
        "note": "Calculated using whole shares. Taxes, brokerage, and statutory charges are excluded.",
    }
