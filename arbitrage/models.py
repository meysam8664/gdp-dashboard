from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple


@dataclass
class ExchangeMarket:
    exchange_id: str
    symbols: List[str]


@dataclass
class Ticker:
    exchange_id: str
    symbol: str
    bid: Optional[float]
    ask: Optional[float]
    timestamp: Optional[int]

    @property
    def mid(self) -> Optional[float]:
        if self.bid is None or self.ask is None:
            return None
        return (self.bid + self.ask) / 2.0


@dataclass
class CrossExchangeOpportunity:
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    gross_spread_pct: float
    est_net_spread_pct: float
    est_net_profit_per_unit: float
    volume_limited_price: Optional[float] = None
    computed_at: datetime = datetime.utcnow()


@dataclass
class TriangularOpportunity:
    exchange_id: str
    path: Tuple[str, str, str]
    gross_multiplier: float
    est_net_multiplier: float
    base_asset: str
    computed_at: datetime = datetime.utcnow()


@dataclass
class FeeModel:
    taker_fee_rate: float = 0.001  # 0.1% default
    withdrawal_fee_asset: Optional[str] = None
    withdrawal_fee_amount: float = 0.0


@dataclass
class ScanConfig:
    exchange_ids: List[str]
    symbols: List[str]
    fee_overrides: Dict[str, FeeModel]
    max_concurrency: int = 10
    request_timeout_ms: int = 10_000
    retries: int = 2
    slippage_bps: float = 10.0  # 0.10%
