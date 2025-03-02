import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from aiokafka import AIOKafkaProducer

from config import settings
from services.model_registry import ModelRegistry
from services.data_service import DataService
from models.temporal_fusion_transformer import TemporalFusionTransformerImplementation
from models.lstm_model import LSTMImplementation
from models.arima_model import ARIMAImplementation

logger = logging.getLogger(__name__)

class InferenceService:
    """Service for generating predictions from trained models."""
    
    def __init__(self, model_registry: ModelRegistry):
        self.model_registry = model_registry
        self.data_service = DataService()
        self.producer = None
        
        self.model_implementations = {
            "TemporalFusionTransformer": TemporalFusionTransformerImplementation,
            "LSTM": LSTMImplementation,
            "ARIMA": ARIMAImplementation
            # Add other model implementations as needed
        }
    
    async def initialize(self):
        """Initialize the Kafka producer."""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await self.producer.start()
    
    async def close(self):
        """Close connections."""
        if self.producer:
            await self.producer.stop()
    
    async def generate_predictions(
        self, 
        model_id: int,
        stock_id: int,
        save_to_db: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Generate predictions for a stock using a specific model."""
        try:
            # Get model record
            model = await self.model_registry.get_model(model_id)
            if not model:
                logger.error(f"Model with ID {model_id} not found")
                return None
            
            # Check if model is ready
            if model.status != "ready":
                logger.error(f"Model {model_id} is not ready (status: {model.status})")
                return None
            
            # Get architecture
            architecture_name = None
            for name, arch in self.model_registry.available_architectures.items():
                if arch.id == model.architecture_id:
                    architecture_name = name
                    break
            
            if not architecture_name:
                logger.error(f"Architecture with ID {model.architecture_id} not found")
                return None
            
            # Check if architecture is supported
            if architecture_name not in self.model_implementations:
                logger.error(f"Architecture {architecture_name} is not implemented")
                return None
            
            # Load model artifact
            model_artifact, error = await self.model_registry.load_model_artifact(model_id)
            if error:
                logger.error(f"Error loading model artifact: {error}")
                return None
            
            # Create model instance
            model_class = self.model_implementations[architecture_name]
            model_instance = model_class.load(model_artifact)
            
            # Get data for prediction
            lookback_window = model.hyperparameters.get("lookback_window", 30)
            forecast_horizon = model.hyperparameters.get("forecast_horizon", 5)
            
            # We need enough historical data for the lookback window
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_window * 2)  # Get extra data to be safe
            
            # Get features needed for this model
            features = []
            if 'time_varying_features' in model.feature_config:
                features.extend(model.feature_config['time_varying_features'])
            
            if 'static_features' in model.feature_config:
                features.extend(model.feature_config['static_features'])
            
            # Get stock data with features
            stock_data = await self.data_service.get_stock_data_with_features(
                stock_id, start_date, end_date, features
            )
            
            if stock_data.empty:
                logger.error(f"No data available for stock {stock_id}")
                return None
            
            # Generate predictions
            predictions_df = await model_instance.predict(stock_data)
            
            if predictions_df.empty:
                logger.error(f"No predictions generated for stock {stock_id}")
                return None
            
            # Format results
            prediction_data = {
                "model_id": model_id,
                "stock_id": stock_id,
                "prediction_timestamp": datetime.now().isoformat(),
                "predictions": []
            }
            
            for idx, row in predictions_df.iterrows():
                prediction_data["predictions"].append({
                    "target_timestamp": idx.isoformat(),
                    "predicted_value": float(row["predicted_close"]),
                    "confidence_lower": float(row["predicted_close"] * 0.95) if "confidence_lower" not in row else float(row["confidence_lower"]),
                    "confidence_upper": float(row["predicted_close"] * 1.05) if "confidence_upper" not in row else float(row["confidence_upper"])
                })
            
            # Save predictions to database if requested
            if save_to_db:
                await self.data_service.save_predictions(
                    model_id, stock_id, prediction_data["predictions"]
                )
            
            # Send to Kafka for further processing
            if self.producer:
                await self.producer.send_and_wait(
                    settings.KAFKA_PREDICTION_TOPIC,
                    prediction_data
                )
            
            logger.info(f"Generated predictions for stock {stock_id} using model {model_id}")
            return prediction_data
        
        except Exception as e:
            logger.error(f"Error generating predictions: {str(e)}")
            return None
    
    async def generate_batch_predictions(
        self, 
        model_ids: List[int],
        stock_ids: List[int],
        save_to_db: bool = True
    ) -> Dict[str, Any]:
        """Generate predictions for multiple stocks using multiple models."""
        results = {
            "total_predictions": 0,
            "successful_predictions": 0,
            "failed_predictions": 0,
            "details": []
        }
        
        for model_id in model_ids:
            for stock_id in stock_ids:
                try:
                    prediction = await self.generate_predictions(model_id, stock_id, save_to_db)
                    results["total_predictions"] += 1
                    
                    if prediction:
                        results["successful_predictions"] += 1
                        results["details"].append({
                            "model_id": model_id,
                            "stock_id": stock_id,
                            "status": "success",
                            "num_predictions": len(prediction["predictions"])
                        })
                    else:
                        results["failed_predictions"] += 1
                        results["details"].append({
                            "model_id": model_id,
                            "stock_id": stock_id,
                            "status": "failed"
                        })
                
                except Exception as e:
                    results["total_predictions"] += 1
                    results["failed_predictions"] += 1
                    results["details"].append({
                        "model_id": model_id,
                        "stock_id": stock_id,
                        "status": "failed",
                        "error": str(e)
                    })
        
        logger.info(f"Batch prediction completed: {results['successful_predictions']} successful, {results['failed_predictions']} failed")
        return results
    
    async def get_comparison_data(
        self, 
        model_ids: List[int],
        stock_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get comparison data for multiple models for a specific stock."""
        # Get actual price data
        actual_data = await self.data_service.get_stock_price_data(
            stock_id, start_date, end_date
        )
        
        if actual_data.empty:
            logger.error(f"No actual data available for stock {stock_id}")
            return {"error": f"No actual data available for stock {stock_id}"}
        
        # Get predictions for each model
        predictions = {}
        
        for model_id in model_ids:
            model_predictions = await self.data_service.get_predictions(
                model_id, stock_id, start_date, end_date
            )
            
            if not model_predictions.empty:
                predictions[str(model_id)] = model_predictions
        
        if not predictions:
            logger.error(f"No predictions available for stock {stock_id}")
            return {"error": f"No predictions available for stock {stock_id}"}
        
        # Merge actual data with predictions
        comparison_data = []
        
        for date, row in actual_data.iterrows():
            data_point = {
                "date": date.isoformat(),
                "actual": float(row["close"]),
                "predictions": {}
            }
            
            for model_id, model_preds in predictions.items():
                if date in model_preds.index:
                    data_point["predictions"][model_id] = float(model_preds.loc[date, "predicted_value"])
            
            comparison_data.append(data_point)
        
        # Calculate performance metrics
        metrics = await self._calculate_performance_metrics(actual_data, predictions)
        
        return {
            "stock_id": stock_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "comparison_data": comparison_data,
            "metrics": metrics
        }
    
    async def _calculate_performance_metrics(
        self, 
        actual_data: pd.DataFrame,
        predictions: Dict[str, pd.DataFrame]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate performance metrics for each model."""
        metrics = {}
        
        for model_id, model_preds in predictions.items():
            # Merge actual and predicted data
            merged_data = pd.DataFrame({"actual": actual_data["close"]})
            merged_data["predicted"] = np.nan
            
            for date, row in model_preds.iterrows():
                if date in merged_data.index:
                    merged_data.loc[date, "predicted"] = row["predicted_value"]
            
            # Remove rows with missing values
            merged_data = merged_data.dropna()
            
            if len(merged_data) == 0:
                continue
            
            # Calculate metrics
            mae = np.mean(np.abs(merged_data["actual"] - merged_data["predicted"]))
            rmse = np.sqrt(np.mean((merged_data["actual"] - merged_data["predicted"]) ** 2))
            
            # Calculate MAPE (Mean Absolute Percentage Error)
            mape = np.mean(np.abs((merged_data["actual"] - merged_data["predicted"]) / merged_data["actual"])) * 100
            
            # Calculate directional accuracy
            actual_diff = merged_data["actual"].diff()
            predicted_diff = merged_data["predicted"].diff()
            
            # Skip first row (has NaN diff)
            correct_direction = np.sign(actual_diff.iloc[1:]) == np.sign(predicted_diff.iloc[1:])
            directional_accuracy = 100 * np.mean(correct_direction)
            
            # Calculate Sharpe ratio (simplified)
            # Assuming we go long when prediction is up, short when prediction is down
            returns = []
            for i in range(1, len(merged_data)):
                pred_direction = np.sign(predicted_diff.iloc[i])
                actual_return = actual_diff.iloc[i] / merged_data["actual"].iloc[i-1]
                
                if pred_direction == 0:
                    # No position if no change predicted
                    returns.append(0)
                else:
                    # Position based on predicted direction
                    returns.append(pred_direction * actual_return)
            
            sharpe_ratio = 0
            if len(returns) > 0:
                avg_return = np.mean(returns) * 252  # Annualized
                std_return = np.std(returns) * np.sqrt(252)  # Annualized
                
                if std_return > 0:
                    sharpe_ratio = avg_return / std_return
            
            metrics[model_id] = {
                "mae": fl