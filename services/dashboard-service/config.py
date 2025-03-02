from pydantic import BaseSettings, PostgresDsn, RedisDsn, HttpUrl

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: PostgresDsn
    TIMESCALEDB_URL: PostgresDsn
    
    # Redis settings
    REDIS_URL: RedisDsn
    
    # Service URLs
    MODEL_SERVICE_URL: HttpUrl
    
    # Dashboard settings
    DEFAULT_PAGE_SIZE: int = 20
    DEFAULT_CACHE_TTL_SECONDS: int = 60
    
    # Session settings
    SECRET_KEY: str
    SESSION_COOKIE_NAME: str = "stock_prediction_session"
    SESSION_MAX_AGE: int = 3600 * 24 * 7  # 1 week
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()