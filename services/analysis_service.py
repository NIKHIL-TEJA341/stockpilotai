"""End-to-End Analysis Orchestration Service for StockPilot AI.

Coordinates screening, market data retrieval, deterministic mathematical
tools, news search, Agno Groq GPT-OSS 120B synthesis, and database persistence.
"""

from datetime import datetime
from typing import Any
import pandas as pd

from config.settings import settings
from services.stock_screener import screen_candidates
from services.market_data_service import get_stock_data, normalize_symbol
from services.ranking_service import calculate_screening_score, rank_shortlisted_stocks
from tools.news_tools import search_stock_news
from tools.analysis_tools import (
    calculate_historical_returns,
    calculate_sma,
    calculate_rsi,
    calculate_volatility,
    calculate_affordability,
    calculate_basket_affordability,
)
from agents.stock_agent import StockPilotAgent
from database.repository import save_analysis


def run_full_investment_analysis(
    budget: float,
    duration: str = "Medium term",
    risk_tolerance: str = "Moderate",
    stock_preference: str = "No preference",
    investment_type: str = "Individual stock candidates",
    market: str = "NSE",
) -> dict[str, Any]:
    """Execute the complete StockPilot AI investment analysis pipeline."""
    # 1. Input Validation
    if budget <= 0:
        return {
            "status": "error",
            "message": "Investment budget must be greater than zero (₹).",
        }

    agent = StockPilotAgent()
    
    # 2. Map Duration to Yahoo Finance historical period
    period_map = {
        "Short term": "6mo",
        "Medium term": "1y",
        "Long term": "2y",
        "Very long term": "5y",
    }
    history_period = period_map.get(duration, "1y")

    # 3. Screen initial candidate pool from universe
    candidates_pool = screen_candidates(
        stock_preference=stock_preference,
        risk_tolerance=risk_tolerance,
        investment_type=investment_type,
        market=market,
        max_candidates=7,
    )

    agent.log_tool_activity(
        tool_name="StockScreener",
        task_description="Candidate Universe Filtering",
        status="success",
        summary=f"Filtered {len(candidates_pool)} candidate stocks matching '{stock_preference}' and '{risk_tolerance}' risk.",
        details={"pool": [s["symbol"] for s in candidates_pool]},
    )

    # 4. Fetch Market Data & Run Deterministic Financial Tools for each candidate
    analyzed_candidates: list[dict[str, Any]] = []

    for item in candidates_pool:
        raw_sym = item["symbol"]
        norm_sym = normalize_symbol(raw_sym, market)

        # Retrieve market data
        market_res = get_stock_data(norm_sym, period=history_period, exchange=market)
        if market_res.get("status") != "success":
            agent.log_tool_activity(
                tool_name="YFinanceTools",
                task_description=f"Market data retrieval for {norm_sym}",
                status="failed",
                summary=f"Could not retrieve historical data for {norm_sym}",
                error=market_res.get("message"),
            )
            continue

        agent.log_tool_activity(
            tool_name="YFinanceTools",
            task_description=f"Historical price data retrieval for {norm_sym}",
            status="success",
            summary=f"Retrieved {market_res['data_points']} trading days of price history (Period: {history_period})",
        )

        closing_prices = market_res["closing_prices"]
        current_price = market_res["current_price"]

        # Run Deterministic Tools
        # Tool A: Historical Returns
        ret_res = calculate_historical_returns(closing_prices, period_name=duration)
        agent.log_tool_activity(
            tool_name="calculate_historical_returns",
            task_description=f"Return calculation for {norm_sym}",
            status="success",
            summary=f"Return: {ret_res.get('return_pct')}% (Change: ₹{ret_res.get('absolute_change')})",
        )

        # Tool B: Moving Averages
        sma_res = calculate_sma(closing_prices, fast_period=20, slow_period=50)
        agent.log_tool_activity(
            tool_name="calculate_sma",
            task_description=f"Moving average trend for {norm_sym}",
            status="success",
            summary=f"Trend: {sma_res.get('trend')} | SMA20: ₹{sma_res['smas'].get('SMA_20')} | SMA50: ₹{sma_res['smas'].get('SMA_50')}",
        )

        # Tool C: RSI
        rsi_res = calculate_rsi(closing_prices, period=14)
        agent.log_tool_activity(
            tool_name="calculate_rsi",
            task_description=f"14-period RSI for {norm_sym}",
            status="success",
            summary=f"RSI: {rsi_res.get('rsi')} ({rsi_res.get('zone')})",
        )

        # Tool D: Volatility
        vol_res = calculate_volatility(closing_prices, trading_days=252)
        agent.log_tool_activity(
            tool_name="calculate_volatility",
            task_description=f"Annualized volatility for {norm_sym}",
            status="success",
            summary=f"Annualized Volatility: {vol_res.get('annualized_volatility_pct')}% ({vol_res.get('risk_category')})",
        )

        # Tool E: Affordability
        afford_res = calculate_affordability(budget=budget, share_price=current_price, stock_symbol=norm_sym)
        agent.log_tool_activity(
            tool_name="calculate_affordability",
            task_description=f"Whole-share budget affordability for {norm_sym}",
            status="success",
            summary=f"Affordable Shares: {afford_res.get('affordable_shares')} (Total Cost: ₹{afford_res.get('total_cost'):,.2f}, Remaining: ₹{afford_res.get('remaining_budget'):,.2f})",
        )

        # Score and rank candidate
        metric_bundle = {
            "current_price": current_price,
            "return_pct": ret_res.get("return_pct"),
            "trend": sma_res.get("trend"),
            "rsi": rsi_res.get("rsi"),
            "annualized_volatility_pct": vol_res.get("annualized_volatility_pct"),
            "affordable_shares": afford_res.get("affordable_shares"),
        }

        scoring = calculate_screening_score(
            metrics=metric_bundle,
            risk_tolerance=risk_tolerance,
            duration=duration,
            budget=budget,
        )

        analyzed_candidates.append({
            "symbol": norm_sym,
            "short_name": market_res.get("short_name", norm_sym),
            "sector": item.get("sector", market_res.get("sector", "General")),
            "market_cap_category": item.get("market_cap_category", "Large-cap"),
            "market_cap": market_res.get("market_cap"),
            "currency": market_res.get("currency", "INR"),
            "current_price": current_price,
            "latest_data_date": market_res.get("latest_data_date"),
            "return_pct": ret_res.get("return_pct"),
            "absolute_change": ret_res.get("absolute_change"),
            "trend": sma_res.get("trend"),
            "smas": sma_res.get("smas"),
            "rsi": rsi_res.get("rsi"),
            "rsi_zone": rsi_res.get("zone"),
            "annualized_volatility_pct": vol_res.get("annualized_volatility_pct"),
            "volatility_category": vol_res.get("risk_category"),
            "affordable_shares": afford_res.get("affordable_shares"),
            "total_cost": afford_res.get("total_cost"),
            "remaining_budget": afford_res.get("remaining_budget"),
            "history": market_res.get("history", []),
            "screening_score": scoring.get("screening_score"),
            "score_breakdown": scoring.get("score_breakdown"),
            "key_reasons": scoring.get("key_reasons"),
            "key_cautions": scoring.get("key_cautions"),
        })

    if not analyzed_candidates:
        return {
            "status": "error",
            "message": "Market data could not be retrieved for any candidate stocks. Please check network connectivity or symbol specifications.",
            "tool_logs": agent.execution_logs,
        }

    # 5. Shortlist top candidates (Top 3 for individual, Top 4 for basket)
    top_count = 4 if "basket" in investment_type.lower() else 3
    shortlisted = rank_shortlisted_stocks(analyzed_candidates, top_n=top_count)

    # 6. Calculate Diversified Basket Allocation if requested
    basket_allocation = None
    if "basket" in investment_type.lower() and shortlisted:
        alloc_inputs = [
            {"symbol": s["symbol"], "share_price": s["current_price"], "target_weight": 1.0 / len(shortlisted)}
            for s in shortlisted
        ]
        basket_res = calculate_basket_affordability(budget=budget, allocations=alloc_inputs)
        basket_allocation = basket_res
        agent.log_tool_activity(
            tool_name="calculate_basket_affordability",
            task_description="Diversified basket whole-share allocation",
            status="success",
            summary=f"Invested: ₹{basket_res.get('total_invested'):,.2f} | Remaining Cash: ₹{basket_res.get('cash_remaining'):,.2f}",
        )

    # 7. Fetch News for shortlisted candidates via DuckDuckGo
    news_by_symbol: dict[str, list[dict[str, Any]]] = {}
    for s in shortlisted:
        sym = s["symbol"]
        news_res = search_stock_news(sym, s["short_name"], max_results=3)
        articles = news_res.get("articles", [])
        news_by_symbol[sym] = articles
        agent.log_tool_activity(
            tool_name="DuckDuckGoTools",
            task_description=f"News search for {s['short_name']}",
            status="success" if articles else "warning",
            summary=f"Found {len(articles)} recent articles" if articles else "No recent articles found, continuing without news",
        )

    # 8. Agno Agent Synthesis with Groq openai/gpt-oss-120b
    synthesis_result = agent.run_synthesis(
        budget=budget,
        duration=duration,
        risk_tolerance=risk_tolerance,
        stock_preference=stock_preference,
        investment_type=investment_type,
        market=market,
        candidate_data=shortlisted,
    )

    # 9. Prepare Comparison Table Dataset
    comparison_table = []
    for s in shortlisted:
        comparison_table.append({
            "Ticker": s["symbol"],
            "Company": s["short_name"],
            "Sector": s["sector"],
            "Price (₹)": f"₹{s['current_price']:,.2f}",
            "Score": f"{s['screening_score']}/100",
            "Return": f"{'+' if (s.get('return_pct') or 0) > 0 else ''}{s.get('return_pct')}%",
            "RSI (14)": f"{s.get('rsi')}",
            "Trend": s.get("trend", "Neutral"),
            "Volatility": f"{s.get('annualized_volatility_pct')}%",
            "Affordable Shares": s.get("affordable_shares", 0),
        })

    # Latest data date
    latest_date = shortlisted[0].get("latest_data_date", datetime.now().strftime("%Y-%m-%d"))

    # 10. Persist Analysis to SQLite
    shortlisted_symbols = [s["symbol"] for s in shortlisted]
    analysis_id = save_analysis(
        budget=budget,
        duration=duration,
        risk_tolerance=risk_tolerance,
        stock_preference=stock_preference,
        investment_type=investment_type,
        shortlisted_symbols=shortlisted_symbols,
        summary_explanation=synthesis_result.get("synthesis_markdown", "")[:1000],
        full_payload={
            "shortlisted": shortlisted,
            "basket_allocation": basket_allocation,
            "latest_data_date": latest_date,
            "comparison_table": comparison_table,
        },
        market_universe=market,
    )

    return {
        "status": "success",
        "analysis_id": analysis_id,
        "summary": {
            "budget": budget,
            "duration": duration,
            "risk_tolerance": risk_tolerance,
            "stock_preference": stock_preference,
            "investment_type": investment_type,
            "market": market,
            "candidates_analyzed": len(analyzed_candidates),
            "shortlisted_count": len(shortlisted),
            "latest_data_date": latest_date,
        },
        "shortlisted": shortlisted,
        "basket_allocation": basket_allocation,
        "comparison_table": comparison_table,
        "news_by_symbol": news_by_symbol,
        "synthesis_markdown": synthesis_result.get("synthesis_markdown", ""),
        "tool_logs": synthesis_result.get("tool_logs", []),
    }
