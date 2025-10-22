"""
Professional Arbitrage Engine
A comprehensive system for detecting and executing arbitrage opportunities across multiple exchanges
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import ccxt
import ccxt.async_support as ccxt_async
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('arbitrage.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ArbitrageType(Enum):
    """Types of arbitrage opportunities"""
    SIMPLE = "simple"  # Buy low, sell high
    TRIANGULAR = "triangular"  # A->B->C->A
    STATISTICAL = "statistical"  # Mean reversion
    CROSS_EXCHANGE = "cross_exchange"  # Between different exchanges
    FUNDING_RATE = "funding_rate"  # Perpetual funding rate arbitrage

@dataclass
class ArbitrageOpportunity:
    """Represents an arbitrage opportunity"""
    id: str
    type: ArbitrageType
    symbol: str
    exchanges: List[str]
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    profit_percentage: float
    profit_amount: float
    volume: float
    confidence: float
    timestamp: datetime
    fees: Dict[str, float]
    risk_score: float
    execution_time_estimate: float
    status: str = "detected"

@dataclass
class ExchangeConfig:
    """Configuration for exchange connections"""
    name: str
    api_key: str
    secret: str
    sandbox: bool = True
    rate_limit: int = 1200
    timeout: int = 30000
    enable_rate_limit: bool = True

class ArbitrageEngine:
    """Main arbitrage detection and execution engine"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        self.async_exchanges: Dict[str, ccxt_async.Exchange] = {}
        self.opportunities: List[ArbitrageOpportunity] = []
        self.price_data: Dict[str, Dict[str, float]] = {}
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Load configuration
        self.load_config()
        
        # Initialize exchanges
        self.initialize_exchanges()
        
    def load_config(self):
        """Load configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_file} not found, using defaults")
            self.config = self.get_default_config()
            
    def get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "exchanges": {
                "binance": {
                    "api_key": "",
                    "secret": "",
                    "sandbox": True
                },
                "coinbase": {
                    "api_key": "",
                    "secret": "",
                    "sandbox": True
                },
                "kraken": {
                    "api_key": "",
                    "secret": "",
                    "sandbox": True
                }
            },
            "arbitrage": {
                "min_profit_percentage": 0.5,
                "max_risk_score": 0.7,
                "min_volume": 1000,
                "max_execution_time": 30,
                "update_interval": 5
            },
            "notifications": {
                "enabled": True,
                "telegram": {
                    "bot_token": "",
                    "chat_id": ""
                },
                "discord": {
                    "webhook_url": ""
                }
            }
        }
    
    def initialize_exchanges(self):
        """Initialize exchange connections"""
        for exchange_name, config in self.config["exchanges"].items():
            try:
                # Initialize sync exchange
                exchange_class = getattr(ccxt, exchange_name)
                self.exchanges[exchange_name] = exchange_class({
                    'apiKey': config.get('api_key', ''),
                    'secret': config.get('secret', ''),
                    'sandbox': config.get('sandbox', True),
                    'rateLimit': config.get('rate_limit', 1200),
                    'timeout': config.get('timeout', 30000),
                    'enableRateLimit': config.get('enable_rate_limit', True)
                })
                
                # Initialize async exchange
                async_exchange_class = getattr(ccxt_async, exchange_name)
                self.async_exchanges[exchange_name] = async_exchange_class({
                    'apiKey': config.get('api_key', ''),
                    'secret': config.get('secret', ''),
                    'sandbox': config.get('sandbox', True),
                    'rateLimit': config.get('rate_limit', 1200),
                    'timeout': config.get('timeout', 30000),
                    'enableRateLimit': config.get('enable_rate_limit', True)
                })
                
                logger.info(f"Initialized {exchange_name} exchange")
                
            except Exception as e:
                logger.error(f"Failed to initialize {exchange_name}: {e}")
    
    async def get_ticker_data(self, symbol: str) -> Dict[str, Dict[str, float]]:
        """Get ticker data from all exchanges for a symbol"""
        ticker_data = {}
        
        async def fetch_ticker(exchange_name: str, exchange: ccxt_async.Exchange):
            try:
                ticker = await exchange.fetch_ticker(symbol)
                return exchange_name, {
                    'bid': ticker['bid'],
                    'ask': ticker['ask'],
                    'last': ticker['last'],
                    'volume': ticker['baseVolume'],
                    'timestamp': ticker['timestamp']
                }
            except Exception as e:
                logger.error(f"Error fetching ticker from {exchange_name}: {e}")
                return exchange_name, None
        
        # Fetch data from all exchanges concurrently
        tasks = [
            fetch_ticker(name, exchange) 
            for name, exchange in self.async_exchanges.items()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, tuple) and result[1] is not None:
                ticker_data[result[0]] = result[1]
        
        return ticker_data
    
    def calculate_arbitrage_opportunities(self, symbol: str, ticker_data: Dict[str, Dict[str, float]]) -> List[ArbitrageOpportunity]:
        """Calculate arbitrage opportunities from ticker data"""
        opportunities = []
        
        if len(ticker_data) < 2:
            return opportunities
        
        exchanges = list(ticker_data.keys())
        
        # Check all possible exchange pairs
        for i, buy_exchange in enumerate(exchanges):
            for j, sell_exchange in enumerate(exchanges):
                if i == j:
                    continue
                
                buy_data = ticker_data[buy_exchange]
                sell_data = ticker_data[sell_exchange]
                
                if not all(key in buy_data and key in sell_data for key in ['bid', 'ask', 'last']):
                    continue
                
                # Simple arbitrage: buy at lowest ask, sell at highest bid
                buy_price = buy_data['ask']
                sell_price = sell_data['bid']
                
                if sell_price > buy_price:
                    profit_percentage = ((sell_price - buy_price) / buy_price) * 100
                    
                    # Check if profit meets minimum threshold
                    min_profit = self.config["arbitrage"]["min_profit_percentage"]
                    if profit_percentage >= min_profit:
                        
                        # Calculate fees (simplified)
                        buy_fee = 0.001  # 0.1% typical fee
                        sell_fee = 0.001
                        net_profit_percentage = profit_percentage - (buy_fee + sell_fee) * 100
                        
                        if net_profit_percentage > 0:
                            # Calculate risk score
                            risk_score = self.calculate_risk_score(buy_data, sell_data, buy_exchange, sell_exchange)
                            
                            # Calculate execution time estimate
                            execution_time = self.estimate_execution_time(buy_exchange, sell_exchange)
                            
                            opportunity = ArbitrageOpportunity(
                                id=f"{symbol}_{buy_exchange}_{sell_exchange}_{int(time.time())}",
                                type=ArbitrageType.SIMPLE,
                                symbol=symbol,
                                exchanges=[buy_exchange, sell_exchange],
                                buy_exchange=buy_exchange,
                                sell_exchange=sell_exchange,
                                buy_price=buy_price,
                                sell_price=sell_price,
                                profit_percentage=net_profit_percentage,
                                profit_amount=0,  # Will be calculated based on volume
                                volume=min(buy_data.get('volume', 0), sell_data.get('volume', 0)),
                                confidence=self.calculate_confidence(buy_data, sell_data),
                                timestamp=datetime.now(),
                                fees={'buy': buy_fee, 'sell': sell_fee},
                                risk_score=risk_score,
                                execution_time_estimate=execution_time
                            )
                            
                            opportunities.append(opportunity)
        
        return opportunities
    
    def calculate_risk_score(self, buy_data: Dict, sell_data: Dict, buy_exchange: str, sell_exchange: str) -> float:
        """Calculate risk score for an arbitrage opportunity (0-1, lower is better)"""
        risk_factors = []
        
        # Volume risk
        min_volume = self.config["arbitrage"]["min_volume"]
        buy_volume = buy_data.get('volume', 0)
        sell_volume = sell_data.get('volume', 0)
        
        if buy_volume < min_volume or sell_volume < min_volume:
            risk_factors.append(0.8)  # High risk for low volume
        else:
            volume_risk = 1 - min(buy_volume, sell_volume) / max(buy_volume, sell_volume)
            risk_factors.append(volume_risk * 0.3)
        
        # Price spread risk
        buy_spread = (buy_data['ask'] - buy_data['bid']) / buy_data['last'] if buy_data['last'] > 0 else 1
        sell_spread = (sell_data['ask'] - sell_data['bid']) / sell_data['last'] if sell_data['last'] > 0 else 1
        spread_risk = (buy_spread + sell_spread) / 2
        risk_factors.append(min(spread_risk * 2, 0.5))
        
        # Exchange reliability (simplified)
        reliable_exchanges = ['binance', 'coinbase', 'kraken']
        exchange_risk = 0.1 if buy_exchange in reliable_exchanges and sell_exchange in reliable_exchanges else 0.3
        risk_factors.append(exchange_risk)
        
        return min(sum(risk_factors), 1.0)
    
    def calculate_confidence(self, buy_data: Dict, sell_data: Dict) -> float:
        """Calculate confidence score for an arbitrage opportunity (0-1, higher is better)"""
        confidence_factors = []
        
        # Data freshness
        current_time = time.time() * 1000
        buy_age = (current_time - buy_data.get('timestamp', current_time)) / 1000
        sell_age = (current_time - sell_data.get('timestamp', current_time)) / 1000
        
        max_age = 60  # 1 minute
        buy_freshness = max(0, 1 - buy_age / max_age)
        sell_freshness = max(0, 1 - sell_age / max_age)
        confidence_factors.append((buy_freshness + sell_freshness) / 2)
        
        # Volume confidence
        min_volume = self.config["arbitrage"]["min_volume"]
        buy_volume_confidence = min(1, buy_data.get('volume', 0) / min_volume)
        sell_volume_confidence = min(1, sell_data.get('volume', 0) / min_volume)
        confidence_factors.append((buy_volume_confidence + sell_volume_confidence) / 2)
        
        return min(sum(confidence_factors) / len(confidence_factors), 1.0)
    
    def estimate_execution_time(self, buy_exchange: str, sell_exchange: str) -> float:
        """Estimate execution time in seconds"""
        # Simplified estimation based on exchange characteristics
        execution_times = {
            'binance': 2.0,
            'coinbase': 3.0,
            'kraken': 2.5,
            'kucoin': 3.5,
            'huobi': 4.0
        }
        
        buy_time = execution_times.get(buy_exchange, 5.0)
        sell_time = execution_times.get(sell_exchange, 5.0)
        
        return buy_time + sell_time + 1.0  # Add 1 second for network latency
    
    async def scan_arbitrage_opportunities(self, symbols: List[str]) -> List[ArbitrageOpportunity]:
        """Scan for arbitrage opportunities across all symbols"""
        all_opportunities = []
        
        for symbol in symbols:
            try:
                logger.info(f"Scanning arbitrage opportunities for {symbol}")
                ticker_data = await self.get_ticker_data(symbol)
                
                if ticker_data:
                    opportunities = self.calculate_arbitrage_opportunities(symbol, ticker_data)
                    all_opportunities.extend(opportunities)
                    
                    logger.info(f"Found {len(opportunities)} opportunities for {symbol}")
                
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
        
        # Filter opportunities based on configuration
        filtered_opportunities = self.filter_opportunities(all_opportunities)
        
        return filtered_opportunities
    
    def filter_opportunities(self, opportunities: List[ArbitrageOpportunity]) -> List[ArbitrageOpportunity]:
        """Filter opportunities based on configuration criteria"""
        filtered = []
        
        for opp in opportunities:
            # Check minimum profit percentage
            if opp.profit_percentage < self.config["arbitrage"]["min_profit_percentage"]:
                continue
            
            # Check maximum risk score
            if opp.risk_score > self.config["arbitrage"]["max_risk_score"]:
                continue
            
            # Check minimum volume
            if opp.volume < self.config["arbitrage"]["min_volume"]:
                continue
            
            # Check maximum execution time
            if opp.execution_time_estimate > self.config["arbitrage"]["max_execution_time"]:
                continue
            
            filtered.append(opp)
        
        return filtered
    
    async def start_monitoring(self, symbols: List[str], interval: int = 5):
        """Start continuous monitoring for arbitrage opportunities"""
        self.running = True
        logger.info(f"Starting arbitrage monitoring for {len(symbols)} symbols")
        
        while self.running:
            try:
                opportunities = await self.scan_arbitrage_opportunities(symbols)
                
                if opportunities:
                    logger.info(f"Found {len(opportunities)} new opportunities")
                    self.opportunities.extend(opportunities)
                    
                    # Send notifications for high-value opportunities
                    await self.send_notifications(opportunities)
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval)
    
    async def send_notifications(self, opportunities: List[ArbitrageOpportunity]):
        """Send notifications for arbitrage opportunities"""
        if not self.config["notifications"]["enabled"]:
            return
        
        for opp in opportunities:
            if opp.profit_percentage > 2.0 and opp.confidence > 0.7:  # High-value opportunities
                message = self.format_opportunity_message(opp)
                
                # Send to configured notification channels
                if self.config["notifications"].get("telegram", {}).get("bot_token"):
                    await self.send_telegram_notification(message)
                
                if self.config["notifications"].get("discord", {}).get("webhook_url"):
                    await self.send_discord_notification(message)
    
    def format_opportunity_message(self, opp: ArbitrageOpportunity) -> str:
        """Format opportunity message for notifications"""
        return f"""
🚀 **Arbitrage Opportunity Detected**

**Symbol:** {opp.symbol}
**Type:** {opp.type.value}
**Buy:** {opp.buy_exchange} @ ${opp.buy_price:.4f}
**Sell:** {opp.sell_exchange} @ ${opp.sell_price:.4f}
**Profit:** {opp.profit_percentage:.2f}%
**Volume:** ${opp.volume:,.0f}
**Confidence:** {opp.confidence:.2f}
**Risk Score:** {opp.risk_score:.2f}
**Execution Time:** {opp.execution_time_estimate:.1f}s

**Timestamp:** {opp.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
        """
    
    async def send_telegram_notification(self, message: str):
        """Send notification via Telegram"""
        # Implementation would go here
        pass
    
    async def send_discord_notification(self, message: str):
        """Send notification via Discord"""
        # Implementation would go here
        pass
    
    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.running = False
        logger.info("Stopped arbitrage monitoring")
    
    def get_opportunities_summary(self) -> Dict[str, Any]:
        """Get summary of all opportunities"""
        if not self.opportunities:
            return {"total": 0, "opportunities": []}
        
        # Group by symbol
        by_symbol = {}
        for opp in self.opportunities:
            if opp.symbol not in by_symbol:
                by_symbol[opp.symbol] = []
            by_symbol[opp.symbol].append(opp)
        
        # Calculate statistics
        total_profit = sum(opp.profit_percentage for opp in self.opportunities)
        avg_profit = total_profit / len(self.opportunities)
        max_profit = max(opp.profit_percentage for opp in self.opportunities)
        
        return {
            "total": len(self.opportunities),
            "total_profit": total_profit,
            "avg_profit": avg_profit,
            "max_profit": max_profit,
            "by_symbol": {symbol: len(opps) for symbol, opps in by_symbol.items()},
            "opportunities": [
                {
                    "id": opp.id,
                    "symbol": opp.symbol,
                    "type": opp.type.value,
                    "profit_percentage": opp.profit_percentage,
                    "confidence": opp.confidence,
                    "risk_score": opp.risk_score,
                    "timestamp": opp.timestamp.isoformat()
                }
                for opp in self.opportunities[-10:]  # Last 10 opportunities
            ]
        }

# Example usage
if __name__ == "__main__":
    async def main():
        engine = ArbitrageEngine()
        
        # Example symbols to monitor
        symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", "SOL/USDT"]
        
        try:
            await engine.start_monitoring(symbols, interval=10)
        except KeyboardInterrupt:
            engine.stop_monitoring()
            print("Monitoring stopped by user")
    
    # Run the example
    asyncio.run(main())