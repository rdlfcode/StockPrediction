from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime

class ModelCreate(BaseModel):
    """Model for creating a new model."""
    architecture: str
    name: str
    version: str
    hyperparameters: Dict[str, Any]
    feature_config: Optional[Dict[str, Any]] = None
    training_dataset_config: Optional[Dict[str, Any]] = None

class ModelResponse(BaseModel):
    """Model for model response."""
    id: int
    architecture_id: int
    name: str
    version: str
    hyperparameters: Dict[str, Any]
    feature_config: Dict[str, Any]
    training_dataset_config: Dict[str, Any]
    status: str
    model_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class TrainModelRequest(BaseModel):
    """Model for training a model."""
    architecture: str
    name: str
    version: str
    hyperparameters: Dict[str, Any]
    feature_config: Optional[Dict[str, Any]] = None
    training_dataset_config: Optional[Dict[str, Any]] = None
    stock_ids: Optional[List[int]] = None

class PredictionRequest(BaseModel):
    """Model for generating predictions."""
    model_id: int
    stock_id: int
    save_to_db: bool = True

class BatchPredictionRequest(BaseModel):
    """Model for generating batch predictions."""
    model_ids: List[int]
    stock_ids: List[int]
    save_to_db: bool = True

class ComparisonRequest(BaseModel):
    """Model for comparing predictions."""
    stock_id: int
    model_ids: List[int]
    start_date: Optional[str] = None
    end_date: Optional[str] = None