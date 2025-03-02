import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from .base_provider import BaseDataProvider
from config import settings

logger = logging.getLogger(__name__)

class AlphaVantageProvider(BaseDataProvider):
    """Data provider implementation for Alpha Vantage API."""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or settings.API_KEY_ALPHA_VANTAGE)
        self.session = None
        self.requests_this_minute = 0
        self.last_request_time = datetime.now()
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
        
    async def _make_request(self, params: Dict[str, str]) -> Dict[str, Any]:
        """Make a request to the Alpha Vantage API with rate limiting."""
        # Add API key to params
        params["apikey"] = self.api_key
        
        # Handle rate limiting (5 requests per minute for free tier)
        now = datetime.now()
        if (now - self.last_request_time).total_seconds() < 60 and self.requests_this_minute >= 5:
            wait_time = 60 - (now - self.last_request_time).total_seconds()
            logger.info(f"Rate limit reached. Waiting {wait_time:.2f} seconds.")
            await asyncio.sleep(wait_time)
            self.requests_this_minute = 0
            self.last_request_time = datetime.now()
        
        # Reset counter if more than a minute has passed
        if (now - self.last_request_time).total_seconds() >= 60:
            self.requests_this_minute = 0
            self.last_request_time = now
        
        # Make the request
        session = await self._get_session()
        async with session.get(self.BASE_URL, params=params) as response:
            self.requests_this_minute += 1
            
            if response.status != 200:
                logger.error(f"Error from Alpha Vantage API: {response.status}")
                return {}
            
            try:
                return await response.json()
            except aiohttp.ContentTypeError:
                logger.error("Invalid JSON response from Alpha Vantage API")
                return {}
    
    async def get_stock_data(
        self, 
        ticker: str, 
        start_date: datetime, 
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve daily stock price data."""
        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": ticker,
            "outputsize": "full" if (datetime.now() - start_date).days > 100 else "compact"
        }
        
        data = await self._make_request(params)
        
        if not data or "Time Series (Daily)" not in data:
            logger.warning(f"No data returned for {ticker}")
            return []
        
        time_series = data["Time Series (Daily)"]
        end_date = end_date or datetime.now()
        
        # Format the response
        result = []
        for date_str, values in time_series.items():
            date = datetime.strptime(date_str, "%Y-%m-%d")
            
            # Filter by date range
            if start_date <= date <= end_date:
                result.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": float(values["1. open"]),
                    "high": float(values["2. high"]),
                    "low": float(values["3. low"]),
                    "close": float(values["4. close"]),
                    "adjusted_close": float(values["5. adjusted close"]),
                    "volume": int(values["6. volume"]),
                    "dividend_amount": float(values["7. dividend amount"]),
                    "split_coefficient": float(values["8. split coefficient"])
                })
        
        return sorted(result, key=lambda x: x["date"])
    
    async def get_stock_info(self, ticker: str) -> Dict[str, Any]:
        """Retrieve overview information for a stock."""
        params = {
            "function": "OVERVIEW",
            "symbol": ticker
        }
        
        data = await self._make_request(params)
        
        if not data or "Symbol" not in data:
            logger.warning(f"No overview data returned for {ticker}")
            return {}
        
        return {
            "ticker": data.get("Symbol", ""),
            "name": data.get("Name", ""),
            "exchange": data.get("Exchange", ""),
            "currency": data.get("Currency", ""),
            "sector": data.get("Sector", ""),
            "industry": data.get("Industry", ""),
            "description": data.get("Description", ""),
            "market_cap": float(data.get("MarketCapitalization", 0)),
            "pe_ratio": float(data.get("PERatio", 0)) if data.get("PERatio") else None,
            "dividend_yield": float(data.get("DividendYield", 0)) if data.get("DividendYield") else None,
            "fifty_two_week_high": float(data.get("52WeekHigh", 0)) if data.get("52WeekHigh") else None,
            "fifty_two_week_low": float(data.get("52WeekLow", 0)) if data.get("52WeekLow") else None
        }
    
    async def search_stocks(self, query: str) -> List[Dict[str, Any]]:
        """Search for stocks matching a query."""
        params = {
            "function": "SYMBOL_SEARCH",
            "keywords": query
        }
        
        data = await self._make_request(params)
        
        if not data or "bestMatches" not in data:
            logger.warning(f"No search results for query: {query}")
            return []
        
        results = []
        for match in data["bestMatches"]:
            results.append({
                "ticker": match.get("1. symbol", ""),
                "name": match.get("2. name", ""),
                "type": match.get("3. type", ""),
                "region": match.get("4. region", ""),
                "market_open": match.get("5. marketOpen", ""),
                "market_close": match.get("6. marketClose", ""),
                "timezone": match.get("7. timezone", ""),
                "currency": match.get("8. currency", ""),
                "match_score": float(match.get("9. matchScore", 0))
            })
        
        return results
    
    async def get_market_indices(self) -> List[Dict[str, Any]]:
        """Get major stock market indices."""
        # Alpha Vantage doesn't have a direct API for indices components
        # This is a simplified implementation
        indices = [
            {"symbol": "^GSPC", "name": "S&P 500", "region": "United States"},
            {"symbol": "^DJI", "name": "Dow Jones Industrial Average", "region": "United States"},
            {"symbol": "^IXIC", "name": "NASDAQ Composite", "region": "United States"},
            {"symbol": "^FTSE", "name": "FTSE 100", "region": "United Kingdom"},
            {"symbol": "^N225", "name": "Nikkei 225", "region": "Japan"}
        ]
        
        return indices
    
    @staticmethod
    def handle_rate_limit() -> None:
        """Handle rate limiting for the Alpha Vantage API."""
        asyncio.sleep(12)  # Simple rate limiting (5 requests per minute = 12 seconds per request)
    
    async def close(self):
        """Close the session."""
        if self.session and not self.session.closed:
            await self.session.close()