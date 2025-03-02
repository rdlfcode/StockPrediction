import os
import torch
from pydantic import BaseSettings, PostgresDsn, RedisDsn

class Settings(BaseSettings):
    # Database settings
    # PostgreSQL connection string for the main database
    DATABASE_URL: PostgresDsn
    # PostgreSQL connection string for the TimescaleDB instance (time-series data)
    TIMESCALEDB_URL: PostgresDsn
    
    # Redis settings - used for caching prediction results
    REDIS_URL: RedisDsn
    
    # Kafka settings
    # Comma-separated list of Kafka bootstrap servers
    KAFKA_BOOTSTRAP_SERVERS: str
    # Topic name for publishing prediction events (default: stock-predictions)
    KAFKA_PREDICTION_TOPIC: str = "stock-predictions"
    
    # MinIO settings - used for storing model artifacts
    # MinIO server endpoint (e.g., "minio:9000")
    MINIO_ENDPOINT: str
    # MinIO access key (username)
    MINIO_ACCESS_KEY: str
    # MinIO secret key (password)
    MINIO_SECRET_KEY: str
    # Whether to use HTTPS for MinIO connection (default: false for development)
    MINIO_SECURE: bool = False
    # Bucket name for storing trained models
    MODELS_BUCKET: str = "models"
    # Bucket name for storing datasets
    DATASETS_BUCKET: str = "datasets"
    
    # Model service settings
    # Batch size for model training/inference (adjust based on available memory)
    # Larger values (32-128) speed up training but require more RAM/VRAM
    MODEL_BATCH_SIZE: int = 32
    # Default number of days to forecast into the future (5 is balanced)
    DEFAULT_PREDICTION_HORIZON_DAYS: int = 5
    
    # PyTorch settings
    # Device to use for model training/inference ("cuda" for GPU, "cpu" for CPU)
    # Auto-detects CUDA availability by default
    PYTORCH_DEVICE: str = "cuda" if torch.cuda.is_available() else "cpu"
    
    class Config:
        # Path to .env file for loading these settings
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()