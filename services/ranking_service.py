"""Documented Stock Ranking and Scoring Service for StockPilot AI.

Implements the multi-factor screening score defined in PRD Section 8.
All calculations are deterministic, explainable, and clearly labeled
as application-generated screening scores, not predictions of profit.
"""

from typing import Any


def calculate_screening_score(
    metrics: dict[str, Any],
    risk_tolerance: str = "Moderate",
    duration: str = "Medium term",
    budget: float = 10000.0,
) -> dict[str, Any]:
    """Calculate an explainable screening score (0 to 100) based on deterministic metrics.

    Components:
    1. Performance Score (0 - 30 pts): Historical returns over lookback period.
    2. Trend & Moving Average Score (0 - 25 pts): SMA alignment and price action.
    3. Momentum / RSI Score (0 - 20 pts): RSI health zone.
    4. Volatility & Risk Fit (0 - 15 pts): Historical volatility matched against user risk tolerance.
    5. Affordability & Liquidity Fit (0 - 10 pts): Ability to purchase whole shares within budget.
    """
    reasons: list[str] = []
    cautions: list[str] = []
    
    # -----------------------------------------------------------------
    # 1. Performance Score (Max 30)
    # -----------------------------------------------------------------
    ret = metrics.get("return_pct")
    perf_score = 15.0  # neutral starting point
    if ret is not None:
        if ret > 30.0:
            perf_score = 30.0
            reasons.append(f"Strong historical return of +{ret}% over analyzed period.")
        elif ret > 15.0:
            perf_score = 25.0
            reasons.append(f"Solid positive return of +{ret}%.")
        elif ret > 0.0:
            perf_score = 18.0
            reasons.append(f"Modest positive gain of +{ret}%.")
        elif ret > -15.0:
            perf_score = 10.0
            cautions.append(f"Recent negative return of {ret}%.")
        else:
            perf_score = 5.0
            cautions.append(f"Significant price drawdown of {ret}%.")
    else:
        perf_score = 10.0
        cautions.append("Historical return data incomplete.")

    # -----------------------------------------------------------------
    # 2. Trend & SMA Score (Max 25)
    # -----------------------------------------------------------------
    trend = str(metrics.get("trend", "")).lower()
    if "strong bullish" in trend:
        trend_score = 25.0
        reasons.append("Strong bullish moving average alignment (Price > SMA 20 > SMA 50).")
    elif "bullish" in trend or "above" in trend:
        trend_score = 20.0
        reasons.append("Trading above its short-term moving average.")
    elif "neutral" in trend or "consolidating" in trend:
        trend_score = 14.0
        reasons.append("Moving averages indicate price consolidation.")
    elif "strong bearish" in trend:
        trend_score = 5.0
        cautions.append("Strong bearish trend (Price < SMA 20 < SMA 50).")
    elif "bearish" in trend or "below" in trend:
        trend_score = 8.0
        cautions.append("Trading below its moving averages.")
    else:
        trend_score = 10.0

    # -----------------------------------------------------------------
    # 3. Momentum & RSI Score (Max 20)
    # -----------------------------------------------------------------
    rsi = metrics.get("rsi")
    if rsi is not None:
        if 40.0 <= rsi <= 62.0:
            rsi_score = 20.0
            reasons.append(f"Balanced RSI momentum at {rsi} (sustainable accumulation zone).")
        elif 62.0 < rsi <= 70.0:
            rsi_score = 17.0
            reasons.append(f"Strong momentum (RSI {rsi}).")
        elif rsi > 70.0:
            rsi_score = 10.0
            cautions.append(f"RSI at {rsi} indicates overbought conditions (elevated consolidation risk).")
        elif 30.0 <= rsi < 40.0:
            rsi_score = 14.0
            reasons.append(f"RSI at {rsi} approaching oversold range.")
        else:  # rsi < 30
            rsi_score = 12.0
            cautions.append(f"RSI at {rsi} indicates deeply oversold levels.")
    else:
        rsi_score = 10.0
        cautions.append("RSI technical indicator unavailable.")

    # -----------------------------------------------------------------
    # 4. Volatility & Risk Fit (Max 15)
    # -----------------------------------------------------------------
    ann_vol = metrics.get("annualized_volatility_pct")
    risk_low = risk_tolerance.lower()
    
    if ann_vol is not None:
        if "low" in risk_low or "conservative" in risk_low:
            if ann_vol < 20.0:
                vol_score = 15.0
                reasons.append(f"Low annualized volatility ({ann_vol}%) aligns with Conservative risk preference.")
            elif ann_vol <= 30.0:
                vol_score = 10.0
                reasons.append(f"Moderate volatility ({ann_vol}%).")
            else:
                vol_score = 4.0
                cautions.append(f"High annualized volatility ({ann_vol}%) exceeds preferred low-risk tolerance.")
        elif "high" in risk_low or "aggressive" in risk_low:
            if ann_vol >= 25.0:
                vol_score = 15.0
                reasons.append(f"Higher volatility ({ann_vol}%) fits aggressive capital growth profile.")
            else:
                vol_score = 11.0
                reasons.append(f"Annualized volatility is {ann_vol}%.")
        else:  # Moderate
            if 18.0 <= ann_vol <= 32.0:
                vol_score = 15.0
                reasons.append(f"Annualized volatility ({ann_vol}%) is well within typical market range.")
            elif ann_vol < 18.0:
                vol_score = 13.0
                reasons.append(f"Stable price action with low volatility ({ann_vol}%).")
            else:
                vol_score = 8.0
                cautions.append(f"Higher volatility ({ann_vol}%) may lead to larger swings.")
    else:
        vol_score = 8.0

    # -----------------------------------------------------------------
    # 5. Affordability Fit (Max 10)
    # -----------------------------------------------------------------
    price = metrics.get("current_price", 0.0)
    affordable_shares = metrics.get("affordable_shares", 0)
    if price > 0 and budget > 0:
        if affordable_shares >= 5:
            afford_score = 10.0
            reasons.append(f"High affordability: Can purchase {affordable_shares} whole shares.")
        elif affordable_shares >= 1:
            afford_score = 8.0
            reasons.append(f"Affordable: Can purchase {affordable_shares} whole share(s) (₹{price:,.2f}/share).")
        else:
            afford_score = 2.0
            cautions.append(f"Single share price (₹{price:,.2f}) exceeds total budget (₹{budget:,.2f}).")
    else:
        afford_score = 5.0

    total_score = round(perf_score + trend_score + rsi_score + vol_score + afford_score, 1)
    total_score = max(0.0, min(100.0, total_score))

    return {
        "screening_score": total_score,
        "score_breakdown": {
            "performance": round(perf_score, 1),
            "trend": round(trend_score, 1),
            "momentum_rsi": round(rsi_score, 1),
            "volatility_fit": round(vol_score, 1),
            "affordability_fit": round(afford_score, 1),
        },
        "key_reasons": reasons,
        "key_cautions": cautions,
        "disclaimer": "Screening score is a deterministic rule-based ranking metric for candidate comparison and not an endorsement or return prediction.",
    }


def rank_shortlisted_stocks(
    analyzed_stocks: list[dict[str, Any]],
    top_n: int = 3,
) -> list[dict[str, Any]]:
    """Rank analyzed stocks by total screening score and return top N shortlisted candidates."""
    # Sort descending by screening score
    ranked = sorted(
        analyzed_stocks,
        key=lambda s: s.get("screening_score", 0.0),
        reverse=True,
    )
    return ranked[:top_n]
