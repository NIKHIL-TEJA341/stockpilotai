"""Unit tests for deterministic financial calculations in StockPilot AI."""

import pytest
import pandas as pd
from tools.analysis_tools import (
    calculate_historical_returns,
    calculate_sma,
    calculate_rsi,
    calculate_volatility,
    calculate_affordability,
    calculate_basket_affordability,
)


def test_calculate_historical_returns():
    # Test positive return
    prices = [100.0, 105.0, 110.0, 120.0]
    res = calculate_historical_returns(prices, "1Y")
    assert res["status"] == "success"
    assert res["return_pct"] == 20.0
    assert res["start_price"] == 100.0
    assert res["end_price"] == 120.0

    # Test negative return
    prices_down = [100.0, 80.0]
    res_down = calculate_historical_returns(prices_down, "6M")
    assert res_down["status"] == "success"
    assert res_down["return_pct"] == -20.0

    # Test invalid / insufficient data
    res_empty = calculate_historical_returns([100.0])
    assert res_empty["status"] == "error"
    assert res_empty["return_pct"] is None


def test_calculate_sma():
    prices = [float(i) for i in range(1, 60)]  # 1 to 59
    res = calculate_sma(prices, fast_period=20, slow_period=50)
    assert res["status"] == "success"
    assert res["smas"]["SMA_20"] == pytest.approx(49.5, 0.1)
    assert res["smas"]["SMA_50"] == pytest.approx(34.5, 0.1)
    assert "Bullish" in res["trend"]

    # Test insufficient points for slow SMA
    short_prices = [10.0, 12.0, 14.0]
    res_short = calculate_sma(short_prices, fast_period=20, slow_period=50)
    assert res_short["smas"]["SMA_20"] is None
    assert res_short["smas"]["SMA_50"] is None


def test_calculate_rsi():
    # 20 steady upward prices -> high RSI
    upward_prices = [100.0 + i * 2.0 for i in range(25)]
    res_up = calculate_rsi(upward_prices, period=14)
    assert res_up["status"] == "success"
    assert res_up["rsi"] == 100.0
    assert "Overbought" in res_up["zone"]

    # 20 steady downward prices -> low RSI
    downward_prices = [200.0 - i * 2.0 for i in range(25)]
    res_down = calculate_rsi(downward_prices, period=14)
    assert res_down["status"] == "success"
    assert res_down["rsi"] == 0.0
    assert "Oversold" in res_down["zone"]

    # Test insufficient data points (< 15)
    res_insuf = calculate_rsi([100.0, 101.0, 102.0], period=14)
    assert res_insuf["status"] == "error"
    assert res_insuf["rsi"] is None


def test_calculate_volatility():
    # Flat price series -> zero volatility
    flat_prices = [100.0] * 30
    res_flat = calculate_volatility(flat_prices)
    assert res_flat["status"] == "success"
    assert res_flat["daily_volatility_pct"] == 0.0
    assert res_flat["annualized_volatility_pct"] == 0.0

    # Insufficient data points
    res_short = calculate_volatility([100.0, 105.0])
    assert res_short["status"] == "error"


def test_calculate_affordability():
    # Valid budget
    res = calculate_affordability(budget=10000.0, share_price=2450.0, stock_symbol="RELIANCE.NS")
    assert res["status"] == "success"
    assert res["affordable_shares"] == 4  # 4 * 2450 = 9800
    assert res["total_cost"] == 9800.0
    assert res["remaining_budget"] == 200.0

    # Budget lower than share price
    res_low = calculate_affordability(budget=1000.0, share_price=2450.0, stock_symbol="RELIANCE.NS")
    assert res_low["status"] == "success"
    assert res_low["affordable_shares"] == 0
    assert res_low["total_cost"] == 0.0
    assert res_low["remaining_budget"] == 1000.0

    # Invalid zero budget
    res_zero = calculate_affordability(budget=0.0, share_price=500.0)
    assert res_zero["status"] == "error"
    assert res_zero["affordable_shares"] == 0


def test_calculate_basket_affordability():
    allocations = [
        {"symbol": "TCS.NS", "share_price": 3500.0, "target_weight": 0.5},
        {"symbol": "INFY.NS", "share_price": 1500.0, "target_weight": 0.5},
    ]
    res = calculate_basket_affordability(budget=10000.0, allocations=allocations)
    assert res["status"] == "success"
    assert res["total_invested"] <= 10000.0
    assert res["cash_remaining"] >= 0.0
    assert len(res["basket"]) == 2
