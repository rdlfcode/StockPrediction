from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from services.dashboard_service import DashboardService
from models.api import PredictionRequest, StockComparisonRequest

router = APIRouter()
dashboard_service = DashboardService()

@router.get("/stocks")
async def get_stocks():
    """Get list of stocks."""
    stocks = await dashboard_service.get_stocks()
    if not stocks:
        raise HTTPException(status_code=404, detail="No stocks found")
    return stocks

@router.get("/models")
async def get_models():
    """Get list of models."""
    models = await dashboard_service.get_models()
    if not models:
        raise HTTPException(status_code=404, detail="No models found")
    return models

@router.get("/predictions/comparison")
async def get_prediction_comparison(
    stock_id: int,
    model_ids: List[int],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get comparison data for multiple models for a specific stock."""
    # Parse dates if provided
    start_date_dt = datetime.fromisoformat(start_date) if start_date else None
    end_date_dt = datetime.fromisoformat(end_date) if end_date else None
    
    comparison = await dashboard_service.get_prediction_comparison(
        stock_id, model_ids, start_date_dt, end_date_dt
    )
    
    if "error" in comparison:
        raise HTTPException(status_code=400, detail=comparison["error"])
    
    return comparison

@router.post("/predictions")
async def generate_prediction(request: PredictionRequest):
    """Generate a new prediction for a stock using a model."""
    result = await dashboard_service.generate_prediction(
        request.model_id, request.stock_id
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@router.get("/models/{model_id}/feature_importance")
async def get_feature_importance(model_id: int):
    """Get feature importance for a model."""
    result = await dashboard_service.get_feature_importance(model_id)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@router.get("/models/{model_id}/metrics")
async def get_model_metrics(model_id: int):
    """Get performance metrics for a model."""
    result = await dashboard_service.get_model_metrics(model_id)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result