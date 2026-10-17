"""Standalone test runner for StockPilot AI financial calculations without external test runners."""

import sys
from pathlib import Path
import math

# Add root directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from tools.analysis_tools import (
    calculate_historical_returns,
    calculate_sma,
    calculate_rsi,
    calculate_volatility,
    calculate_affordability,
    calculate_basket_affordability,
)


def run_all_tests():
    print("=== Running StockPilot AI Financial Engine Tests ===")
    passed = 0
    failed = 0

    # 1. Historical Returns
    try:
        res = calculate_historical_returns([100.0, 105.0, 110.0, 120.0], "1Y")
        assert res["status"] == "success"
        assert res["return_pct"] == 20.0
        assert res["start_price"] == 100.0
        assert res["end_price"] == 120.0
        print("[PASS] Historical returns - positive growth")
        passed += 1
    except Exception as e:
        print(f"[FAIL] Historical returns: {e}")
        failed += 1

    # 2. Historical Returns - Negative
    try:
        res_down = calculate_historical_returns([100.0, 80.0], "6M")
        assert res_down["status"] == "success"
        assert res_down["return_pct"] == -20.0
        print("[PASS] Historical returns - negative drawdown")
        passed += 1
    except Exception as e:
        print(f"[FAIL] Historical returns drawdown: {e}")
        failed += 1

    # 3. SMA Calculation
    try:
        prices = [float(i) for i in range(1, 60)]
        res_sma = calculate_sma(prices, fast_period=20, slow_period=50)
        assert res_sma["status"] == "success"
        assert abs(res_sma["smas"]["SMA_20"] - 49.5) < 0.2
        assert abs(res_sma["smas"]["SMA_50"] - 34.5) < 0.2
        assert "Bullish" in res_sma["trend"]
        print("[PASS] Simple Moving Averages (20/50 SMA & Trend)")
        passed += 1
    except Exception as e:
        print(f"[FAIL] SMA calculation: {e}")
        failed += 1

    # 4. RSI Calculation - Overbought & Oversold
    try:
        upward = [100.0 + i * 2.0 for i in range(25)]
        res_rsi_up = calculate_rsi(upward, period=14)
        assert res_rsi_up["status"] == "success"
        assert res_rsi_up["rsi"] == 100.0
        assert "Overbought" in res_rsi_up["zone"]

        downward = [200.0 - i * 2.0 for i in range(25)]
        res_rsi_down = calculate_rsi(downward, period=14)
        assert res_rsi_down["status"] == "success"
        assert res_rsi_down["rsi"] == 0.0
        assert "Oversold" in res_rsi_down["zone"]
        print("[PASS] 14-period Wilder RSI calculation (Overbought / Oversold)")
        passed += 1
    except Exception as e:
        print(f"[FAIL] RSI calculation: {e}")
        failed += 1

    # 5. Volatility Calculation
    try:
        flat = [100.0] * 30
        res_vol = calculate_volatility(flat)
        assert res_vol["status"] == "success"
        assert res_vol["daily_volatility_pct"] == 0.0
        assert res_vol["annualized_volatility_pct"] == 0.0
        print("[PASS] Annualized & Daily Volatility calculation")
        passed += 1
    except Exception as e:
        print(f"[FAIL] Volatility calculation: {e}")
        failed += 1

    # 6. Affordability Calculation
    try:
        res_afford = calculate_affordability(budget=10000.0, share_price=2450.0, stock_symbol="RELIANCE.NS")
        assert res_afford["status"] == "success"
        assert res_afford["affordable_shares"] == 4
        assert res_afford["total_cost"] == 9800.0
        assert res_afford["remaining_budget"] == 200.0

        res_zero = calculate_affordability(budget=1000.0, share_price=2450.0, stock_symbol="RELIANCE.NS")
        assert res_zero["affordable_shares"] == 0
        assert res_zero["remaining_budget"] == 1000.0
        print("[PASS] Whole-share Affordability & Remaining Cash")
        passed += 1
    except Exception as e:
        print(f"[FAIL] Affordability calculation: {e}")
        failed += 1

    # 7. Basket Affordability
    try:
        allocations = [
            {"symbol": "TCS.NS", "share_price": 3500.0, "target_weight": 0.5},
            {"symbol": "INFY.NS", "share_price": 1500.0, "target_weight": 0.5},
        ]
        res_basket = calculate_basket_affordability(budget=10000.0, allocations=allocations)
        assert res_basket["status"] == "success"
        assert res_basket["total_invested"] <= 10000.0
        assert res_basket["cash_remaining"] >= 0.0
        assert len(res_basket["basket"]) == 2
        print("[PASS] Diversified Basket Whole-share allocation")
        passed += 1
    except Exception as e:
        print(f"[FAIL] Basket affordability: {e}")
        failed += 1

    print(f"\nSummary: {passed} passed, {failed} failed.")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
