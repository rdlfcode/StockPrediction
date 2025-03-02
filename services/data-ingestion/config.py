import os
from pydantic import BaseSettings, PostgresDsn, RedisDsn

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: PostgresDsn
    TIMESCALEDB_URL: PostgresDsn
    
    # Kafka settings
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_PRICE_DATA_TOPIC: str = "stock-price-data"
    KAFKA_FEATURE_DATA_TOPIC: str = "stock-feature-data"
    
    # Redis settings
    REDIS_URL: RedisDsn
    
    # API settings
    API_KEY_ALPHA_VANTAGE: str = os.getenv("API_KEY_ALPHA_VANTAGE", "")
    API_KEY_FINNHUB: str = os.getenv("API_KEY_FINNHUB", "")
    API_KEY_POLYGON: str = os.getenv("API_KEY_POLYGON", "")
    
    # Data ingestion settings
    DATA_BATCH_SIZE: int = 1000
    DATA_FETCH_INTERVAL_MINUTES: int = 15
    HISTORICAL_DATA_DAYS: int = 365 * 2  # 2 years
    
    # Feature engineering settings
    FEATURE_CALCULATION_INTERVALS: list[int] = [5, 10, 20, 50, 100, 200]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()