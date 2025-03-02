import os
from pydantic import BaseSettings, PostgresDsn, RedisDsn

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: PostgresDsn
    TIMESCALEDB_URL: PostgresDsn
    
    # Redis settings
    REDIS_URL: RedisDsn
    
    # Kafka settings
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_PREDICTION_TOPIC: str = "stock-predictions"
    
    # MinIO settings
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_SECURE: bool = False
    MODELS_BUCKET: str = "models"
    DATASETS_BUCKET: str = "datasets"
    
    # Model service settings
    MODEL_BATCH_SIZE: int = 32
    DEFAULT_PREDICTION_HORIZON_DAYS: int = 5
    
    # PyTorch settings
    PYTORCH_DEVICE: str = "cuda" if torch.cuda.is_available() else "cpu"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()