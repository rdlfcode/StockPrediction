from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from db import get_db_session
from services.stock_data_service import StockDataService
from services.feature_engineering_service import FeatureEngineeringService
from tasks.data_ingestion_tasks import import_historical_data_for_all_stocks
from models.api import (
    StockCreate, 
    StockResponse, 
    ImportIndexRequest, 
    ImportDataRequest,
    EnableRealtimeRequest
)

router = APIRouter()
stock_service = StockDataService()
feature_service = FeatureEngineeringService()

@router.post("/stocks", response_model=StockResponse)
async def create_stock(stock: StockCreate):
    """Add a new stock to the database."""
    result = await stock_service.add_stock(stock.ticker)
    if not result:
        raise HTTPException(status_code=404, detail=f"Could not retrieve info for ticker {stock.ticker}")
    return result

@router.get("/stocks", response_model=List[StockResponse])
async def get_stocks(active_only: bool = True):
    """Get all stocks."""
    return await stock_service.get_all_stocks(active_only)

@router.get("/stocks/{stock_id}", response_model=StockResponse)
async def get_stock(stock_id: int):
    """Get a stock by ID."""
    stock = await stock_service.get_stock_by_id(stock_id)
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock with ID {stock_id} not found")
    return stock

@router.post("/stocks/import", response_model=List[StockResponse])
async def import_index(request: ImportIndexRequest):
    """Import stocks from a market index."""
    return await stock_service.import_market_index(request.source)

@router.post("/data/import_historical")
async def import_historical_data(request: ImportDataRequest, stock_id: int = None):
    """Import historical data for a stock or all stocks."""
    if stock_id:
        return await stock_service.import_historical_data(stock_id, request.days)
    else:
        # Run in background task
        background_tasks.add_task(import_historical_data_for_all_stocks)
        return {"message": "Historical data import started in the background"}

@router.post("/data/enable_realtime")
async def enable_realtime_data(request: EnableRealtimeRequest):
    """Enable real-time data ingestion."""
    from config import settings
    
    # Update the data fetch interval
    settings.DATA_FETCH_INTERVAL_MINUTES = request.interval_minutes
    
    return {
        "message": f"Real-time data ingestion enabled with interval of {request.interval_minutes} minutes"
    }

@router.get("/data/latest/{stock_id}")
async def get_latest_data(stock_id: int):
    """Get the latest data for a stock."""
    return await stock_service.get_latest_price_data(stock_id)

@router.post("/features/generate/{stock_id}")
async def generate_features(stock_id: int, days: int = 60):
    """Generate features for a stock."""
    from datetime import datetime, timedelta
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    features = await feature_service.generate_features_for_stock(stock_id, start_date, end_date)
    
    if not features:
        raise HTTPException(status_code=404, detail=f"No data found for stock {stock_id}")
    
    await feature_service.store_features(stock_id, features)
    
    return {
        "message": f"Features generated and stored for stock {stock_id}",
        "feature_types": list(features.keys()),
        "data_points": sum(len(data) for data in features.values())
    }