import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA

from .base_model import BaseModel

class ARIMAImplementation(BaseModel):
    """Implementation of ARIMA model for stock prediction."""
    
    def __init__(self, hyperparameters: Dict[str, Any], feature_config: Dict[str, Any]):
        super().__init__(hyperparameters, feature_config)
        
        # Extract hyperparameters
        self.p = hyperparameters.get("p", 5)
        self.d = hyperparameters.get("d", 1)
        self.q = hyperparameters.get("q", 0)
        
        # Initialize model
        self.model = None
        self.feature_importance_scores = {}
    
    async def train(
        self, 
        train_data: pd.DataFrame,
        validation_data: Optional[pd.DataFrame] = None
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Train the ARIMA model."""
        # ARIMA models typically use only the target variable
        target_col = "close"
        
        # Prepare time series data
        ts_data = train_data[target_col].values
        
        # Fit ARIMA model
        self.model = ARIMA(
            ts_data, 
            order=(self.p, self.d, self.q)
        ).fit()
        
        # Calculate training metrics
        train_pred = self.model.fittedvalues
        train_mse = ((ts_data[self.p+self.d:] - train_pred) ** 2).mean()
        train_rmse = np.sqrt(train_mse)
        
        # Calculate validation metrics if validation data is provided
        val_metrics = {}
        if validation_data is not None:
            val_data = validation_data[target_col].values
            forecast_steps = len(val_data)
            
            # Generate forecasts
            val_pred = self.model.forecast(steps=forecast_steps)
            
            # Calculate validation metrics
            val_mse = ((val_data - val_pred[:len(val_data)]) ** 2).mean()
            val_rmse = np.sqrt(val_mse)
            
            val_metrics = {
                "val_mse": float(val_mse),
                "val_rmse": float(val_rmse)
            }
        
        # No meaningful feature importance for ARIMA
        # ARIMA only uses lagged values of the target variable
        
        # Return metrics
        metrics = {
            "train_mse": float(train_mse),
            "train_rmse": float(train_rmse),
            "p": self.p,
            "d": self.d,
            "q": self.q,
            **val_metrics
        }
        
        return metrics, {}
    
    async def predict(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate predictions using the trained model."""
        if self.model is None:
            raise ValueError("Model has not been trained or loaded")
        
        # Get forecast horizon
        forecast_horizon = self.hyperparameters.get("forecast_horizon", 5)
        
        # Generate forecast
        forecast = self.model.forecast(steps=forecast_horizon)
        
        # Create result DataFrame
        result = pd.DataFrame()
        last_date = data.index[-1]
        
        # Assuming the index is datetime
        for i in range(forecast_horizon):
            next_date = last_date + pd.Timedelta(days=i+1)
            result.loc[next_date, "predicted_close"] = forecast[i]
        
        return result
    
    def save(self) -> Dict[str, Any]:
            """Save the model state for serialization."""
            if self.model is None:
                raise ValueError("Model has not been trained")
            
            # Save model parameters
            return {
                "hyperparameters": self.hyperparameters,
                "feature_config": self.feature_config,
                "model_params": {
                    "params": self.model.params.tolist(),
                    "pvalues": self.model.pvalues.tolist() if hasattr(self.model, 'pvalues') else None,
                    "order": self.model.model.order,
                    "seasonal_order": self.model.model.seasonal_order if hasattr(self.model.model, 'seasonal_order') else None,
                    "sigma2": float(self.model.sigma2) if hasattr(self.model, 'sigma2') else None,
                    "aic": float(self.model.aic) if hasattr(self.model, 'aic') else None,
                    "bic": float(self.model.bic) if hasattr(self.model, 'bic') else None
                }
            }
    
    @classmethod
    def load(cls, saved_model: Dict[str, Any]) -> 'ARIMAImplementation':
        """Load a model from a serialized state."""
        # Create instance
        instance = cls(
            saved_model["hyperparameters"],
            saved_model["feature_config"]
        )
        
        # Create a dummy ARIMA model with the saved parameters
        # Note: This approach recreates the model but doesn't exactly restore the internal state
        # For production use, consider using pickle for ARIMA models
        
        p, d, q = saved_model["model_params"]["order"]
        
        # Create a dummy time series to initialize the model
        dummy_data = np.ones(p + d + q + 5)
        
        # Initialize model
        instance.model = ARIMA(dummy_data, order=(p, d, q)).fit()
        
        # Set the parameters
        instance.model.params = np.array(saved_model["model_params"]["params"])
        
        return instance
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from the model."""
        # ARIMA does not have traditional feature importance
        # Could potentially use coefficient significance (p-values) if needed
        return {}