import logging
import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from config import settings
from redis_client import get_redis_client

logger = logging.getLogger(__name__)

class DashboardService:
    """Service for retrieving data for the dashboard."""
    
    def __init__(self):
        self.redis_client = get_redis_client()
        self.model_service_url = settings.MODEL_SERVICE_URL
    
    async def get_stocks(self) -> List[Dict[str, Any]]:
        """Get list of stocks."""
        # Create HTTP client
        async with httpx.AsyncClient() as client:
            try:
                # Get stocks from the data ingestion service
                response = await client.get(f"{settings.MODEL_SERVICE_URL}/api/stocks")
                response.raise_for_status()
                
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"Error getting stocks: {str(e)}")
                return []
    
    async def get_models(self) -> List[Dict[str, Any]]:
        """Get list of models."""
        # Try to get from cache first
        cached_models = await self.redis_client.get("models")
        if cached_models:
            return cached_models
        
        # If not in cache, get from model service
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{settings.MODEL_SERVICE_URL}/api/models")
                response.raise_for_status()
                
                models = response.json()
                
                # Cache for future requests
                await self.redis_client.setex("models", settings.DEFAULT_CACHE_TTL_SECONDS, models)
                
                return models
            except httpx.RequestError as e:
                logger.error(f"Error getting models: {str(e)}")
                return []
    
    async def get_prediction_comparison(
        self, 
        stock_id: int,
        model_ids: List[int],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get comparison data for multiple models for a specific stock."""
        # Set default dates if not provided
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        
        if not end_date:
            end_date = datetime.now() + timedelta(days=5)
        
        # Create HTTP client
        async with httpx.AsyncClient() as client:
            try:
                # Prepare query params
                params = {
                    "stock_id": stock_id,
                    "model_ids": model_ids,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
                
                # Make request to model service
                response = await client.get(
                    f"{settings.MODEL_SERVICE_URL}/api/predictions/comparison",
                    params=params
                )
                response.raise_for_status()
                
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"Error getting prediction comparison: {str(e)}")
                return {"error": str(e)}
    
    async def get_feature_importance(self, model_id: int) -> Dict[str, Any]:
        """Get feature importance for a model."""
        # Try to get from cache first
        cache_key = f"feature_importance:{model_id}"
        cached_data = await self.redis_client.get(cache_key)
        if cached_data:
            return cached_data
        
        # If not in cache, get from model service
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{settings.MODEL_SERVICE_URL}/api/models/{model_id}/feature_importance"
                )
                response.raise_for_status()
                
                feature_importance = response.json()
                
                # Cache for future requests
                await self.redis_client.setex(
                    cache_key, 
                    settings.DEFAULT_CACHE_TTL_SECONDS, 
                    feature_importance
                )
                
                return feature_importance
            except httpx.RequestError as e:
                logger.error(f"Error getting feature importance: {str(e)}")
                return {"error": str(e)}
    
    async def generate_prediction(
        self, 
        model_id: int,
        stock_id: int
    ) -> Dict[str, Any]:
        """Generate a new prediction for a stock using a model."""
        async with httpx.AsyncClient() as client:
            try:
                # Prepare request data
                data = {
                    "model_id": model_id,
                    "stock_id": stock_id,
                    "save_to_db": True
                }
                
                # Make request to model service
                response = await client.post(
                    f"{settings.MODEL_SERVICE_URL}/api/predictions",
                    json=data
                )
                response.raise_for_status()
                
                # Invalidate cache for comparison data
                cache_key = f"comparison:{stock_id}"
                await self.redis_client.delete(cache_key)
                
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"Error generating prediction: {str(e)}")
                return {"error": str(e)}
    
    async def get_model_metrics(self, model_id: int) -> Dict[str, Any]:
        """Get performance metrics for a model."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{settings.MODEL_SERVICE_URL}/api/models/{model_id}/metrics"
                )
                response.raise_for_status()
                
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"Error getting model metrics: {str(e)}")
                return {"error": str(e)}