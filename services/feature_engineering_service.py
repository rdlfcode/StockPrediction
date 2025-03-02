import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.stock_data import StockFeatureData, StockPriceData
from db import get_timescale_db_session

logger = logging.getLogger(__name__)

class FeatureEngineeringService:
    """Service for generating engineered features from stock price data."""
    
    def __init__(self):
        self.feature_generators = {
            "simple_moving_average": self._generate_moving_average,
            "exponential_moving_average": self._generate_exponential_moving_average,
            "relative_strength_index": self._generate_rsi,
            "bollinger_bands": self._generate_bollinger_bands,
            "macd": self._generate_macd,
            "rate_of_change": self._generate_rate_of_change,
            "average_true_range": self._generate_atr,
            "stochastic_oscillator": self._generate_stochastic_oscillator,
            "on_balance_volume": self._generate_on_balance_volume,
            "price_channel": self._generate_price_channel
        }
    
    async def generate_features_for_stock(
        self, 
        stock_id: int, 
        start_date: datetime, 
        end_date: Optional[datetime] = None,
        session: Optional[AsyncSession] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate all features for a given stock and time range."""
        end_date = end_date or datetime.now()
        
        # Get price data for the stock
        if session is None:
            async with get_timescale_db_session() as session:
                price_data = await self._get_price_data(stock_id, start_date, end_date, session)
        else:
            price_data = await self._get_price_data(stock_id, start_date, end_date, session)
        
        if not price_data:
            logger.warning(f"No price data found for stock_id {stock_id} in the given time range")
            return {}
        
        # Convert to DataFrame for easier processing
        df = pd.DataFrame([
            {
                "date": pd.Timestamp(row.timestamp),
                "open": row.open,
                "high": row.high,
                "low": row.low,
                "close": row.close,
                "volume": row.volume,
                "adjusted_close": row.adjusted_close
            } for row in price_data
        ])
        
        # Sort by date
        df = df.sort_values("date")
        
        # Generate all features
        features = {}
        for feature_name, generator_func in self.feature_generators.items():
            try:
                feature_df = generator_func(df)
                # Convert back to list of dictionaries
                features[feature_name] = feature_df.to_dict("records")
            except Exception as e:
                logger.error(f"Error generating feature {feature_name}: {str(e)}")
        
        return features
    
    async def _get_price_data(
        self, 
        stock_id: int, 
        start_date: datetime, 
        end_date: datetime,
        session: AsyncSession
    ) -> List[StockPriceData]:
        """Retrieve price data for a stock from the database."""
        # We need more data for lookback periods, so extend start date
        extended_start_date = start_date - timedelta(days=200)  # 200 days for longest lookback
        
        query = select(StockPriceData).where(
            StockPriceData.stock_id == stock_id,
            StockPriceData.timestamp >= extended_start_date,
            StockPriceData.timestamp <= end_date
        ).order_by(StockPriceData.timestamp)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    def _generate_moving_average(self, df: pd.DataFrame, windows: List[int] = [5, 10, 20, 50, 100, 200]) -> pd.DataFrame:
        """Generate simple moving averages for different window sizes."""
        result_df = pd.DataFrame({"date": df["date"]})
        
        for window in windows:
            col_name = f"ma_{window}"
            result_df[col_name] = df["close"].rolling(window=window).mean()
        
        return result_df
    
    def _generate_exponential_moving_average(self, df: pd.DataFrame, windows: List[int] = [5, 10, 20, 50, 100, 200]) -> pd.DataFrame:
        """Generate exponential moving averages for different window sizes."""
        result_df = pd.DataFrame({"date": df["date"]})
        
        for window in windows:
            col_name = f"ema_{window}"
            result_df[col_name] = df["close"].ewm(span=window, adjust=False).mean()
        
        return result_df
    
    def _generate_rsi(self, df: pd.DataFrame, windows: List[int] = [9, 14, 25]) -> pd.DataFrame:
        """Generate Relative Strength Index for different window sizes."""
        result_df = pd.DataFrame({"date": df["date"]})
        
        # Calculate price changes
        delta = df["close"].diff()
        
        for window in windows:
            # Get gains and losses
            gain = delta.copy()
            loss = delta.copy()
            gain[gain < 0] = 0
            loss[loss > 0] = 0
            loss = -loss
            
            # Calculate average gain and loss
            avg_gain = gain.rolling(window=window).mean()
            avg_loss = loss.rolling(window=window).mean()
            
            # Calculate RS and RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            col_name = f"rsi_{window}"
            result_df[col_name] = rsi
        
        return result_df
    
    def _generate_bollinger_bands(self, df: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
        """Generate Bollinger Bands."""
        result_df = pd.DataFrame({"date": df["date"]})
        
        # Calculate middle band (simple moving average)
        middle_band = df["close"].rolling(window=window).mean()
        
        # Calculate standard deviation
        std = df["close"].rolling(window=window).std()
        
        # Calculate upper and lower bands
        upper_band = middle_band + (std * num_std)
        lower_band = middle_band - (std * num_std)
        
        # Store results
        result_df["bb_middle"] = middle_band
        result_df["bb_upper"] = upper_band
        result_df["bb_lower"] = lower_band
        result_df["bb_width"] = (upper_band - lower_band) / middle_band
        
        return result_df
    
    def _generate_macd(
        self, 
        df: pd.DataFrame, 
        fast_period: int = 12, 
        slow_period: int = 26, 
        signal_period: int = 9
    ) -> pd.DataFrame:
        """Generate MACD (Moving Average Convergence Divergence)."""
        result_df = pd.DataFrame({"date": df["date"]})
        
        # Calculate fast and slow EMAs
        ema_fast = df["close"].ewm(span=fast_period, adjust=False).mean()
        ema_slow = df["close"].ewm(span=slow_period, adjust=False).mean()
        
        # Calculate MACD line
        macd_line = ema_fast - ema_slow
        
        # Calculate signal line
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        
        # Calculate histogram
        histogram = macd_line - signal_line
        
        # Store results
        result_df["macd_line"] = macd_line
        result_df["macd_signal"] = signal_line
        result_df["macd_histogram"] = histogram
        
        return result_df
    
    def _generate_rate_of_change(self, df: pd.DataFrame, windows: List[int] = [5, 10, 20]) -> pd.DataFrame:
        """Generate Rate of Change for different window sizes."""
        result_df = pd.DataFrame({"date": df["date"]})
        
        for window in windows:
            # Calculate rate of change as percentage
            roc = ((df["close"] / df["close"].shift(window)) - 1) * 100
            
            col_name = f"roc_{window}"
            result_df[col_name] = roc
        
        return result_df
    
    def _generate_atr(self, df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """Generate Average True Range."""
        result_df = pd.DataFrame({"date": df["date"]})
        
        # Calculate true range
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift()).abs()
        low_close = (df["low"] - df["close"].shift()).abs()
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # Calculate ATR
        atr = true_range.rolling(window=window).mean()
        
        result_df["atr"] = atr
        
        return result_df
    
    def _generate_stochastic_oscillator(
        self, 
        df: pd.DataFrame, 
        k_window: int = 14, 
        d_window: int = 3
    ) -> pd.DataFrame:
        """Generate Stochastic Oscillator."""
        result_df = pd.DataFrame({"date": df["date"]})
        
        # Calculate %K
        lowest_low = df["low"].rolling(window=k_window).min()
        highest_high = df["high"].rolling(window=k_window).max()
        k_percent = 100 * ((df["close"] - lowest_low) / (highest_high - lowest_low))
        
        # Calculate %D (simple moving average of %K)
        d_percent = k_percent.rolling(window=d_window).mean()
        
        result_df["stoch_k"] = k_percent
        result_df["stoch_d"] = d_percent
        
        return result_df
    
    def _generate_on_balance_volume(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate On-Balance Volume."""
        result_df = pd.DataFrame({"date": df["date"]})
        
        # Calculate price direction
        price_direction = np.sign(df["close"].diff())
        
        # Calculate OBV
        obv = (price_direction * df["volume"]).fillna(0).cumsum()
        
        result_df["obv"] = obv
        
        return result_df
    
    def _generate_price_channel(self, df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """Generate Price Channel."""
        result_df = pd.DataFrame({"date": df["date"]})
        
        # Calculate upper channel (highest high)
        upper_channel = df["high"].rolling(window=window).max()
        
        # Calculate lower channel (lowest low)
        lower_channel = df["low"].rolling(window=window).min()
        
        # Calculate middle channel
        middle_channel = (upper_channel + lower_channel) / 2
        
        result_df["pc_upper"] = upper_channel
        result_df["pc_middle"] = middle_channel
        result_df["pc_lower"] = lower_channel
        
        return result_df
    
    async def store_features(
        self, 
        stock_id: int, 
        features: Dict[str, List[Dict[str, Any]]], 
        session: Optional[AsyncSession] = None
    ) -> None:
        """Store generated features in the database."""
        if not features:
            return
        
        use_provided_session = session is not None
        
        if not use_provided_session:
            session = get_timescale_db_session()
        
        try:
            # Flatten features data
            feature_rows = []
            for feature_type, feature_data in features.items():
                for record in feature_data:
                    # Skip records with missing date
                    if "date" not in record:
                        continue
                    
                    date = record["date"]
                    
                    for key, value in record.items():
                        # Skip date column
                        if key == "date":
                            continue
                        
                        # Skip NaN values
                        if pd.isna(value):
                            continue
                        
                        feature_name = f"{feature_type}_{key}" if key != feature_type else feature_type
                        
                        feature_row = StockFeatureData(
                            stock_id=stock_id,
                            timestamp=date if isinstance(date, datetime) else pd.Timestamp(date).to_pydatetime(),
                            feature_name=feature_name,
                            feature_value=float(value),
                            created_at=datetime.now()
                        )
                        
                        feature_rows.append(feature_row)
            
            # Bulk insert features
            if feature_rows:
                session.add_all(feature_rows)
                await session.commit()
                
                logger.info(f"Stored {len(feature_rows)} feature records for stock_id {stock_id}")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error storing features for stock_id {stock_id}: {str(e)}")
            raise
        finally:
            if not use_provided_session:
                await session.close()