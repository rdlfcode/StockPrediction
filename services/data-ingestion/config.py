import os
from pydantic import BaseSettings, PostgresDsn, RedisDsn

class Settings(BaseSettings):
    # Database settings
    # PostgreSQL connection string for the main database
    DATABASE_URL: PostgresDsn
    # PostgreSQL connection string for the TimescaleDB instance (time-series data)
    TIMESCALEDB_URL: PostgresDsn
    
    # Kafka settings
    # Comma-separated list of Kafka bootstrap servers
    KAFKA_BOOTSTRAP_SERVERS: str
    # Topic name for publishing price data events (default: stock-price-data)
    KAFKA_PRICE_DATA_TOPIC: str = "stock-price-data"
    # Topic name for publishing feature data events (default: stock-feature-data)
    KAFKA_FEATURE_DATA_TOPIC: str = "stock-feature-data"
    
    # Redis settings - used for caching and rate limiting
    REDIS_URL: RedisDsn
    
    # API settings - keys for external data providers
    # Alpha Vantage API key for stock data (register at alphavantage.co)
    API_KEY_ALPHA_VANTAGE: str = os.getenv("API_KEY_ALPHA_VANTAGE", "")
    # Finnhub API key for additional market data (register at finnhub.io)
    API_KEY_FINNHUB: str = os.getenv("API_KEY_FINNHUB", "")
    # Polygon.io API key for market data (register at polygon.io)
    API_KEY_POLYGON: str = os.getenv("API_KEY_POLYGON", "")
    
    # Data ingestion settings
    # Number of records to process in a single batch (1000 is a good balance)
    DATA_BATCH_SIZE: int = 1000
    # How often to fetch new data in minutes (15 min respects most API rate limits)
    DATA_FETCH_INTERVAL_MINUTES: int = 15
    # Number of days of historical data to load (730 days = 2 years is recommended)
    HISTORICAL_DATA_DAYS: int = 365 * 2
    
    # Feature engineering settings
    # Time intervals in days for calculating technical indicators like moving averages
    # Common values include 5 (week), 20 (month), 50, 100, 200 (long-term trends)
    FEATURE_CALCULATION_INTERVALS: list[int] = [5, 10, 20, 50, 100, 200]
    
    class Config:
        # Path to .env file for loading these settings
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()