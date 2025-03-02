import logging
import asyncio
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

from config import settings
from services.model_registry import ModelRegistry
from services.data_service import DataService
from models.temporal_fusion_transformer import TemporalFusionTransformerImplementation
from models.lstm_model import LSTMImplementation
from models.arima_model import ARIMAImplementation

logger = logging.getLogger(__name__)

class TrainingService:
    """Service for training machine learning models."""
    
    def __init__(self, model_registry: ModelRegistry):
        self.model_registry = model_registry
        self.data_service = DataService()
        
        self.model_implementations = {
            "TemporalFusionTransformer": TemporalFusionTransformerImplementation,
            "LSTM": LSTMImplementation,
            "ARIMA": ARIMAImplementation
            # Add other model implementations as needed
        }
    
    async def train_model(
        self, 
        model_id: int,
        stock_ids: Optional[List[int]] = None
    ) -> Tuple[bool, str]:
        """Train a model with the given ID."""
        try:
            # Get model record
            model = await self.model_registry.get_model(model_id)
            if not model:
                return False, f"Model with ID {model_id} not found"
            
            # Get architecture
            architecture_name = None
            for name, arch in self.model_registry.available_architectures.items():
                if arch.id == model.architecture_id:
                    architecture_name = name
                    break
            
            if not architecture_name:
                return False, f"Architecture with ID {model.architecture_id} not found"
            
            # Check if architecture is supported
            if architecture_name not in self.model_implementations:
                return False, f"Architecture {architecture_name} is not implemented"
            
            # Record training start
            training_id = await self.model_registry.record_training_start(model_id)
            await self.model_registry.update_model_status(model_id, "training")
            
            # Get training data
            train_data, validation_data = await self._prepare_training_data(
                model.training_dataset_config, stock_ids
            )
            
            if not train_data:
                error_msg = "No training data available"
                await self.model_registry.record_training_completion(
                    training_id, "failed", {}, error_msg
                )
                await self.model_registry.update_model_status(model_id, "failed")
                return False, error_msg
            
            # Create model instance
            model_class = self.model_implementations[architecture_name]
            model_instance = model_class(model.hyperparameters, model.feature_config)
            
            # Train model
            logger.info(f"Starting training for model {model_id} ({architecture_name})")
            metrics, feature_importance = await model_instance.train(train_data, validation_data)
            
            # Save model artifact
            model_artifact = model_instance.save()
            model_path = f"{architecture_name}/{model.name}/{model.version}/{datetime.now().strftime('%Y%m%d%H%M%S')}.pkl"
            await self.model_registry.store_model_artifact(model_id, model_artifact, model_path)
            
            # Record feature importance
            if feature_importance:
                await self.model_registry.record_feature_importance(model_id, feature_importance)
            
            # Record training completion
            await self.model_registry.record_training_completion(
                training_id, "completed", metrics
            )
            await self.model_registry.update_model_status(model_id, "ready")
            
            logger.info(f"Completed training for model {model_id}")
            return True, "Training completed successfully"
        
        except Exception as e:
            error_msg = f"Error training model: {str(e)}"
            logger.error(error_msg)
            
            # Record training failure
            if 'training_id' in locals():
                await self.model_registry.record_training_completion(
                    training_id, "failed", {}, error_msg
                )
            
            # Update model status
            await self.model_registry.update_model_status(model_id, "failed")
            
            return False, error_msg
    
    async def _prepare_training_data(
        self, 
        dataset_config: Dict[str, Any],
        stock_ids: Optional[List[int]] = None
    ) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
        """Prepare training and validation data."""
        # Extract configuration
        train_test_split = dataset_config.get("train_test_split", 0.8)
        lookback_window = dataset_config.get("lookback_window", 30)
        forecast_horizon = dataset_config.get("forecast_horizon", 5)
        
        # Determine time range
        end_date = datetime.now()
        
        # We need enough data for both training and validation
        # Plus the lookback window and forecast horizon
        days_needed = int(lookback_window * 1.5) + forecast_horizon * 10
        start_date = end_date - timedelta(days=days_needed)
        
        # Determine stocks to use
        if not stock_ids:
            stocks_config = dataset_config.get("stocks", "all")
            if stocks_config == "all":
                # Get all active stocks
                stock_ids = await self.data_service.get_all_stock_ids()
            elif isinstance(stocks_config, list):
                stock_ids = stocks_config
        
        if not stock_ids:
            logger.error("No stocks specified for training")
            return None, None
        
        # Get data for all stocks
        all_data = []
        
        for stock_id in stock_ids:
            try:
                # Get price data and features for the stock
                stock_data = await self.data_service.get_stock_data_with_features(
                    stock_id, start_date, end_date
                )
                
                if not stock_data.empty:
                    # Add stock_id column
                    stock_data["stock_id"] = stock_id
                    all_data.append(stock_data)
            except Exception as e:
                logger.warning(f"Error getting data for stock {stock_id}: {str(e)}")
        
        if not all_data:
            logger.error("No data available for training")
            return None, None
        
        # Combine all stock data
        combined_data = pd.concat(all_data)
        
        # Sort by date
        combined_data = combined_data.sort_index()
        
        # Split into training and validation
        split_idx = int(len(combined_data) * train_test_split)
        train_data = combined_data.iloc[:split_idx]
        validation_data = combined_data.iloc[split_idx:]
        
        logger.info(f"Prepared training data: {len(train_data)} samples, validation: {len(validation_data)} samples")
        
        return train_data, validation_data