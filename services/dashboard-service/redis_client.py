import logging
import json
from typing import Any, Dict, List, Optional, Union
import aioredis

from config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    """Client for Redis caching."""
    
    def __init__(self, url: str):
        self.url = url
        self.redis = None
    
    async def connect(self):
        """Connect to Redis."""
        try:
            self.redis = await aioredis.create_redis_pool(self.url)
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Error connecting to Redis: {str(e)}")
            self.redis = None
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()
            logger.info("Disconnected from Redis")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from Redis."""
        if not self.redis:
            await self.connect()
            if not self.redis:
                return None
        
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting key {key} from Redis: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any) -> bool:
        """Set a value in Redis."""
        if not self.redis:
            await self.connect()
            if not self.redis:
                return False
        
        try:
            await self.redis.set(key, json.dumps(value))
            return True
        except Exception as e:
            logger.error(f"Error setting key {key} in Redis: {str(e)}")
            return False
    
    async def setex(self, key: str, seconds: int, value: Any) -> bool:
        """Set a value in Redis with an expiration time."""
        if not self.redis:
            await self.connect()
            if not self.redis:
                return False
        
        try:
            await self.redis.setex(key, seconds, json.dumps(value))
            return True
        except Exception as e:
            logger.error(f"Error setting key {key} with expiration in Redis: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete a key from Redis."""
        if not self.redis:
            await self.connect()
            if not self.redis:
                return False
        
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting key {key} from Redis: {str(e)}")
            return False

_redis_client = None

def get_redis_client() -> RedisClient:
    """Get the Redis client instance."""
    global _redis_client
    
    if _redis_client is None:
        _redis_client = RedisClient(settings.REDIS_URL)
    
    return _redis_client