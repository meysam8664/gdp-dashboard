"""
Configuration Management for Arbitrage Finder
"""

import os
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class ArbitrageConfig:
    """Configuration for arbitrage detection"""
    
    # Profit thresholds
    min_profit_percentage: float = 1.0
    high_profit_threshold: float = 3.0
    
    # Risk management
    max_risk_level: str = "HIGH"
    min_confidence: float = 0.5
    
    # Exchange settings
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_per_second: int = 10
    
    # Monitoring settings
    scan_interval: int = 10
    auto_scan_enabled: bool = False
    
    # Assets to monitor
    default_assets: List[str] = None
    
    # Fee settings
    default_trading_fee: float = 0.002  # 0.2%
    withdrawal_fee_percentage: float = 0.001  # 0.1%
    
    # Execution settings
    max_execution_time: float = 60.0  # seconds
    min_liquidity: float = 10000.0  # USD
    
    def __post_init__(self):
        if self.default_assets is None:
            self.default_assets = [
                'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 
                'SOL/USDT', 'ADA/USDT',
                'ETH/BTC', 'BNB/BTC', 'BNB/ETH'
            ]
    
    @classmethod
    def from_env(cls):
        """Load configuration from environment variables"""
        return cls(
            min_profit_percentage=float(os.getenv('MIN_PROFIT_PCT', 1.0)),
            max_retries=int(os.getenv('MAX_RETRIES', 3)),
            scan_interval=int(os.getenv('SCAN_INTERVAL', 10)),
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'min_profit_percentage': self.min_profit_percentage,
            'high_profit_threshold': self.high_profit_threshold,
            'max_risk_level': self.max_risk_level,
            'min_confidence': self.min_confidence,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'rate_limit_per_second': self.rate_limit_per_second,
            'scan_interval': self.scan_interval,
            'auto_scan_enabled': self.auto_scan_enabled,
            'default_assets': self.default_assets,
            'default_trading_fee': self.default_trading_fee,
            'withdrawal_fee_percentage': self.withdrawal_fee_percentage,
            'max_execution_time': self.max_execution_time,
            'min_liquidity': self.min_liquidity,
        }


# Default configuration
DEFAULT_CONFIG = ArbitrageConfig()


# Exchange reliability scores (0-1)
EXCHANGE_RELIABILITY = {
    'Binance': 0.99,
    'Coinbase': 0.98,
    'Kraken': 0.97,
    'KuCoin': 0.95,
    'Bitfinex': 0.94,
}


# Supported arbitrage types
SUPPORTED_ARBITRAGE_TYPES = [
    'spatial',
    'triangular',
    'statistical',
    'cross_exchange'
]


# Color scheme for UI
UI_COLORS = {
    'primary': '#2ecc71',
    'secondary': '#3498db',
    'success': '#27ae60',
    'warning': '#f39c12',
    'danger': '#e74c3c',
    'info': '#3498db',
}
