"""
Professional Arbitrage Opportunity Finder
========================================

A comprehensive arbitrage detection system that monitors multiple exchanges
and identifies profitable trading opportunities in real-time.

Features:
- Multi-exchange support (Binance, Coinbase, Kraken, etc.)
- Real-time price monitoring
- Intelligent opportunity detection
- Risk management
- Comprehensive error handling
- Live dashboard
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import traceback

import ccxt
import pandas as pd
import numpy as np
from loguru import logger
import requests
from pydantic import BaseModel, Field

# Configure logging
logger.remove()
logger.add("arbitrage.log", rotation="1 day", retention="7 days", level="DEBUG")
logger.add(lambda msg: print(msg, end=""), level="INFO")

class ExchangeType(Enum):
    """Supported exchange types"""
    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    KUCOIN = "kucoin"
    BYBIT = "bybit"
    OKX = "okx"
    GATEIO = "gateio"

class ArbitrageType(Enum):
    """Types of arbitrage opportunities"""
    SIMPLE = "simple"  # Same asset, different exchanges
    TRIANGULAR = "triangular"  # A->B->C->A
    CROSS_CURRENCY = "cross_currency"  # Different base currencies
    FUTURES_SPOT = "futures_spot"  # Futures vs spot arbitrage

@dataclass
class PriceData:
    """Price data structure"""
    exchange: str
    symbol: str
    bid: float
    ask: float
    timestamp: datetime
    volume_24h: float = 0.0
    spread: float = 0.0

@dataclass
class ArbitrageOpportunity:
    """Arbitrage opportunity structure"""
    id: str
    type: ArbitrageType
    buy_exchange: str
    sell_exchange: str
    symbol: str
    buy_price: float
    sell_price: float
    profit_percentage: float
    profit_absolute: float
    volume: float
    confidence: float
    timestamp: datetime
    risk_score: float
    execution_time_estimate: float

class ExchangeManager:
    """Manages multiple exchange connections and data fetching"""
    
    def __init__(self):
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        self.exchange_configs = {
            ExchangeType.BINANCE: {
                'apiKey': '',  # Add your API keys
                'secret': '',
                'sandbox': True,  # Use sandbox for testing
                'enableRateLimit': True,
            },
            ExchangeType.COINBASE: {
                'apiKey': '',
                'secret': '',
                'sandbox': True,
            },
            ExchangeType.KRAKEN: {
                'apiKey': '',
                'secret': '',
                'sandbox': True,
            },
            ExchangeType.KUCOIN: {
                'apiKey': '',
                'secret': '',
                'sandbox': True,
            },
            ExchangeType.BYBIT: {
                'apiKey': '',
                'secret': '',
                'sandbox': True,
            },
            ExchangeType.OKX: {
                'apiKey': '',
                'secret': '',
                'sandbox': True,
            },
            ExchangeType.GATEIO: {
                'apiKey': '',
                'secret': '',
                'sandbox': True,
            }
        }
        self._initialize_exchanges()
    
    def _initialize_exchanges(self):
        """Initialize exchange connections"""
        for exchange_type, config in self.exchange_configs.items():
            try:
                exchange_class = getattr(ccxt, exchange_type.value)
                self.exchanges[exchange_type.value] = exchange_class(config)
                logger.info(f"Initialized {exchange_type.value} exchange")
            except Exception as e:
                logger.error(f"Failed to initialize {exchange_type.value}: {e}")
    
    async def get_ticker_data(self, exchange_name: str, symbol: str) -> Optional[PriceData]:
        """Get ticker data from specific exchange"""
        try:
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                return None
            
            ticker = await asyncio.get_event_loop().run_in_executor(
                None, exchange.fetch_ticker, symbol
            )
            
            if not ticker:
                return None
            
            spread = (ticker['ask'] - ticker['bid']) / ticker['bid'] * 100 if ticker['bid'] > 0 else 0
            
            return PriceData(
                exchange=exchange_name,
                symbol=symbol,
                bid=ticker['bid'],
                ask=ticker['ask'],
                timestamp=datetime.now(),
                volume_24h=ticker.get('quoteVolume', 0),
                spread=spread
            )
        except Exception as e:
            logger.error(f"Error fetching ticker from {exchange_name} for {symbol}: {e}")
            return None
    
    async def get_all_tickers(self, symbol: str) -> List[PriceData]:
        """Get ticker data from all exchanges"""
        tasks = []
        for exchange_name in self.exchanges.keys():
            task = self.get_ticker_data(exchange_name, symbol)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        for result in results:
            if isinstance(result, PriceData):
                valid_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Exception in ticker fetch: {result}")
        
        return valid_results

class ArbitrageDetector:
    """Detects arbitrage opportunities across exchanges"""
    
    def __init__(self, exchange_manager: ExchangeManager):
        self.exchange_manager = exchange_manager
        self.min_profit_percentage = 0.1  # Minimum 0.1% profit
        self.min_volume = 1000  # Minimum volume requirement
        self.max_spread = 5.0  # Maximum spread percentage
        
    def detect_simple_arbitrage(self, price_data: List[PriceData]) -> List[ArbitrageOpportunity]:
        """Detect simple arbitrage opportunities"""
        opportunities = []
        
        if len(price_data) < 2:
            return opportunities
        
        # Sort by ask price (ascending) for buying
        buy_candidates = sorted(price_data, key=lambda x: x.ask)
        
        # Sort by bid price (descending) for selling
        sell_candidates = sorted(price_data, key=lambda x: x.bid, reverse=True)
        
        for buy_data in buy_candidates:
            for sell_data in sell_candidates:
                if buy_data.exchange == sell_data.exchange:
                    continue
                
                # Calculate profit
                profit_absolute = sell_data.bid - buy_data.ask
                profit_percentage = (profit_absolute / buy_data.ask) * 100
                
                # Check if opportunity meets criteria
                if (profit_percentage >= self.min_profit_percentage and
                    buy_data.volume_24h >= self.min_volume and
                    sell_data.volume_24h >= self.min_volume and
                    buy_data.spread <= self.max_spread and
                    sell_data.spread <= self.max_spread):
                    
                    # Calculate confidence based on volume and spread
                    confidence = self._calculate_confidence(buy_data, sell_data)
                    
                    # Calculate risk score
                    risk_score = self._calculate_risk_score(buy_data, sell_data)
                    
                    opportunity = ArbitrageOpportunity(
                        id=f"{buy_data.exchange}_{sell_data.exchange}_{buy_data.symbol}_{int(time.time())}",
                        type=ArbitrageType.SIMPLE,
                        buy_exchange=buy_data.exchange,
                        sell_exchange=sell_data.exchange,
                        symbol=buy_data.symbol,
                        buy_price=buy_data.ask,
                        sell_price=sell_data.bid,
                        profit_percentage=profit_percentage,
                        profit_absolute=profit_absolute,
                        volume=min(buy_data.volume_24h, sell_data.volume_24h),
                        confidence=confidence,
                        timestamp=datetime.now(),
                        risk_score=risk_score,
                        execution_time_estimate=self._estimate_execution_time(buy_data, sell_data)
                    )
                    
                    opportunities.append(opportunity)
        
        return opportunities
    
    def detect_triangular_arbitrage(self, price_data: List[PriceData]) -> List[ArbitrageOpportunity]:
        """Detect triangular arbitrage opportunities"""
        opportunities = []
        
        # This is a simplified version - in practice, you'd need more complex logic
        # to handle different trading pairs and cross-currency arbitrage
        
        return opportunities
    
    def _calculate_confidence(self, buy_data: PriceData, sell_data: PriceData) -> float:
        """Calculate confidence score for arbitrage opportunity"""
        volume_factor = min(buy_data.volume_24h, sell_data.volume_24h) / 1000000  # Normalize volume
        spread_factor = 1 - (buy_data.spread + sell_data.spread) / 100  # Lower spread = higher confidence
        
        confidence = (volume_factor * 0.6 + spread_factor * 0.4) * 100
        return min(confidence, 100.0)
    
    def _calculate_risk_score(self, buy_data: PriceData, sell_data: PriceData) -> float:
        """Calculate risk score for arbitrage opportunity"""
        time_diff = abs((buy_data.timestamp - sell_data.timestamp).total_seconds())
        time_risk = min(time_diff / 60, 1.0)  # Risk increases with time difference
        
        spread_risk = (buy_data.spread + sell_data.spread) / 100
        
        risk_score = (time_risk * 0.5 + spread_risk * 0.5) * 100
        return min(risk_score, 100.0)
    
    def _estimate_execution_time(self, buy_data: PriceData, sell_data: PriceData) -> float:
        """Estimate execution time for arbitrage"""
        # This is a simplified estimation
        base_time = 2.0  # Base execution time in seconds
        network_latency = 0.5  # Network latency
        exchange_processing = 1.0  # Exchange processing time
        
        return base_time + network_latency + exchange_processing

class ArbitrageMonitor:
    """Main arbitrage monitoring system"""
    
    def __init__(self):
        self.exchange_manager = ExchangeManager()
        self.detector = ArbitrageDetector(self.exchange_manager)
        self.opportunities: List[ArbitrageOpportunity] = []
        self.monitoring = False
        self.symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT']
        
    async def start_monitoring(self):
        """Start the arbitrage monitoring process"""
        self.monitoring = True
        logger.info("Starting arbitrage monitoring...")
        
        while self.monitoring:
            try:
                await self._scan_opportunities()
                await asyncio.sleep(5)  # Scan every 5 seconds
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def stop_monitoring(self):
        """Stop the arbitrage monitoring process"""
        self.monitoring = False
        logger.info("Stopped arbitrage monitoring")
    
    async def _scan_opportunities(self):
        """Scan for arbitrage opportunities"""
        for symbol in self.symbols:
            try:
                # Get price data from all exchanges
                price_data = await self.exchange_manager.get_all_tickers(symbol)
                
                if len(price_data) < 2:
                    continue
                
                # Detect simple arbitrage opportunities
                simple_opportunities = self.detector.detect_simple_arbitrage(price_data)
                
                # Add new opportunities
                for opportunity in simple_opportunities:
                    if not any(op.id == opportunity.id for op in self.opportunities):
                        self.opportunities.append(opportunity)
                        logger.info(f"New arbitrage opportunity: {opportunity.symbol} "
                                  f"{opportunity.buy_exchange}->{opportunity.sell_exchange} "
                                  f"Profit: {opportunity.profit_percentage:.2f}%")
                
                # Clean up old opportunities (older than 5 minutes)
                cutoff_time = datetime.now() - timedelta(minutes=5)
                self.opportunities = [op for op in self.opportunities if op.timestamp > cutoff_time]
                
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
    
    def get_opportunities(self, limit: int = 50) -> List[ArbitrageOpportunity]:
        """Get current arbitrage opportunities"""
        return sorted(self.opportunities, key=lambda x: x.profit_percentage, reverse=True)[:limit]
    
    def get_opportunities_by_symbol(self, symbol: str) -> List[ArbitrageOpportunity]:
        """Get opportunities for specific symbol"""
        return [op for op in self.opportunities if op.symbol == symbol]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        if not self.opportunities:
            return {
                'total_opportunities': 0,
                'avg_profit': 0,
                'max_profit': 0,
                'active_exchanges': len(self.exchange_manager.exchanges),
                'monitoring_symbols': len(self.symbols)
            }
        
        profits = [op.profit_percentage for op in self.opportunities]
        
        return {
            'total_opportunities': len(self.opportunities),
            'avg_profit': np.mean(profits),
            'max_profit': max(profits),
            'min_profit': min(profits),
            'active_exchanges': len(self.exchange_manager.exchanges),
            'monitoring_symbols': len(self.symbols),
            'last_scan': max(op.timestamp for op in self.opportunities).isoformat()
        }

# Global monitor instance
arbitrage_monitor = ArbitrageMonitor()

async def main():
    """Main function for testing"""
    try:
        await arbitrage_monitor.start_monitoring()
    except KeyboardInterrupt:
        await arbitrage_monitor.stop_monitoring()
        logger.info("Arbitrage monitoring stopped by user")

if __name__ == "__main__":
    asyncio.run(main())