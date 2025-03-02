import logging
import asyncio
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from aiokafka import AIOKafkaProducer
import json

from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from models.stock_data import Stock, StockPriceData
from db import get_db_session, get_timescale_db_session
from providers.alpha_vantage_provider import AlphaVantageProvider
from config import settings

logger = logging.getLogger(__name__)

class StockDataService:
    """Service for managing stock data."""
    
    def __init__(self):
        self.alpha_vantage = AlphaVantageProvider()
        self.producer = None
    
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
        await self.alpha_vantage.close()
    
    async def get_stock_by_ticker(self, ticker: str) -> Optional[Stock]:
        """Get a stock by its ticker symbol."""
        async with get_db_session() as session:
            query = select(Stock).where(Stock.ticker == ticker)
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    async def get_stock_by_id(self, stock_id: int) -> Optional[Stock]:
        """Get a stock by its ID."""
        async with get_db_session() as session:
            query = select(Stock).where(Stock.id == stock_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    async def get_all_stocks(self, active_only: bool = True) -> List[Stock]:
        """Get all stocks."""
        async with get_db_session() as session:
            query = select(Stock)
            if active_only:
                query = query.where(Stock.is_active == True)
            result = await session.execute(query)
            return result.scalars().all()
    
    async def get_stocks_by_sector(self, sector: str) -> List[Stock]:
        """Get stocks by sector."""
        async with get_db_session() as session:
            query = select(Stock).where(Stock.sector == sector, Stock.is_active == True)
            result = await session.execute(query)
            return result.scalars().all()
    
    async def add_stock(self, ticker: str) -> Union[Stock, None]:
        """Add a new stock to the database."""
        # Get stock info from Alpha Vantage
        stock_info = await self.alpha_vantage.get_stock_info(ticker)
        
        if not stock_info:
            logger.warning(f"Could not retrieve info for ticker {ticker}")
            return None
        
        async with get_db_session() as session:
            try:
                new_stock = Stock(
                    ticker=stock_info.get("ticker", "").upper(),
                    name=stock_info.get("name", ""),
                    sector=stock_info.get("sector", ""),
                    industry=stock_info.get("industry", ""),
                    market_cap=stock_info.get("market_cap", 0),
                    exchange=stock_info.get("exchange", ""),
                    is_active=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                session.add(new_stock)
                await session.commit()
                await session.refresh(new_stock)
                
                logger.info(f"Added new stock: {new_stock.ticker} ({new_stock.name})")
                return new_stock
            except IntegrityError:
                await session.rollback()
                # Stock might already exist, let's update it
                query = update(Stock).where(Stock.ticker == ticker).values(
                    name=stock_info.get("name", ""),
                    sector=stock_info.get("sector", ""),
                    industry=stock_info.get("industry", ""),
                    market_cap=stock_info.get("market_cap", 0),
                    exchange=stock_info.get("exchange", ""),
                    is_active=True,
                    updated_at=datetime.now()
                )
                await session.execute(query)
                await session.commit()
                
                # Get the updated stock
                query = select(Stock).where(Stock.ticker == ticker)
                result = await session.execute(query)
                updated_stock = result.scalar_one_or_none()
                
                logger.info(f"Updated existing stock: {ticker}")
                return updated_stock
            except Exception as e:
                await session.rollback()
                logger.error(f"Error adding stock {ticker}: {str(e)}")
                return None
    
    async def import_market_index(self, index_symbol: str) -> List[Stock]:
        """Import all stocks from a market index."""
        # This would be expanded with actual API calls to get index components
        # For now, we'll simulate with some sample stocks
        
        # Map of index symbols to sample stocks for demonstration
        index_components = {
            "sp500": [
                "AAPL", "MSFT", "AMZN", "GOOGL", "FB", 
                "TSLA", "BRK.B", "JPM", "JNJ", "V"
            ],
            "nasdaq100": [
                "AAPL", "MSFT", "AMZN", "GOOGL", "FB",
                "TSLA", "NVDA", "PYPL", "INTC", "CMCSA"
            ],
            "dow30": [
                "AAPL", "MSFT", "JPM", "V", "HD",
                "DIS", "MCD", "AMGN", "BA", "CAT"
            ]
        }
        
        # Get tickers for the requested index
        if index_symbol.lower() not in index_components:
            logger.warning(f"Unknown index: {index_symbol}")
            return []
        
        tickers = index_components[index_symbol.lower()]
        added_stocks = []
        
        for ticker in tickers:
            try:
                stock = await self.add_stock(ticker)
                if stock:
                    added_stocks.append(stock)
            except Exception as e:
                logger.error(f"Error adding stock {ticker} from index {index_symbol}: {str(e)}")
        
        logger.info(f"Imported {len(added_stocks)} stocks from index {index_symbol}")
        return added_stocks
    
    async def import_historical_data(
        self, 
        stock_id: int, 
        days: int = 365
    ) -> Dict[str, Any]:
        """Import historical data for a stock."""
        # Get the stock
        stock = await self.get_stock_by_id(stock_id)
        if not stock:
            logger.warning(f"Stock with ID {stock_id} not found")
            return {"success": False, "message": f"Stock with ID {stock_id} not found"}
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get historical data
        price_data = await self.alpha_vantage.get_stock_data(stock.ticker, start_date, end_date)
        
        if not price_data:
            logger.warning(f"No historical data found for {stock.ticker}")
            return {"success": False, "message": f"No historical data found for {stock.ticker}"}
        
        # Store data in TimescaleDB
        async with get_timescale_db_session() as session:
            try:
                for data_point in price_data:
                    price_record = StockPriceData(
                        stock_id=stock_id,
                        timestamp=datetime.strptime(data_point["date"], "%Y-%m-%d"),
                        open=data_point["open"],
                        high=data_point["high"],
                        low=data_point["low"],
                        close=data_point["close"],
                        volume=data_point["volume"],
                        adjusted_close=data_point["adjusted_close"],
                        data_source="alpha_vantage",
                        created_at=datetime.now()
                    )
                    session.add(price_record)
                
                await session.commit()
                
                # Send data to Kafka for further processing
                if self.producer:
                    await self.producer.send_and_wait(
                        settings.KAFKA_PRICE_DATA_TOPIC,
                        {
                            "stock_id": stock_id,
                            "ticker": stock.ticker,
                            "data_source": "alpha_vantage",
                            "data_points": len(price_data),
                            "start_date": start_date.isoformat(),
                            "end_date": end_date.isoformat()
                        }
                    )
                
                logger.info(f"Imported {len(price_data)} historical data points for {stock.ticker}")
                return {
                    "success": True, 
                    "message": f"Imported {len(price_data)} historical data points",
                    "stock_id": stock_id,
                    "ticker": stock.ticker,
                    "data_points": len(price_data)
                }
            except Exception as e:
                await session.rollback()
                logger.error(f"Error importing historical data for {stock.ticker}: {str(e)}")
                return {"success": False, "message": f"Error: {str(e)}"}
    
    async def get_latest_price_data(self, stock_id: int) -> Dict[str, Any]:
        """Get the latest price data for a stock."""
        async with get_timescale_db_session() as session:
            query = select(StockPriceData).where(
                StockPriceData.stock_id == stock_id
            ).order_by(StockPriceData.timestamp.desc()).limit(1)
            
            result = await session.execute(query)
            latest_data = result.scalar_one_or_none()
            
            if not latest_data:
                return {}
            
            return {
                "stock_id": latest_data.stock_id,
                "timestamp": latest_data.timestamp.isoformat(),
                "open": latest_data.open,
                "high": latest_data.high,
                "low": latest_data.low,
                "close": latest_data.close,
                "volume": latest_data.volume,
                "adjusted_close": latest_data.adjusted_close
            }
    
    async def import_latest_data_for_all_stocks(self) -> Dict[str, Any]:
        """Import the latest data for all active stocks."""
        stocks = await self.get_all_stocks(active_only=True)
        
        results = {
            "total": len(stocks),
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        for stock in stocks:
            try:
                # Get the latest data point in the database
                latest_data = await self.get_latest_price_data(stock.id)
                
                # Set the start date to the day after the latest data point
                # or to yesterday if no data is available
                if latest_data:
                    start_date = datetime.fromisoformat(latest_data["timestamp"]) + timedelta(days=1)
                else:
                    start_date = datetime.now() - timedelta(days=1)
                
                # Get data from Alpha Vantage
                end_date = datetime.now()
                price_data = await self.alpha_vantage.get_stock_data(stock.ticker, start_date, end_date)
                
                if not price_data:
                    results["failed"] += 1
                    results["details"].append({
                        "stock_id": stock.id,
                        "ticker": stock.ticker,
                        "success": False,
                        "message": "No new data available"
                    })
                    continue
                
                # Store data in TimescaleDB
                async with get_timescale_db_session() as session:
                    for data_point in price_data:
                        price_record = StockPriceData(
                            stock_id=stock.id,
                            timestamp=datetime.strptime(data_point["date"], "%Y-%m-%d"),
                            open=data_point["open"],
                            high=data_point["high"],
                            low=data_point["low"],
                            close=data_point["close"],
                            volume=data_point["volume"],
                            adjusted_close=data_point["adjusted_close"],
                            data_source="alpha_vantage",
                            created_at=datetime.now()
                        )
                        session.add(price_record)
                    
                    await session.commit()
                
                # Send data to Kafka for further processing
                if self.producer:
                    await self.producer.send_and_wait(
                        settings.KAFKA_PRICE_DATA_TOPIC,
                        {
                            "stock_id": stock.id,
                            "ticker": stock.ticker,
                            "data_source": "alpha_vantage",
                            "data_points": len(price_data),
                            "start_date": start_date.isoformat(),
                            "end_date": end_date.isoformat()
                        }
                    )
                
                results["success"] += 1
                results["details"].append({
                    "stock_id": stock.id,
                    "ticker": stock.ticker,
                    "success": True,
                    "data_points": len(price_data)
                })
                
                logger.info(f"Imported {len(price_data)} new data points for {stock.ticker}")
                
                # Rate limiting
                await asyncio.sleep(12)  # Sleep to respect API rate limits
                
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "stock_id": stock.id,
                    "ticker": stock.ticker,
                    "success": False,
                    "message": str(e)
                })
                logger.error(f"Error importing latest data for {stock.ticker}: {str(e)}")
        
        return results