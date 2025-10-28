"""
Real Exchange Integration using CCXT
Connects to actual cryptocurrency exchanges
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

logger = logging.getLogger(__name__)

try:
    import ccxt.async_support as ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False
    logger.warning("CCXT not installed. Using simulation mode only.")


class CCXTConnector:
    """
    Real exchange connector using CCXT library
    Supports 100+ cryptocurrency exchanges
    """
    
    def __init__(self, api_keys: Dict[str, Dict] = None, use_testnet: bool = True):
        """
        Initialize CCXT connector
        
        Args:
            api_keys: Dict of {exchange: {apiKey: ..., secret: ...}}
            use_testnet: Use testnet/sandbox mode
        """
        self.api_keys = api_keys or {}
        self.use_testnet = use_testnet
        self.exchanges = {}
        self.initialized = False
        
        if not CCXT_AVAILABLE:
            logger.error("CCXT library not available. Install with: pip install ccxt")
    
    async def initialize_exchanges(self, exchange_list: List[str] = None) -> bool:
        """
        Initialize exchange connections
        
        Args:
            exchange_list: List of exchange IDs to initialize
            
        Returns:
            True if successful
        """
        if not CCXT_AVAILABLE:
            return False
        
        if exchange_list is None:
            exchange_list = ['binance', 'coinbase', 'kraken', 'kucoin', 'bitfinex']
        
        for exchange_id in exchange_list:
            try:
                # Get exchange class
                exchange_class = getattr(ccxt, exchange_id)
                
                # Initialize with config
                config = {
                    'enableRateLimit': True,
                    'timeout': 30000,
                }
                
                # Add API keys if available
                if exchange_id in self.api_keys:
                    config.update(self.api_keys[exchange_id])
                
                # Enable testnet if requested
                if self.use_testnet and hasattr(exchange_class, 'set_sandbox_mode'):
                    config['sandbox'] = True
                
                # Create exchange instance
                exchange = exchange_class(config)
                
                # Load markets
                await exchange.load_markets()
                
                self.exchanges[exchange_id] = exchange
                logger.info(f"Initialized {exchange_id} - {len(exchange.markets)} markets")
                
            except Exception as e:
                logger.error(f"Failed to initialize {exchange_id}: {e}")
                continue
        
        self.initialized = len(self.exchanges) > 0
        return self.initialized
    
    async def fetch_ticker(self, exchange_id: str, symbol: str) -> Optional[Dict]:
        """
        Fetch ticker from exchange
        
        Args:
            exchange_id: Exchange identifier
            symbol: Trading symbol (e.g., 'BTC/USDT')
            
        Returns:
            Ticker data or None
        """
        if exchange_id not in self.exchanges:
            logger.error(f"Exchange {exchange_id} not initialized")
            return None
        
        try:
            exchange = self.exchanges[exchange_id]
            ticker = await exchange.fetch_ticker(symbol)
            
            return {
                'symbol': symbol,
                'exchange': exchange_id,
                'bid': ticker.get('bid'),
                'ask': ticker.get('ask'),
                'last': ticker.get('last'),
                'high': ticker.get('high'),
                'low': ticker.get('low'),
                'volume': ticker.get('baseVolume'),
                'quoteVolume': ticker.get('quoteVolume'),
                'timestamp': ticker.get('timestamp'),
                'datetime': ticker.get('datetime'),
            }
            
        except Exception as e:
            logger.error(f"Error fetching {symbol} from {exchange_id}: {e}")
            return None
    
    async def fetch_order_book(self, exchange_id: str, symbol: str, 
                               limit: int = 10) -> Optional[Dict]:
        """
        Fetch order book
        
        Args:
            exchange_id: Exchange identifier
            symbol: Trading symbol
            limit: Number of orders to fetch
            
        Returns:
            Order book data
        """
        if exchange_id not in self.exchanges:
            return None
        
        try:
            exchange = self.exchanges[exchange_id]
            order_book = await exchange.fetch_order_book(symbol, limit)
            
            return {
                'symbol': symbol,
                'exchange': exchange_id,
                'bids': order_book['bids'][:limit],
                'asks': order_book['asks'][:limit],
                'timestamp': order_book.get('timestamp'),
            }
            
        except Exception as e:
            logger.error(f"Error fetching order book for {symbol} from {exchange_id}: {e}")
            return None
    
    async def fetch_tickers_batch(self, exchange_id: str, 
                                  symbols: List[str]) -> Dict[str, Dict]:
        """
        Fetch multiple tickers at once
        
        Args:
            exchange_id: Exchange identifier
            symbols: List of symbols
            
        Returns:
            Dict of {symbol: ticker_data}
        """
        if exchange_id not in self.exchanges:
            return {}
        
        try:
            exchange = self.exchanges[exchange_id]
            
            # Try batch fetch if supported
            if exchange.has['fetchTickers']:
                tickers = await exchange.fetch_tickers(symbols)
                return {
                    symbol: {
                        'symbol': symbol,
                        'exchange': exchange_id,
                        'bid': data.get('bid'),
                        'ask': data.get('ask'),
                        'last': data.get('last'),
                        'volume': data.get('baseVolume'),
                        'timestamp': data.get('timestamp'),
                    }
                    for symbol, data in tickers.items()
                }
            else:
                # Fetch individually
                tasks = [self.fetch_ticker(exchange_id, symbol) for symbol in symbols]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                return {
                    symbol: result
                    for symbol, result in zip(symbols, results)
                    if isinstance(result, dict)
                }
                
        except Exception as e:
            logger.error(f"Error fetching tickers from {exchange_id}: {e}")
            return {}
    
    async def fetch_all_exchanges(self, symbols: List[str]) -> Dict[str, Dict[str, Dict]]:
        """
        Fetch data from all initialized exchanges
        
        Args:
            symbols: List of symbols to fetch
            
        Returns:
            Dict of {exchange: {symbol: ticker_data}}
        """
        tasks = []
        exchange_ids = []
        
        for exchange_id in self.exchanges.keys():
            tasks.append(self.fetch_tickers_batch(exchange_id, symbols))
            exchange_ids.append(exchange_id)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_data = {}
        for exchange_id, result in zip(exchange_ids, results):
            if isinstance(result, dict):
                all_data[exchange_id] = result
            else:
                logger.error(f"Failed to fetch from {exchange_id}: {result}")
                all_data[exchange_id] = {}
        
        return all_data
    
    async def get_exchange_balance(self, exchange_id: str) -> Optional[Dict]:
        """
        Get account balance (requires API keys)
        
        Args:
            exchange_id: Exchange identifier
            
        Returns:
            Balance data
        """
        if exchange_id not in self.exchanges:
            return None
        
        try:
            exchange = self.exchanges[exchange_id]
            balance = await exchange.fetch_balance()
            
            return {
                'total': balance['total'],
                'free': balance['free'],
                'used': balance['used'],
                'timestamp': datetime.now(),
            }
            
        except Exception as e:
            logger.error(f"Error fetching balance from {exchange_id}: {e}")
            return None
    
    async def place_order(self, exchange_id: str, symbol: str, 
                         order_type: str, side: str, amount: float, 
                         price: float = None) -> Optional[Dict]:
        """
        Place an order (requires API keys and testnet recommended)
        
        Args:
            exchange_id: Exchange identifier
            symbol: Trading symbol
            order_type: 'market' or 'limit'
            side: 'buy' or 'sell'
            amount: Amount to trade
            price: Price (for limit orders)
            
        Returns:
            Order data
        """
        if exchange_id not in self.exchanges:
            return None
        
        if not self.use_testnet:
            logger.warning("⚠️ PLACING REAL ORDER! Use testnet for safety.")
        
        try:
            exchange = self.exchanges[exchange_id]
            
            if order_type == 'market':
                order = await exchange.create_market_order(symbol, side, amount)
            elif order_type == 'limit':
                if price is None:
                    raise ValueError("Price required for limit orders")
                order = await exchange.create_limit_order(symbol, side, amount, price)
            else:
                raise ValueError(f"Invalid order type: {order_type}")
            
            logger.info(f"Order placed on {exchange_id}: {order}")
            return order
            
        except Exception as e:
            logger.error(f"Error placing order on {exchange_id}: {e}")
            return None
    
    async def close_all(self):
        """Close all exchange connections"""
        for exchange_id, exchange in self.exchanges.items():
            try:
                await exchange.close()
                logger.info(f"Closed connection to {exchange_id}")
            except Exception as e:
                logger.error(f"Error closing {exchange_id}: {e}")
    
    def get_supported_exchanges(self) -> List[str]:
        """Get list of CCXT supported exchanges"""
        if not CCXT_AVAILABLE:
            return []
        return ccxt.exchanges
    
    def get_exchange_info(self, exchange_id: str) -> Dict[str, Any]:
        """
        Get exchange information
        
        Args:
            exchange_id: Exchange identifier
            
        Returns:
            Exchange info
        """
        if exchange_id not in self.exchanges:
            return {}
        
        exchange = self.exchanges[exchange_id]
        
        return {
            'id': exchange.id,
            'name': exchange.name,
            'countries': getattr(exchange, 'countries', []),
            'has': exchange.has,
            'markets_count': len(exchange.markets) if exchange.markets else 0,
            'currencies_count': len(exchange.currencies) if exchange.currencies else 0,
            'rate_limit': exchange.rateLimit,
            'certified': getattr(exchange, 'certified', False),
            'pro': getattr(exchange, 'pro', False),
        }
