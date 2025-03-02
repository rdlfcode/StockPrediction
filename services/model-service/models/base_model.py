from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime

class BaseModel(ABC):
    """Base class for all stock prediction models."""
    
    def __init__(self, hyperparameters: Dict[str, Any], feature_config: Dict[str, Any]):
        self.hyperparameters = hyperparameters
        self.feature_config = feature_config
        self.model = None
    
    @abstractmethod
    async def train(
        self, 
        train_data: pd.DataFrame,
        validation_data: Optional[pd.DataFrame] = None
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        Train the model on the given data.
        
        Args:
            train_data: Training data
            validation_data: Validation data
            
        Returns:
            Tuple of training metrics and feature importance
        """
        pass
    
    @abstractmethod
    async def predict(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate predictions for the given data.
        
        Args:
            data: Input data for prediction
            
        Returns:
            DataFrame with predictions
        """
        pass
    
    @abstractmethod
    def save(self) -> Any:
        """
        Save the model to be serialized.
        
        Returns:
            Serializable model object
        """
        pass
    
    @classmethod
    @abstractmethod
    def load(cls, saved_model: Any) -> 'BaseModel':
        """
        Load a model from a serialized object.
        
        Args:
            saved_model: Serialized model object
            
        Returns:
            Loaded model instance
        """
        pass
    
    @abstractmethod
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance from the trained model.
        
        Returns:
            Dictionary mapping feature names to importance scores
        """
        pass

    @staticmethod
    def prepare_data(
        df: pd.DataFrame,
        features: List[str],
        target: str,
        lookback_window: int,
        forecast_horizon: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare data with sliding window for time series prediction.
        
        Args:
            df: DataFrame with time series data
            features: List of feature columns to use
            target: Target column name
            lookback_window: Number of past time steps to use
            forecast_horizon: Number of future time steps to predict
            
        Returns:
            Tuple of (X, y) arrays for model training/prediction
        """
        X, y = [], []
        
        for i in range(len(df) - lookback_window - forecast_horizon + 1):
            # Input window
            X_window = df.iloc[i:i+lookback_window][features].values
            
            # Target window
            y_window = df.iloc[i+lookback_window:i+lookback_window+forecast_horizon][target].values
            
            X.append(X_window)
            y.append(y_window)
        
        return np.array(X), np.array(y)