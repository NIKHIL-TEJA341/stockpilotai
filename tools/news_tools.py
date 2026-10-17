"""News search tool for StockPilot AI.

Integrates with DuckDuckGo to retrieve recent financial news for analyzed equities.
Includes robust fallback and error handling as specified in PRD Section 10.
"""

from datetime import datetime
from typing import Any
import json

try:
    from agno.tools.duckduckgo import DuckDuckGoTools
    _HAS_AGNO_DDG = True
except ImportError:
    _HAS_AGNO_DDG = False

try:
    from duckduckgo_search import DDGS
    _HAS_DDGS = True
except ImportError:
    _HAS_DDGS = False


def search_stock_news(
    symbol: str,
    company_name: str,
    max_results: int = 5,
) -> dict[str, Any]:
    """Retrieve recent news articles for a company/stock symbol.

    Returns structured news items with title, link, date, source, and summary.
    If search fails or returns empty, returns a safe fallback message without crashing.
    """
    clean_symbol = symbol.replace(".NS", "").replace(".BO", "").strip()
    query = f"{company_name} {clean_symbol} stock market news"
    
    articles: list[dict[str, Any]] = []

    # Attempt 1: Direct DDGS library
    if _HAS_DDGS:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.news(keywords=query, max_results=max_results))
                for item in results:
                    articles.append({
                        "title": item.get("title", "No Title"),
                        "link": item.get("url") or item.get("link", "#"),
                        "date": item.get("date") or datetime.now().strftime("%Y-%m-%d"),
                        "source": item.get("source", "Web"),
                        "snippet": item.get("body") or item.get("snippet", ""),
                    })
        except Exception:
            articles = []

    # Attempt 2: Agno DuckDuckGoTools if DDGS yielded no articles
    if not articles and _HAS_AGNO_DDG:
        try:
            ddg_tool = DuckDuckGoTools(fixed_max_results=max_results)
            raw_results = ddg_tool.search_news(query=query)
            if isinstance(raw_results, str):
                try:
                    parsed = json.loads(raw_results)
                    if isinstance(parsed, list):
                        for item in parsed:
                            articles.append({
                                "title": item.get("title", "News Item"),
                                "link": item.get("url") or item.get("link", "#"),
                                "date": item.get("date") or datetime.now().strftime("%Y-%m-%d"),
                                "source": item.get("source", "Web"),
                                "snippet": item.get("body") or item.get("snippet", ""),
                            })
                except Exception:
                    articles.append({
                        "title": f"Recent coverage for {company_name}",
                        "link": f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "source": "DuckDuckGo Search",
                        "snippet": str(raw_results)[:300],
                    })
        except Exception:
            articles = []

    if not articles:
        return {
            "status": "warning",
            "symbol": symbol,
            "company_name": company_name,
            "message": f"No recent news articles could be retrieved for {symbol} at this time. Continuing analysis with available market and financial data.",
            "articles": [],
            "retrieved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    return {
        "status": "success",
        "symbol": symbol,
        "company_name": company_name,
        "total_results": len(articles),
        "articles": articles[:max_results],
        "retrieved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
