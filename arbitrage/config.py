from __future__ import annotations

from typing import List, Dict
from pydantic import BaseModel, Field, PositiveFloat
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_EXCHANGES = [
    "binance",
    "kucoin",
    "bybit",
]

DEFAULT_SYMBOLS = [
    "BTC/USDT",
    "ETH/USDT",
]


class FeeConfig(BaseModel):
    taker: float = Field(0.001, ge=0.0, le=0.01)


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ARBIT_", env_file=".env", extra="ignore")

    exchanges: List[str] = Field(default_factory=lambda: list(DEFAULT_EXCHANGES))
    symbols: List[str] = Field(default_factory=lambda: list(DEFAULT_SYMBOLS))

    # Amount of QUOTE currency to trade per opportunity (e.g., USDT)
    amount_quote: PositiveFloat = 1000.0

    # Timeouts and concurrency
    request_timeout_seconds: PositiveFloat = 10.0
    exchange_concurrency: int = Field(5, ge=1, le=20)

    # Minimum profit percentage to display
    min_profit_pct: float = Field(0.002, ge=0.0, le=1.0)

    # Toggle triangular scanning
    include_triangular: bool = True

    # Per-exchange fee overrides (taker fees). Keys are ccxt exchange ids.
    fees: Dict[str, FeeConfig] = Field(default_factory=lambda: {
        "binance": FeeConfig(taker=0.001),
        "kucoin": FeeConfig(taker=0.001),
        "bybit": FeeConfig(taker=0.001),
        "okx": FeeConfig(taker=0.0008),
        "gate": FeeConfig(taker=0.002),
        "htx": FeeConfig(taker=0.002),
    })

    def taker_fee(self, exchange_id: str) -> float:
        fee_cfg = self.fees.get(exchange_id)
        return fee_cfg.taker if fee_cfg else 0.001
