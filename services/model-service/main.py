import logging
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db_session
from config import settings
from api.router import router as api_router
from services.model_registry import ModelRegistry
from services.training_service import TrainingService
from services.inference_service import InferenceService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("model_service")

# Create FastAPI app
app = FastAPI(
    title="Stock Prediction Platform - Model Service",
    description="Service for training and serving machine learning models for stock prediction",
    version="0.1.0",
)

# Include API router
app.include_router(api_router, prefix="/api")

# Initialize services
model_registry = ModelRegistry()
training_service = TrainingService(model_registry)
inference_service = InferenceService(model_registry)

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting model service")
    
    # Initialize model registry
    await model_registry.initialize()
    
    logger.info("Model service started")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Main entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)