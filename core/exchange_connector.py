"""
Exchange Connector with intelligent error handling and retry logic
Connects to multiple exchanges and fetches market data
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


class ExchangeError(Exception):
    """Base exception for exchange errors"""
    pass


class RateLimitError(ExchangeError):
    """Rate limit exceeded"""
    pass


class ConnectionError(ExchangeError):
    """Connection failed"""
    pass


class ExchangeConnector:
    """
    Intelligent exchange connector with error handling and retry logic
    """
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.exchanges = {}
        self.last_request_time = {}
        self.rate_limits = {}
        self.error_counts = {}
        self.uptime_stats = {}
        
    async def retry_with_backoff(self, func, *args, **kwargs):
        """
        Retry function with exponential backoff
        
        Args:
            func: Function to retry
            *args, **kwargs: Arguments for function
            
        Returns:
            Function result
            
        Raises:
            ExchangeError: If all retries fail
        """
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except RateLimitError as e:
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Rate limit hit, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    raise
            except ConnectionError as e:
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Connection error, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    raise
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise ExchangeError(f"Failed after {self.max_retries} attempts: {e}")
    
    async def check_rate_limit(self, exchange: str):
        """
        Check and enforce rate limits
        
        Args:
            exchange: Exchange name
        """
        if exchange not in self.rate_limits:
            self.rate_limits[exchange] = {'requests_per_second': 10}
            
        if exchange in self.last_request_time:
            time_since_last = (datetime.now() - self.last_request_time[exchange]).total_seconds()
            min_interval = 1.0 / self.rate_limits[exchange]['requests_per_second']
            
            if time_since_last < min_interval:
                await asyncio.sleep(min_interval - time_since_last)
                
        self.last_request_time[exchange] = datetime.now()
    
    async def fetch_ticker(self, exchange: str, symbol: str) -> Optional[Dict]:
        """
        Fetch ticker data for a symbol from an exchange
        
        Args:
            exchange: Exchange name
            symbol: Trading symbol (e.g., 'BTC/USDT')
            
        Returns:
            Ticker data dict or None if error
        """
        async def _fetch():
            await self.check_rate_limit(exchange)
            
            # Simulate API call with occasional errors
            if random.random() < 0.05:  # 5% error rate
                raise ConnectionError(f"Simulated connection error for {exchange}")
                
            if random.random() < 0.02:  # 2% rate limit
                raise RateLimitError(f"Rate limit exceeded for {exchange}")
            
            # Simulate realistic price data
            base_prices = {
                'BTC/USDT': 65000,
                'ETH/USDT': 3200,
                'BNB/USDT': 580,
                'SOL/USDT': 145,
                'ADA/USDT': 0.45,
                'ETH/BTC': 0.049,
                'BNB/BTC': 0.0089,
                'BNB/ETH': 0.181,
            }
            
            if symbol not in base_prices:
                return None
                
            base_price = base_prices[symbol]
            
            # Add exchange-specific variance
            exchange_variance = {
                'Binance': 0.002,
                'Coinbase': 0.015,
                'Kraken': 0.008,
                'KuCoin': 0.012,
                'Bitfinex': 0.005,
            }
            
            variance = exchange_variance.get(exchange, 0.002)
            price = base_price * (1 + random.uniform(-variance, variance))
            
            return {
                'symbol': symbol,
                'last': price,
                'bid': price * 0.9998,
                'ask': price * 1.0002,
                'volume': random.uniform(10000, 1000000),
                'timestamp': datetime.now(),
            }
        
        try:
            result = await self.retry_with_backoff(_fetch)
            self.error_counts[exchange] = self.error_counts.get(exchange, 0)
            return result
        except Exception as e:
            self.error_counts[exchange] = self.error_counts.get(exchange, 0) + 1
            logger.error(f"Failed to fetch {symbol} from {exchange}: {e}")
            return None
    
    async def fetch_multiple_tickers(self, exchange: str, symbols: List[str]) -> Dict[str, Dict]:
        """
        Fetch multiple tickers from an exchange
        
        Args:
            exchange: Exchange name
            symbols: List of symbols
            
        Returns:
            Dict of {symbol: ticker_data}
        """
        tasks = [self.fetch_ticker(exchange, symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        tickers = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, dict):
                tickers[symbol] = result
                
        return tickers
    
    async def fetch_all_exchanges(self, symbols: List[str]) -> Dict[str, Dict[str, Dict]]:
        """
        Fetch data from all exchanges
        
        Args:
            symbols: List of symbols to fetch
            
        Returns:
            Dict of {exchange: {symbol: ticker_data}}
        """
        exchanges = ['Binance', 'Coinbase', 'Kraken', 'KuCoin', 'Bitfinex']
        
        tasks = []
        for exchange in exchanges:
            tasks.append(self.fetch_multiple_tickers(exchange, symbols))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_data = {}
        for exchange, result in zip(exchanges, results):
            if isinstance(result, dict):
                all_data[exchange] = result
            else:
                logger.error(f"Failed to fetch from {exchange}: {result}")
                all_data[exchange] = {}
                
        return all_data
    
    def get_exchange_prices(self, all_data: Dict) -> Dict[str, Dict[str, float]]:
        """
        Extract prices from ticker data
        
        Args:
            all_data: All exchange data
            
        Returns:
            Dict of {exchange: {asset: price}}
        """
        prices = {}
        
        for exchange, symbols_data in all_data.items():
            prices[exchange] = {}
            for symbol, ticker in symbols_data.items():
                if ticker and 'last' in ticker:
                    # Extract base asset (e.g., BTC from BTC/USDT)
                    asset = symbol.split('/')[0]
                    prices[exchange][asset] = ticker['last']
                    
        return prices
    
    def get_pair_prices(self, all_data: Dict) -> Dict[str, Dict[str, float]]:
        """
        Extract trading pair prices
        
        Args:
            all_data: All exchange data
            
        Returns:
            Dict of {exchange: {pair: price}}
        """
        pair_prices = {}
        
        for exchange, symbols_data in all_data.items():
            pair_prices[exchange] = {}
            for symbol, ticker in symbols_data.items():
                if ticker and 'last' in ticker:
                    pair_prices[exchange][symbol] = ticker['last']
                    
        return pair_prices
    
    def get_health_status(self) -> Dict[str, Dict]:
        """
        Get health status of all exchanges
        
        Returns:
            Dict of health metrics per exchange
        """
        status = {}
        
        for exchange in ['Binance', 'Coinbase', 'Kraken', 'KuCoin', 'Bitfinex']:
            errors = self.error_counts.get(exchange, 0)
            total_requests = max(errors + 100, 100)  # Estimate
            success_rate = (total_requests - errors) / total_requests * 100
            
            status[exchange] = {
                'status': 'healthy' if success_rate > 95 else 'degraded' if success_rate > 80 else 'unhealthy',
                'success_rate': success_rate,
                'error_count': errors,
                'last_request': self.last_request_time.get(exchange, datetime.now()),
            }
            
        return status
