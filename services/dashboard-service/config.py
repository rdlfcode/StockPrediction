from pydantic import BaseSettings, PostgresDsn, RedisDsn, HttpUrl

class Settings(BaseSettings):
    # Database settings
    # PostgreSQL connection string for the main database
    DATABASE_URL: PostgresDsn
    # PostgreSQL connection string for the TimescaleDB instance (time-series data)
    TIMESCALEDB_URL: PostgresDsn
    
    # Redis settings - used for caching dashboard data
    REDIS_URL: RedisDsn
    
    # Service URLs - internal service connections
    # URL for the model service API
    MODEL_SERVICE_URL: HttpUrl
    
    # Dashboard settings
    # Default number of items per page in lists/tables (20 is good for most screens)
    DEFAULT_PAGE_SIZE: int = 20
    # Default cache TTL in seconds (60 seconds balances freshness and performance)
    DEFAULT_CACHE_TTL_SECONDS: int = 60
    
    # Session settings
    # Secret key for signing session cookies (must be unique and secure)
    SECRET_KEY: str
    # Name of the session cookie
    SESSION_COOKIE_NAME: str = "stock_prediction_session"
    # Session lifetime in seconds (1 week = 3600 * 24 * 7)
    SESSION_MAX_AGE: int = 3600 * 24 * 7
    
    class Config:
        # Path to .env file for loading these settings
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()