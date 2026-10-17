"""Data access repository for watchlist and analysis history."""

import json
from datetime import datetime
from typing import Any
from database.db import get_connection


def add_to_watchlist(symbol: str, name: str, sector: str = "Unknown", market_cap: str = "Unknown") -> bool:
    """Add a stock symbol to the watchlist."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO watchlist (symbol, name, sector, market_cap_category, added_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (symbol.upper(), name, sector, market_cap, datetime.now().isoformat()),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding to watchlist: {e}")
        return False
    finally:
        conn.close()


def remove_from_watchlist(symbol: str) -> bool:
    """Remove a stock symbol from the watchlist."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM watchlist WHERE symbol = ?", (symbol.upper(),))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error removing from watchlist: {e}")
        return False
    finally:
        conn.close()


def get_watchlist() -> list[dict[str, Any]]:
    """Retrieve all stocks from the watchlist."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM watchlist ORDER BY added_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def is_in_watchlist(symbol: str) -> bool:
    """Check if a stock symbol is already in the watchlist."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM watchlist WHERE symbol = ?", (symbol.upper(),))
        return cursor.fetchone() is not None
    finally:
        conn.close()


def save_analysis(
    budget: float,
    duration: str,
    risk_tolerance: str,
    stock_preference: str,
    investment_type: str,
    shortlisted_symbols: list[str],
    summary_explanation: str,
    full_payload: dict[str, Any] | None = None,
    market_universe: str = "NSE",
) -> int:
    """Save an investment analysis record to the database."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO analysis_history (
                budget, duration, risk_tolerance, stock_preference,
                investment_type, market_universe, shortlisted_symbols,
                summary_explanation, full_payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                budget,
                duration,
                risk_tolerance,
                stock_preference,
                investment_type,
                market_universe,
                json.dumps(shortlisted_symbols),
                summary_explanation,
                json.dumps(full_payload or {}, default=str),
            ),
        )
        conn.commit()
        return cursor.lastrowid or 0
    except Exception as e:
        print(f"Error saving analysis: {e}")
        return 0
    finally:
        conn.close()


def get_analysis_history(limit: int = 20) -> list[dict[str, Any]]:
    """Retrieve recent analysis history records."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM analysis_history ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        results = []
        for row in rows:
            record = dict(row)
            try:
                record["shortlisted_symbols"] = json.loads(record["shortlisted_symbols"])
            except Exception:
                record["shortlisted_symbols"] = []
            results.append(record)
        return results
    finally:
        conn.close()


def get_analysis_by_id(analysis_id: int) -> dict[str, Any] | None:
    """Retrieve a single analysis record by ID."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM analysis_history WHERE id = ?", (analysis_id,))
        row = cursor.fetchone()
        if not row:
            return None
        record = dict(row)
        try:
            record["shortlisted_symbols"] = json.loads(record["shortlisted_symbols"])
        except Exception:
            record["shortlisted_symbols"] = []
        try:
            record["full_payload_json"] = json.loads(record["full_payload_json"])
        except Exception:
            record["full_payload_json"] = {}
        return record
    finally:
        conn.close()
