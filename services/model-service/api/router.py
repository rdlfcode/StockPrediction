from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from db import get_db_session
from services.model_registry import ModelRegistry
from services.training_service import TrainingService
from services.inference_service import InferenceService
from models.api import (
    ModelCreate, 
    ModelResponse, 
    TrainModelRequest,
    PredictionRequest,
    BatchPredictionRequest,
    ComparisonRequest
)

router = APIRouter()
model_registry = ModelRegistry()
training_service = TrainingService(model_registry)
inference_service = InferenceService(model_registry)

@router.post("/models", response_model=ModelResponse)
async def create_model(model: ModelCreate):
    """Create a new model."""
    result = await model_registry.create_model(
        model.architecture,
        model.name,
        model.version,
        model.hyperparameters,
        model.feature_config,
        model.training_dataset_config
    )
    
    if not result:
        raise HTTPException(status_code=400, detail="Could not create model")
    
    return result

@router.get("/models", response_model=List[ModelResponse])
async def get_models(architecture: Optional[str] = None):
    """Get all models."""
    if architecture:
        return await model_registry.get_models_by_architecture(architecture)
    else:
        models = []
        for arch_name in model_registry.available_architectures:
            models.extend(await model_registry.get_models_by_architecture(arch_name))
        return models

@router.get("/models/{model_id}", response_model=ModelResponse)
async def get_model(model_id: int):
    """Get a model by ID."""
    model = await model_registry.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model with ID {model_id} not found")
    return model

@router.post("/models/train")
async def train_model(request: TrainModelRequest, background_tasks: BackgroundTasks):
    """Train a model."""
    model = await model_registry.create_model(
        request.architecture,
        request.name,
        request.version,
        request.hyperparameters,
        request.feature_config,
        request.training_dataset_config
    )
    
    if not model:
        raise HTTPException(status_code=400, detail="Could not create model")
    
    # Train model in background task
    background_tasks.add_task(training_service.train_model, model.id, request.stock_ids)
    
    return {
        "message": f"Model creation initiated. Training started in background.",
        "model_id": model.id
    }

@router.post("/models/{model_id}/train")
async def retrain_model(model_id: int, stock_ids: Optional[List[int]] = None, background_tasks: BackgroundTasks = None):
    """Retrain an existing model."""
    model = await model_registry.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model with ID {model_id} not found")
    
    if background_tasks:
        # Train in background
        background_tasks.add_task(training_service.train_model, model_id, stock_ids)
        
        return {
            "message": f"Retraining of model {model_id} started in background."
        }
    else:
        # Train synchronously
        success, message = await training_service.train_model(model_id, stock_ids)
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        return {
            "message": message
        }

@router.post("/predictions")
async def generate_prediction(request: PredictionRequest):
    """Generate predictions for a stock using a model."""
    if not await model_registry.get_model(request.model_id):
        raise HTTPException(status_code=404, detail=f"Model with ID {request.model_id} not found")
    
    prediction = await inference_service.generate_predictions(
        request.model_id, 
        request.stock_id,
        request.save_to_db
    )
    
    if not prediction:
        raise HTTPException(status_code=400, detail="Could not generate prediction")
    
    return prediction

@router.post("/predictions/batch")
async def generate_batch_predictions(request: BatchPredictionRequest):
    """Generate predictions for multiple stocks using multiple models."""
    result = await inference_service.generate_batch_predictions(
        request.model_ids,
        request.stock_ids,
        request.save_to_db
    )
    
    return result

@router.get("/predictions/comparison")
async def get_prediction_comparison(
    stock_id: int,
    model_ids: List[int],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get comparison data for multiple models for a specific stock."""
    # Parse dates
    if not start_date:
        start_date_dt = datetime.now() - timedelta(days=30)
    else:
        start_date_dt = datetime.fromisoformat(start_date)
    
    if not end_date:
        end_date_dt = datetime.now() + timedelta(days=5)
    else:
        end_date_dt = datetime.fromisoformat(end_date)
    
    comparison_data = await inference_service.get_comparison_data(
        model_ids,
        stock_id,
        start_date_dt,
        end_date_dt
    )
    
    if "error" in comparison_data:
        raise HTTPException(status_code=400, detail=comparison_data["error"])
    
    return comparison_data

@router.get("/models/{model_id}/feature_importance")
async def get_feature_importance(model_id: int):
    """Get feature importance for a model."""
    model = await model_registry.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model with ID {model_id} not found")
    
    feature_importance = await model_registry.get_feature_importance(model_id)
    
    return {
        "model_id": model_id,
        "feature_importance": feature_importance
    }