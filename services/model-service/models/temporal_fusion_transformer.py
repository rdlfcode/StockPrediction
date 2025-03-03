import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .base_model import BaseModel

class TemporalFusionTransformerImplementation(BaseModel):
    """Implementation of the Temporal Fusion Transformer model."""
    
    def __init__(self, hyperparameters: Dict[str, Any], feature_config: Dict[str, Any]):
        super().__init__(hyperparameters, feature_config)
        
        # Extract hyperparameters
        self.hidden_dim = hyperparameters.get("hidden_dim", 64)
        self.num_heads = hyperparameters.get("num_heads", 4)
        self.dropout = hyperparameters.get("dropout", 0.1)
        self.learning_rate = hyperparameters.get("learning_rate", 0.001)
        self.batch_size = hyperparameters.get("batch_size", 64)
        self.num_epochs = hyperparameters.get("epochs", 50)
        
        # Extract feature configuration
        self.static_features = feature_config.get("static_features", [])
        self.time_varying_features = feature_config.get("time_varying_features", [])
        
        # Set device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Initialize model
        self.model = None
        self.feature_importance_scores = {}
    
    async def train(
        self, 
        train_data: pd.DataFrame,
        validation_data: Optional[pd.DataFrame] = None
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Train the TFT model."""
        # Prepare static feature data (if any)
        static_data = None
        if self.static_features and len(self.static_features) > 0:
            # Assuming first row contains static features for the stock
            static_data = train_data[self.static_features].iloc[0].values
            static_data = torch.tensor(static_data, dtype=torch.float32).to(self.device)
        
        # Prepare time series data
        lookback_window = self.hyperparameters.get("lookback_window", 30)
        forecast_horizon = self.hyperparameters.get("forecast_horizon", 5)
        
        # Prepare training data
        X_train, y_train = self.prepare_time_series_data(
            train_data, 
            self.time_varying_features, 
            "close", 
            lookback_window, 
            forecast_horizon
        )
        
        # Prepare validation data if provided
        X_val, y_val = None, None
        if validation_data is not None:
            X_val, y_val = self.prepare_time_series_data(
                validation_data, 
                self.time_varying_features, 
                "close", 
                lookback_window, 
                forecast_horizon
            )
        
        # Convert to PyTorch tensors
        X_train = torch.tensor(X_train, dtype=torch.float32).to(self.device)
        y_train = torch.tensor(y_train, dtype=torch.float32).to(self.device)
        
        if X_val is not None and y_val is not None:
            X_val = torch.tensor(X_val, dtype=torch.float32).to(self.device)
            y_val = torch.tensor(y_val, dtype=torch.float32).to(self.device)
        
        # Create data loaders
        train_dataset = torch.utils.data.TensorDataset(X_train, y_train)
        train_loader = torch.utils.data.DataLoader(
            train_dataset, batch_size=self.batch_size, shuffle=True
        )
        
        # Initialize model
        num_time_varying_features = len(self.time_varying_features)
        num_static_features = len(self.static_features)
        
        self.model = TemporalFusionTransformerModel(
            num_static_features=num_static_features,
            num_time_varying_features=num_time_varying_features,
            hidden_dim=self.hidden_dim,
            num_heads=self.num_heads,
            dropout=self.dropout,
            forecast_horizon=forecast_horizon
        ).to(self.device)
        
        # Initialize optimizer
        optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        
        # Initialize loss function
        criterion = nn.MSELoss()
        
        # Training loop
        self.model.train()
        best_val_loss = float('inf')
        metrics = {"train_loss": [], "val_loss": []}
        
        for epoch in range(self.num_epochs):
            epoch_loss = 0.0
            
            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                
                # Create dummy static features if none provided
                batch_static = None
                if static_data is not None:
                    batch_static = static_data.unsqueeze(0).repeat(batch_X.size(0), 1)
                
                # Forward pass
                outputs = self.model(batch_static, batch_X, None)  # No decoder inputs for training
                
                # Calculate loss
                loss = criterion(outputs, batch_y)
                
                # Backward pass and optimize
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
            
            avg_epoch_loss = epoch_loss / len(train_loader)
            metrics["train_loss"].append(avg_epoch_loss)
            
            # Validate if validation data is provided
            if X_val is not None and y_val is not None:
                self.model.eval()
                with torch.no_grad():
                    val_static = None
                    if static_data is not None:
                        val_static = static_data.unsqueeze(0).repeat(X_val.size(0), 1)
                    
                    val_outputs = self.model(val_static, X_val, None)
                    val_loss = criterion(val_outputs, y_val).item()
                    metrics["val_loss"].append(val_loss)
                    
                    # Save best model
                    if val_loss < best_val_loss:
                        best_val_loss = val_loss
                        best_model_state = {
                            "model_state_dict": self.model.state_dict(),
                            "optimizer_state_dict": optimizer.state_dict(),
                            "epoch": epoch,
                            "val_loss": val_loss
                        }
                
                self.model.train()
        
        # Load best model if validation was used
        if X_val is not None and y_val is not None and 'best_model_state' in locals():
            self.model.load_state_dict(best_model_state["model_state_dict"])
        
        # Calculate feature importance
        self.calculate_feature_importance(X_train, y_train)
        
        # Return metrics and feature importance
        final_metrics = {
            "train_loss": metrics["train_loss"][-1],
            "val_loss": metrics["val_loss"][-1] if "val_loss" in metrics and len(metrics["val_loss"]) > 0 else None,
            "num_epochs": self.num_epochs,
            "batch_size": self.batch_size,
            "learning_rate": self.learning_rate
        }
        
        return final_metrics, self.feature_importance_scores
    
    async def predict(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate predictions using the trained model."""
        if self.model is None:
            raise ValueError("Model has not been trained or loaded")
        
        # Prepare static feature data (if any)
        static_data = None
        if self.static_features and len(self.static_features) > 0:
            # Assuming first row contains static features for the stock
            static_data = data[self.static_features].iloc[0].values
            static_data = torch.tensor(static_data, dtype=torch.float32).to(self.device)
        
        # Prepare time series data
        lookback_window = self.hyperparameters.get("lookback_window", 30)
        forecast_horizon = self.hyperparameters.get("forecast_horizon", 5)
        
        # Get the latest window of data for prediction
        if len(data) < lookback_window:
            raise ValueError(f"Not enough data for prediction. Need at least {lookback_window} data points.")
        
        latest_window = data.iloc[-lookback_window:][self.time_varying_features].values
        latest_window = np.expand_dims(latest_window, axis=0)  # Add batch dimension
        latest_window = torch.tensor(latest_window, dtype=torch.float32).to(self.device)
        
        # Set model to evaluation mode
        self.model.eval()
        
        # Generate prediction
        with torch.no_grad():
            static_input = None
            if static_data is not None:
                static_input = static_data.unsqueeze(0)  # Add batch dimension
            
            prediction = self.model(static_input, latest_window, None)
            prediction = prediction.cpu().numpy()[0]  # Remove batch dimension
        
        # Create result DataFrame
        result = pd.DataFrame()
        last_date = data.index[-1]
        
        # Assuming the index is datetime
        for i in range(forecast_horizon):
            next_date = last_date + pd.Timedelta(days=i+1)
            result.loc[next_date, "predicted_close"] = prediction[i]
        
        return result
    
    def save(self) -> Dict[str, Any]:
        """Save the model state for serialization."""
        if self.model is None:
            raise ValueError("Model has not been trained")
        
        return {
            "model_state_dict": self.model.state_dict(),
            "hyperparameters": self.hyperparameters,
            "feature_config": self.feature_config,
            "feature_importance": self.feature_importance_scores
        }
    
    @classmethod
    def load(cls, saved_model: Dict[str, Any]) -> 'TemporalFusionTransformerImplementation':
        """Load a model from a serialized state."""
        # Create instance
        instance = cls(
            saved_model["hyperparameters"],
            saved_model["feature_config"]
        )
        
        # Extract parameters
        num_static_features = len(instance.static_features)
        num_time_varying_features = len(instance.time_varying_features)
        hidden_dim = instance.hidden_dim
        num_heads = instance.num_heads
        dropout = instance.dropout
        forecast_horizon = instance.hyperparameters.get("forecast_horizon", 5)
        
        # Initialize model
        instance.model = TemporalFusionTransformerImplementation(
            num_static_features=num_static_features,
            num_time_varying_features=num_time_varying_features,
            hidden_dim=hidden_dim,
            num_heads=num_heads,
            dropout=dropout,
            forecast_horizon=forecast_horizon
        ).to(instance.device)
        
        # Load state dict
        instance.model.load_state_dict(saved_model["model_state_dict"])
        instance.model.eval()
        
        # Load feature importance
        instance.feature_importance_scores = saved_model["feature_importance"]
        
        return instance
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from the model."""
        return self.feature_importance_scores
    
    def calculate_feature_importance(self, X: torch.Tensor, y: torch.Tensor) -> None:
        """Calculate feature importance for the model."""
        # For TFT, we can use the attention weights as a proxy for feature importance
        # This is a simplified implementation
        
        self.model.eval()
        with torch.no_grad():
            # Get a sample batch
            if X.shape[0] > 100:
                sample_X = X[:100]
                sample_y = y[:100]
            else:
                sample_X = X
                sample_y = y
            
            # Create dummy static features if none provided
            sample_static = None
            if self.static_features and len(self.static_features) > 0:
                # Create a dummy static tensor
                sample_static = torch.zeros(
                    (sample_X.size(0), len(self.static_features)), 
                    dtype=torch.float32
                ).to(self.device)
            
            # Forward pass to get attention weights
            _, attn_weights = self.model(sample_static, sample_X, None, return_attention=True)
            
            # Average attention weights across heads and time steps
            avg_attn = attn_weights.mean(dim=(0, 1))
            
            # Normalize to sum to 1
            if avg_attn.sum() > 0:
                avg_attn = avg_attn / avg_attn.sum()
            
            # Map to feature names
            for i, feature in enumerate(self.time_varying_features):
                self.feature_importance_scores[feature] = float(avg_attn[i].cpu())
    
    @staticmethod
    def prepare_time_series_data(
        df: pd.DataFrame,
        features: List[str],
        target: str,
        lookback_window: int,
        forecast_horizon: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare time series data for the TFT model."""
        X, y = BaseModel.prepare_data(df, features, target, lookback_window, forecast_horizon)
        return X, y