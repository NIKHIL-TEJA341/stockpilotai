import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(dotenv_path=BASE_DIR / ".env")

class Settings:
    # Groq Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    # Application settings
    APP_NAME: str = "StockPilot AI"
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEFAULT_MARKET: str = os.getenv("DEFAULT_MARKET", "NSE")
    DATABASE_PATH: Path = BASE_DIR / os.getenv("DATABASE_PATH", "stockpilot.db")
    DATA_DIR: Path = BASE_DIR / "data"
    STOCK_UNIVERSE_PATH: Path = BASE_DIR / "data" / "stock_universe.csv"

    # Financial analysis defaults
    DEFAULT_LOOKBACK_PERIOD: str = "1y"
    DEFAULT_RSI_PERIOD: int = 14
    FAST_SMA_PERIOD: int = 20
    SLOW_SMA_PERIOD: int = 50
    TRADING_DAYS_PER_YEAR: int = 252

    @classmethod
    def validate(cls) -> list[str]:
        """Validate critical configuration settings."""
        errors = []
        if not cls.GROQ_API_KEY:
            errors.append("GROQ_API_KEY is not set in environment or .env file.")
        return errors

settings = Settings()
