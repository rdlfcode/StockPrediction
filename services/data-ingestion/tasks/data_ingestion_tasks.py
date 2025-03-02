import asyncio
import logging
from datetime import datetime, timedelta

from config import settings
from services.stock_data_service import StockDataService
from services.feature_engineering_service import FeatureEngineeringService

logger = logging.getLogger(__name__)

async def start_scheduled_data_ingestion():
    """Start scheduled data ingestion tasks."""
    stock_service = StockDataService()
    feature_service = FeatureEngineeringService()
    
    try:
        await stock_service.initialize()
        
        while True:
            try:
                # Import latest data for all stocks
                logger.info("Starting scheduled data import")
                results = await stock_service.import_latest_data_for_all_stocks()
                logger.info(f"Completed data import: {results['success']} succeeded, {results['failed']} failed")
                
                # Generate features for stocks with new data
                for detail in results["details"]:
                    if detail["success"] and detail.get("data_points", 0) > 0:
                        # Get 60 days of data for feature calculation
                        end_date = datetime.now()
                        start_date = end_date - timedelta(days=60)
                        
                        logger.info(f"Generating features for {detail['ticker']} (ID: {detail['stock_id']})")
                        features = await feature_service.generate_features_for_stock(
                            detail["stock_id"], start_date, end_date
                        )
                        
                        if features:
                            await feature_service.store_features(detail["stock_id"], features)
                            logger.info(f"Stored features for {detail['ticker']}")
                
                # Wait for the next scheduled run
                logger.info(f"Waiting {settings.DATA_FETCH_INTERVAL_MINUTES} minutes for next data import")
                await asyncio.sleep(settings.DATA_FETCH_INTERVAL_MINUTES * 60)
                
            except Exception as e:
                logger.error(f"Error in scheduled data ingestion: {str(e)}")
                # Wait before retrying
                await asyncio.sleep(300)  # 5 minutes
    
    except Exception as e:
        logger.error(f"Failed to start scheduled data ingestion: {str(e)}")
    finally:
        await stock_service.close()

async def import_historical_data_for_all_stocks():
    """Import historical data for all stocks."""
    stock_service = StockDataService()
    feature_service = FeatureEngineeringService()
    
    try:
        await stock_service.initialize()
        
        # Get all active stocks
        stocks = await stock_service.get_all_stocks(active_only=True)
        logger.info(f"Importing historical data for {len(stocks)} stocks")
        
        for stock in stocks:
            try:
                # Import historical data
                logger.info(f"Importing historical data for {stock.ticker} (ID: {stock.id})")
                result = await stock_service.import_historical_data(
                    stock.id, days=settings.HISTORICAL_DATA_DAYS
                )
                
                if result["success"]:
                    # Generate features
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=settings.HISTORICAL_DATA_DAYS)
                    
                    logger.info(f"Generating features for {stock.ticker}")
                    features = await feature_service.generate_features_for_stock(
                        stock.id, start_date, end_date
                    )
                    
                    if features:
                        await feature_service.store_features(stock.id, features)
                        logger.info(f"Stored features for {stock.ticker}")
                
                # Rate limiting
                await asyncio.sleep(12)  # Sleep to respect API rate limits
                
            except Exception as e:
                logger.error(f"Error processing {stock.ticker}: {str(e)}")
        
        logger.info("Completed historical data import for all stocks")
    
    except Exception as e:
        logger.error(f"Failed to import historical data: {str(e)}")
    finally:
        await stock_service.close()