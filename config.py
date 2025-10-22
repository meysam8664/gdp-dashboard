"""
Configuration settings for the Arbitrage Opportunity Finder
"""

import os
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class ExchangeConfig:
    """Exchange configuration"""
    name: str
    api_key: str = ""
    secret: str = ""
    sandbox: bool = True
    enabled: bool = True
    rate_limit: int = 1200  # requests per minute
    timeout: int = 30  # seconds

@dataclass
class ArbitrageConfig:
    """Arbitrage detection configuration"""
    min_profit_percentage: float = 0.1
    min_volume: float = 1000
    max_spread: float = 5.0
    max_risk_score: float = 50.0
    scan_interval: int = 5  # seconds
    max_opportunities: int = 100
    confidence_threshold: float = 60.0

@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    symbols: List[str] = None
    exchanges: List[str] = None
    auto_start: bool = False
    log_level: str = "INFO"
    log_file: str = "arbitrage.log"
    max_log_size: str = "10MB"
    log_retention: int = 7  # days

class Config:
    """Main configuration class"""
    
    def __init__(self):
        self.exchanges = {
            "binance": ExchangeConfig(
                name="binance",
                api_key=os.getenv("BINANCE_API_KEY", ""),
                secret=os.getenv("BINANCE_SECRET", ""),
                sandbox=True,
                enabled=True
            ),
            "coinbase": ExchangeConfig(
                name="coinbase",
                api_key=os.getenv("COINBASE_API_KEY", ""),
                secret=os.getenv("COINBASE_SECRET", ""),
                sandbox=True,
                enabled=True
            ),
            "kraken": ExchangeConfig(
                name="kraken",
                api_key=os.getenv("KRAKEN_API_KEY", ""),
                secret=os.getenv("KRAKEN_SECRET", ""),
                sandbox=True,
                enabled=True
            ),
            "kucoin": ExchangeConfig(
                name="kucoin",
                api_key=os.getenv("KUCOIN_API_KEY", ""),
                secret=os.getenv("KUCOIN_SECRET", ""),
                sandbox=True,
                enabled=True
            ),
            "bybit": ExchangeConfig(
                name="bybit",
                api_key=os.getenv("BYBIT_API_KEY", ""),
                secret=os.getenv("BYBIT_SECRET", ""),
                sandbox=True,
                enabled=True
            ),
            "okx": ExchangeConfig(
                name="okx",
                api_key=os.getenv("OKX_API_KEY", ""),
                secret=os.getenv("OKX_SECRET", ""),
                sandbox=True,
                enabled=True
            ),
            "gateio": ExchangeConfig(
                name="gateio",
                api_key=os.getenv("GATEIO_API_KEY", ""),
                secret=os.getenv("GATEIO_SECRET", ""),
                sandbox=True,
                enabled=True
            )
        }
        
        self.arbitrage = ArbitrageConfig()
        
        self.monitoring = MonitoringConfig(
            symbols=[
                'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT',
                'DOT/USDT', 'LINK/USDT', 'MATIC/USDT', 'AVAX/USDT', 'ATOM/USDT'
            ],
            exchanges=["binance", "coinbase", "kraken", "kucoin", "bybit", "okx", "gateio"],
            auto_start=False
        )
    
    def get_enabled_exchanges(self) -> List[str]:
        """Get list of enabled exchanges"""
        return [name for name, config in self.exchanges.items() if config.enabled]
    
    def get_exchange_config(self, exchange_name: str) -> ExchangeConfig:
        """Get configuration for specific exchange"""
        return self.exchanges.get(exchange_name, ExchangeConfig(name=exchange_name))
    
    def update_arbitrage_config(self, **kwargs):
        """Update arbitrage configuration"""
        for key, value in kwargs.items():
            if hasattr(self.arbitrage, key):
                setattr(self.arbitrage, key, value)
    
    def update_monitoring_config(self, **kwargs):
        """Update monitoring configuration"""
        for key, value in kwargs.items():
            if hasattr(self.monitoring, key):
                setattr(self.monitoring, key, value)

# Global configuration instance
config = Config()