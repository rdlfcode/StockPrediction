from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

class BaseDataProvider(ABC):
    """Abstract base class for all stock data providers."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    async def get_stock_data(
        self, 
        ticker: str, 
        start_date: datetime, 
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve stock price data for a given ticker and time range.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date for data retrieval
            end_date: End date for data retrieval (defaults to today if None)
            
        Returns:
            List of dictionaries containing price data
        """
        pass
    
    @abstractmethod
    async def get_stock_info(self, ticker: str) -> Dict[str, Any]:
        """
        Retrieve general information about a stock.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary containing stock information
        """
        pass
    
    @abstractmethod
    async def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for stocks based on a query string.
        
        Args:
            query: Search query (ticker, name, etc.)
            
        Returns:
            List of stocks matching the query
        """
        pass
    
    @abstractmethod
    async def get_market_indices(self) -> List[Dict[str, Any]]:
        """
        Retrieve list of major market indices and their components.
        
        Returns:
            List of indices with their component stocks
        """
        pass
    
    @staticmethod
    def handle_rate_limit() -> None:
        """Handle rate limiting for the API."""
        pass