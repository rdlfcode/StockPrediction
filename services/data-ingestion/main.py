import asyncio
import logging
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db_session
from config import settings
from services.stock_data_service import StockDataService
from services.feature_engineering_service import FeatureEngineeringService
from api.router import router as api_router
from tasks.data_ingestion_tasks import start_scheduled_data_ingestion

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("data_ingestion")

# Create FastAPI app
app = FastAPI(
    title="Stock Prediction Platform - Data Ingestion Service",
    description="Service for ingesting and processing stock data",
    version="0.1.0",
)

# Include API router
app.include_router(api_router, prefix="/api")

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting data ingestion service")
    
    # Start scheduled data ingestion tasks
    asyncio.create_task(start_scheduled_data_ingestion())
    
    logger.info("Data ingestion service started")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Main entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)