import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db_session, get_timescale_db_session
from models.stock_data import Stock, StockPriceData, StockFeatureData
from models.predictions import StockPrediction

logger = logging.getLogger(__name__)

class DataService:
    """Service for retrieving and storing data for model training and inference."""
    
    async def get_all_stock_ids(self) -> List[int]:
        """Get IDs of all active stocks."""
        async with get_db_session() as session:
            query = select(Stock.id).where(Stock.is_active == True)
            result = await session.execute(query)
            return [row[0] for row in result]
    
    async def get_stock_price_data(
        self, 
        stock_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """Get price data for a stock."""
        async with get_timescale_db_session() as session:
            query = select(StockPriceData).where(
                StockPriceData.stock_id == stock_id,
                StockPriceData.timestamp >= start_date,
                StockPriceData.timestamp <= end_date
            ).order_by(StockPriceData.timestamp)
            
            result = await session.execute(query)
            price_data = result.scalars().all()
            
            if not price_data:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame([
                {
                    "timestamp": row.timestamp,
                    "open": row.open,
                    "high": row.high,
                    "low": row.low,
                    "close": row.close,
                    "volume": row.volume,
                    "adjusted_close": row.adjusted_close
                } for row in price_data
            ])
            
            # Set timestamp as index
            df = df.set_index("timestamp")
            
            return df
    
    async def get_stock_features(
        self, 
        stock_id: int,
        start_date: datetime,
        end_date: datetime,
        feature_names: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Get feature data for a stock."""
        async with get_timescale_db_session() as session:
            query = select(StockFeatureData).where(
                StockFeatureData.stock_id == stock_id,
                StockFeatureData.timestamp >= start_date,
                StockFeatureData.timestamp <= end_date
            )
            
            if feature_names:
                # Filter by feature names if provided
                query = query.where(StockFeatureData.feature_name.in_(feature_names))
            
            query = query.order_by(StockFeatureData.timestamp)
            
            result = await session.execute(query)
            feature_data = result.scalars().all()
            
            if not feature_data:
                return pd.DataFrame()
            
            # Convert to wide format DataFrame
            data_dict = {}
            
            for row in feature_data:
                if row.timestamp not in data_dict:
                    data_dict[row.timestamp] = {}
                
                data_dict[row.timestamp][row.feature_name] = row.feature_value
            
            df = pd.DataFrame.from_dict(data_dict, orient="index")
            
            # Fill missing values
            df = df.fillna(method="ffill").fillna(method="bfill")
            
            return df
    
    async def get_stock_data_with_features(
        self, 
        stock_id: int,
        start_date: datetime,
        end_date: datetime,
        features: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Get combined price and feature data for a stock."""
        # Get price data
        price_df = await self.get_stock_price_data(stock_id, start_date, end_date)
        
        if price_df.empty:
            return pd.DataFrame()
        
        # Get feature data
        feature_df = await self.get_stock_features(stock_id, start_date, end_date, features)
        
        if feature_df.empty:
            return price_df
        
        # Merge price and feature data
        merged_df = price_df.join(feature_df, how="left")
        
        # Fill missing feature values
        merged_df = merged_df.fillna(method="ffill").fillna(method="bfill")
        
        return merged_df
    
    async def save_predictions(
        self, 
        model_id: int,
        stock_id: int,
        predictions: List[Dict[str, Any]]
    ) -> bool:
        """Save predictions to the database."""
        try:
            async with get_timescale_db_session() as session:
                # Create prediction records
                prediction_records = []
                
                prediction_timestamp = datetime.now()
                
                for pred in predictions:
                    target_timestamp = datetime.fromisoformat(pred["target_timestamp"])
                    
                    prediction_record = StockPrediction(
                        model_id=model_id,
                        stock_id=stock_id,
                        prediction_timestamp=prediction_timestamp,
                        target_timestamp=target_timestamp,
                        predicted_value=pred["predicted_value"],
                        confidence_lower=pred.get("confidence_lower"),
                        confidence_upper=pred.get("confidence_upper"),
                        created_at=datetime.now()
                    )
                    
                    prediction_records.append(prediction_record)
                
                # Bulk insert
                if prediction_records:
                    session.add_all(prediction_records)
                    await session.commit()
                
                logger.info(f"Saved {len(prediction_records)} predictions for model {model_id}, stock {stock_id}")
                return True
        
        except Exception as e:
            logger.error(f"Error saving predictions: {str(e)}")
            return False
    
    async def get_predictions(
        self, 
        model_id: int,
        stock_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """Get predictions for a stock and model."""
        async with get_timescale_db_session() as session:
            query = select(StockPrediction).where(
                StockPrediction.model_id == model_id,
                StockPrediction.stock_id == stock_id,
                StockPrediction.target_timestamp >= start_date,
                StockPrediction.target_timestamp <= end_date
            ).order_by(StockPrediction.target_timestamp)
            
            result = await session.execute(query)
            predictions = result.scalars().all()
            
            if not predictions:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame([
                {
                    "target_timestamp": row.target_timestamp,
                    "predicted_value": row.predicted_value,
                    "confidence_lower": row.confidence_lower,
                    "confidence_upper": row.confidence_upper,
                    "prediction_timestamp": row.prediction_timestamp
                } for row in predictions
            ])
            
            # Get most recent prediction for each target date
            df = df.sort_values("prediction_timestamp", ascending=False)
            df = df.drop_duplicates(subset=["target_timestamp"], keep="first")
            
            # Set target timestamp as index
            df = df.set_index("target_timestamp")
            
            return df