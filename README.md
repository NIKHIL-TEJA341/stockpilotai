# 🚀 StockPilot AI — Indian Equity Analysis & Decision Support

StockPilot AI is an AI-agent-based financial research and stock analysis application designed for the Indian equities market (NSE / BSE).

It combines:
- **Groq API Inference** using **`openai/gpt-oss-120b`** (strictly configured in `.env`)
- **Agno Framework (v3.1.4)** for agent execution and tool management
- **Yahoo Finance** for historical daily stock data and fundamentals
- **DuckDuckGo Search** for real-time company news
- **Deterministic Python Financial Calculations**:
  - Historical returns
  - Simple Moving Averages (20/50 SMA & Trend Analysis)
  - 14-period Wilder Relative Strength Index (RSI)
  - Historical Daily & Annualized Volatility
  - Whole-share Budget Affordability & Diversified Basket Allocation
- **Transparent 5-Factor Screening & Scoring Methodology** (0-100 score)
- **Verified Tool Execution Transparency** (Feature 7: Only actually executed tools appear in activity logs)
- **Polished Streamlit Financial Dashboard** (Dark slate theme, interactive Plotly charts, multi-stock comparison, SQLite-backed watchlist and analysis history)

---

## 🏗️ Project Architecture

```text
stockpilotai/
├── app.py                      # Main Streamlit application entrypoint
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (GROQ_API_KEY, GROQ_MODEL)
├── .env.example                # Example configuration
├── prd.txt                     # Comprehensive Product Requirements Document
│
├── config/
│   ├── __init__.py
│   └── settings.py             # Settings, defaults, and paths
│
├── data/
│   └── stock_universe.csv      # Curated Indian equity universe (50 stocks across market caps)
│
├── database/
│   ├── __init__.py
│   ├── db.py                   # SQLite connection & schema init
│   └── repository.py           # Watchlist & analysis history CRUD operations
│
├── tools/
│   ├── __init__.py
│   ├── analysis_tools.py       # Deterministic Python financial calculations
│   └── news_tools.py           # DuckDuckGo financial news search with graceful fallback
│
├── services/
│   ├── __init__.py
│   ├── market_data_service.py  # Yahoo Finance retrieval, caching, & normalization
│   ├── stock_screener.py       # Candidate universe filtering
│   ├── ranking_service.py      # Documented 5-factor scoring engine
│   └── analysis_service.py     # End-to-end analysis orchestration pipeline
│
├── agents/
│   ├── __init__.py
│   ├── instructions.py         # Grounded system prompts for openai/gpt-oss-120b
│   └── stock_agent.py          # Agno Groq Agent with tool telemetry
│
├── ui/
│   ├── __init__.py
│   ├── dashboard.py            # Main investment analysis dashboard & tool activity
│   ├── comparison.py           # Side-by-side stock comparison view
│   ├── watchlist.py            # SQLite watchlist management
│   └── history.py              # Past analysis sessions browser
│
└── tests/
    ├── test_calculations.py    # Unit tests for financial formulas
    └── run_tests.py            # Standalone test runner
```

---

## ⚙️ Configuration (`.env`)

StockPilot AI uses the Groq-hosted `openai/gpt-oss-120b` model:

```ini
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b

# Application Settings
APP_ENV=development
DEFAULT_MARKET=NSE
DATABASE_PATH=stockpilot.db
```

---

## 🏃‍♂️ How to Run the Application

Activate your virtual environment and launch Streamlit:

```powershell
.\venv\Scripts\activate
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## ⚠️ Statutory Disclaimer

StockPilot AI provides AI-generated analysis based on available financial data and historical information. It is intended for informational and educational purposes and is **not personalized investment advice**. Stock prices and data may be delayed, incomplete, or inaccurate. Historical performance does not guarantee future results.
