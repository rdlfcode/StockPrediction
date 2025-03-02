import os
import logging
import pickle
import json
from typing import Dict, List, Any, Optional, Tuple
import torch
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db_session
from models.model_management import ModelArchitecture, Model, TrainingHistory
from minio_client import get_minio_client

logger = logging.getLogger(__name__)

class ModelRegistry:
    """Service for managing ML models."""
    
    def __init__(self):
        self.available_architectures = {}
        self.minio_client = get_minio_client()
        
    async def initialize(self):
        """Initialize the model registry."""
        # Load available architectures from database
        await self._load_architectures()
        
    async def _load_architectures(self):
        """Load available model architectures from the database."""
        async with get_db_session() as session:
            query = select(ModelArchitecture)
            result = await session.execute(query)
            architectures = result.scalars().all()
            
            self.available_architectures = {arch.name: arch for arch in architectures}
            
            logger.info(f"Loaded {len(self.available_architectures)} model architectures")
    
    async def create_model(
        self, 
        architecture_name: str, 
        name: str, 
        version: str,
        hyperparameters: Dict[str, Any],
        feature_config: Optional[Dict[str, Any]] = None,
        training_dataset_config: Optional[Dict[str, Any]] = None
    ) -> Optional[Model]:
        """Create a new model record."""
        if architecture_name not in self.available_architectures:
            logger.error(f"Unknown architecture: {architecture_name}")
            return None
        
        architecture = self.available_architectures[architecture_name]
        
        async with get_db_session() as session:
            # Check if model with same name and version exists
            query = select(Model).where(
                Model.name == name,
                Model.version == version
            )
            result = await session.execute(query)
            existing_model = result.scalar_one_or_none()
            
            if existing_model:
                logger.warning(f"Model {name} version {version} already exists")
                return None
            
            # Create new model record
            new_model = Model(
                architecture_id=architecture.id,
                name=name,
                version=version,
                hyperparameters=hyperparameters,
                feature_config=feature_config or {},
                training_dataset_config=training_dataset_config or {},
                status="created",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            session.add(new_model)
            await session.commit()
            await session.refresh(new_model)
            
            logger.info(f"Created new model: {name} version {version}")
            return new_model
    
    async def get_model(self, model_id: int) -> Optional[Model]:
        """Get a model by ID."""
        async with get_db_session() as session:
            query = select(Model).where(Model.id == model_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    async def get_model_by_name_version(self, name: str, version: str) -> Optional[Model]:
        """Get a model by name and version."""
        async with get_db_session() as session:
            query = select(Model).where(
                Model.name == name,
                Model.version == version
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    async def get_models_by_architecture(self, architecture_name: str) -> List[Model]:
        """Get all models for a specific architecture."""
        if architecture_name not in self.available_architectures:
            logger.error(f"Unknown architecture: {architecture_name}")
            return []
        
        architecture = self.available_architectures[architecture_name]
        
        async with get_db_session() as session:
            query = select(Model).where(Model.architecture_id == architecture.id)
            result = await session.execute(query)
            return result.scalars().all()
    
    async def update_model_status(self, model_id: int, status: str) -> bool:
        """Update the status of a model."""
        valid_statuses = ["created", "training", "ready", "failed"]
        if status not in valid_statuses:
            logger.error(f"Invalid status: {status}")
            return False
        
        async with get_db_session() as session:
            query = update(Model).where(Model.id == model_id).values(
                status=status,
                updated_at=datetime.now()
            )
            await session.execute(query)
            await session.commit()
            
            logger.info(f"Updated model {model_id} status to {status}")
            return True
    
    async def store_model_artifact(
        self, 
        model_id: int, 
        model_artifact: Any, 
        model_path: str
    ) -> bool:
        """Store a model artifact in MinIO."""
        try:
            # Serialize the model
            model_bytes = pickle.dumps(model_artifact)
            
            # Store in MinIO
            from io import BytesIO
            model_data = BytesIO(model_bytes)
            
            await self.minio_client.put_object(
                "models", 
                model_path, 
                model_data, 
                len(model_bytes)
            )
            
            # Update model record with path
            async with get_db_session() as session:
                query = update(Model).where(Model.id == model_id).values(
                    model_path=model_path,
                    updated_at=datetime.now()
                )
                await session.execute(query)
                await session.commit()
            
            logger.info(f"Stored model artifact for model {model_id} at {model_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error storing model artifact: {str(e)}")
            return False
    
    async def load_model_artifact(self, model_id: int) -> Tuple[Optional[Any], Optional[str]]:
        """Load a model artifact from MinIO."""
        try:
            # Get model record
            model = await self.get_model(model_id)
            if not model or not model.model_path:
                logger.error(f"Model {model_id} not found or has no artifact path")
                return None, "Model not found or has no artifact path"
            
            # Load from MinIO
            response = await self.minio_client.get_object("models", model.model_path)
            model_bytes = await response.read()
            
            # Deserialize the model
            model_artifact = pickle.loads(model_bytes)
            
            logger.info(f"Loaded model artifact for model {model_id}")
            return model_artifact, None
        
        except Exception as e:
            error_msg = f"Error loading model artifact: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    async def record_training_start(self, model_id: int) -> Optional[int]:
        """Record the start of model training."""
        async with get_db_session() as session:
            # Create training history record
            training_record = TrainingHistory(
                model_id=model_id,
                start_time=datetime.now(),
                status="running",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            session.add(training_record)
            await session.commit()
            await session.refresh(training_record)
            
            logger.info(f"Recorded training start for model {model_id}")
            return training_record.id
    
    async def record_training_completion(
        self, 
        training_id: int, 
        status: str, 
        metrics: Dict[str, Any],
        error_message: Optional[str] = None
    ) -> bool:
        """Record the completion of model training."""
        valid_statuses = ["completed", "failed"]
        if status not in valid_statuses:
            logger.error(f"Invalid status: {status}")
            return False
        
        async with get_db_session() as session:
            query = update(TrainingHistory).where(TrainingHistory.id == training_id).values(
                end_time=datetime.now(),
                status=status,
                metrics=metrics,
                error_message=error_message,
                updated_at=datetime.now()
            )
            await session.execute(query)
            await session.commit()
            
            logger.info(f"Recorded training completion for training {training_id} with status {status}")
            return True
    
    async def record_feature_importance(
        self,
        model_id: int,
        feature_importance: Dict[str, float]
    ) -> bool:
        """Record feature importance for a model."""
        from models.model_management import FeatureImportance
        
        try:
            async with get_db_session() as session:
                # Delete existing feature importance records
                from sqlalchemy import delete
                delete_query = delete(FeatureImportance).where(
                    FeatureImportance.model_id == model_id
                )
                await session.execute(delete_query)
                
                # Create new records
                for feature_name, importance in feature_importance.items():
                    feature_record = FeatureImportance(
                        model_id=model_id,
                        feature_name=feature_name,
                        importance_score=float(importance),
                        created_at=datetime.now()
                    )
                    session.add(feature_record)
                
                await session.commit()
                
                logger.info(f"Recorded feature importance for model {model_id}")
                return True
        
        except Exception as e:
            logger.error(f"Error recording feature importance: {str(e)}")
            return False
    
    async def get_feature_importance(self, model_id: int) -> Dict[str, float]:
        """Get feature importance for a model."""
        from models.model_management import FeatureImportance
        
        async with get_db_session() as session:
            query = select(FeatureImportance).where(
                FeatureImportance.model_id == model_id
            )
            result = await session.execute(query)
            records = result.scalars().all()
            
            return {record.feature_name: record.importance_score for record in records}