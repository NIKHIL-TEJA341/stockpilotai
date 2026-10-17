"""SQLite Database connection and schema initialization for StockPilot AI."""

import sqlite3
from pathlib import Path
from config.settings import settings


def get_connection() -> sqlite3.Connection:
    """Get a SQLite database connection with row factory enabled."""
    db_path = settings.DATABASE_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize database tables for watchlist and analysis history."""
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 1. Watchlist table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                sector TEXT DEFAULT 'Unknown',
                market_cap_category TEXT DEFAULT 'Unknown',
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Analysis History table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                budget REAL NOT NULL,
                duration TEXT NOT NULL,
                risk_tolerance TEXT NOT NULL,
                stock_preference TEXT NOT NULL,
                investment_type TEXT NOT NULL,
                market_universe TEXT DEFAULT 'NSE',
                shortlisted_symbols TEXT NOT NULL,
                summary_explanation TEXT,
                full_payload_json TEXT
            )
        """)

        conn.commit()
    finally:
        conn.close()
