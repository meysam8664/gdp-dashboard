from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple
from datetime import datetime, timezone


@dataclass
class OrderLevel:
    price: float  # price denominated in quote per base
    amount_base: float  # amount in base asset available at price


@dataclass
class OrderBook:
    symbol: str
    bids: List[OrderLevel]
    asks: List[OrderLevel]
    timestamp_ms: Optional[int] = None


@dataclass
class Opportunity:
    kind: str  # "cross" or "triangular"
    symbol: str
    amount_quote: float
    profit_abs_quote: float
    profit_pct: float
    buy_exchange: Optional[str] = None
    sell_exchange: Optional[str] = None
    effective_buy_price: Optional[float] = None  # quote per base
    effective_sell_price: Optional[float] = None  # quote per base
    path: Optional[List[Tuple[str, str]]] = None  # [(symbol, side)] for triangular
    timestamp: datetime = datetime.now(timezone.utc)


@dataclass
class LiquidityFill:
    filled_base: float
    spent_quote: float
    avg_price_buy: float


@dataclass
class LiquidityProceeds:
    sold_base: float
    received_quote: float
    avg_price_sell: float


def simulate_buy_with_quote_budget(orderbook: OrderBook, quote_budget: float) -> Optional[LiquidityFill]:
    remaining_quote = quote_budget
    acquired_base = 0.0
    for lvl in orderbook.asks:
        if remaining_quote <= 0:
            break
        max_base_at_level = remaining_quote / lvl.price
        take_base = min(lvl.amount_base, max_base_at_level)
        cost_quote = take_base * lvl.price
        remaining_quote -= cost_quote
        acquired_base += take_base
    if acquired_base <= 0:
        return None
    spent_quote = quote_budget - max(0.0, remaining_quote)
    avg_price = spent_quote / acquired_base
    return LiquidityFill(filled_base=acquired_base, spent_quote=spent_quote, avg_price_buy=avg_price)


def simulate_sell_base_for_quote(orderbook: OrderBook, base_amount: float) -> Optional[LiquidityProceeds]:
    remaining_base = base_amount
    got_quote = 0.0
    for lvl in orderbook.bids:
        if remaining_base <= 0:
            break
        take_base = min(lvl.amount_base, remaining_base)
        proceeds_quote = take_base * lvl.price
        remaining_base -= take_base
        got_quote += proceeds_quote
    if base_amount <= 0:
        return None
    if remaining_base > 1e-12:
        # not enough liquidity to sell all base_amount
        return None
    avg_price = got_quote / base_amount
    return LiquidityProceeds(sold_base=base_amount, received_quote=got_quote, avg_price_sell=avg_price)
