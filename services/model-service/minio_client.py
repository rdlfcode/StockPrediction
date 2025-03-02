import logging
from typing import Any, Optional

from config import settings
from aiominio import Client

logger = logging.getLogger(__name__)

_minio_client = None

async def get_minio_client() -> Client:
    """Get the MinIO client instance."""
    global _minio_client
    
    if _minio_client is None:
        try:
            # Create a client with the MinIO server
            _minio_client = Client(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
            
            # Check if the required buckets exist and create them if not
            buckets_to_check = [settings.MODELS_BUCKET, settings.DATASETS_BUCKET]
            
            for bucket in buckets_to_check:
                exists = await _minio_client.bucket_exists(bucket)
                if not exists:
                    await _minio_client.make_bucket(bucket)
                    logger.info(f"Created bucket: {bucket}")
            
            logger.info("MinIO client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing MinIO client: {str(e)}")
            raise
    
    return _minio_client