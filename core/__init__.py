"""
Core modules for Professional Arbitrage Finder
"""

from .arbitrage_engine import ArbitrageEngine, ArbitrageOpportunity, ArbitrageType
from .exchange_connector import ExchangeConnector
from .database import ArbitrageDatabase
from .notifications import NotificationManager, NotificationConfig
from .backtesting import BacktestEngine, BacktestResult
from .analytics import AdvancedAnalytics

# Optional CCXT connector (requires ccxt package)
try:
    from .ccxt_connector import CCXTConnector
    CCXT_AVAILABLE = True
except ImportError:
    CCXTConnector = None
    CCXT_AVAILABLE = False

__all__ = [
    'ArbitrageEngine',
    'ArbitrageOpportunity', 
    'ArbitrageType',
    'ExchangeConnector',
    'ArbitrageDatabase',
    'NotificationManager',
    'NotificationConfig',
    'BacktestEngine',
    'BacktestResult',
    'AdvancedAnalytics',
    'CCXTConnector',
    'CCXT_AVAILABLE',
]
