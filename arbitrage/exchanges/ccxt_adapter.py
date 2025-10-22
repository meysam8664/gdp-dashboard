from __future__ import annotations

import asyncio
from typing import Dict, Optional, List

import ccxt.async_support as ccxt
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from arbitrage.logging import get_logger
from arbitrage.models import OrderBook, OrderLevel


_LOG = get_logger(__name__)


class CCXTExchangeAdapter:
    def __init__(self, exchange_id: str, *, timeout_ms: int = 10000, enable_rate_limit: bool = True) -> None:
        self.exchange_id = exchange_id
        self.exchange = getattr(ccxt, exchange_id)({
            "timeout": timeout_ms,
            "enableRateLimit": enable_rate_limit,
        })
        self._markets_loaded = False

    async def load_markets(self) -> Dict:
        if not self._markets_loaded:
            _LOG.info("[%s] Loading markets", self.exchange_id)
            self.markets = await self.exchange.load_markets(reload=True)
            self._markets_loaded = True
        return self.markets

    def has_symbol(self, symbol: str) -> bool:
        return self._markets_loaded and symbol in self.markets

    async def fetch_order_book(self, symbol: str, *, limit: int = 20) -> Optional[OrderBook]:
        async for attempt in AsyncRetrying(
            retry=retry_if_exception_type(Exception),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
            stop=stop_after_attempt(3),
            reraise=False,
        ):
            with attempt:
                try:
                    ob = await self.exchange.fetch_order_book(symbol, limit=limit)
                    bids = [OrderLevel(price=float(p), amount_base=float(a)) for p, a in ob.get("bids", [])]
                    asks = [OrderLevel(price=float(p), amount_base=float(a)) for p, a in ob.get("asks", [])]
                    return OrderBook(symbol=symbol, bids=bids, asks=asks, timestamp_ms=ob.get("timestamp"))
                except Exception as e:
                    _LOG.warning("[%s] fetch_order_book failed for %s: %s", self.exchange_id, symbol, e)
                    raise
        return None

    async def close(self) -> None:
        try:
            await self.exchange.close()
        except Exception:
            pass


async def create_adapters(exchange_ids: List[str], *, timeout_ms: int = 10000) -> List[CCXTExchangeAdapter]:
    adapters = [CCXTExchangeAdapter(eid, timeout_ms=timeout_ms) for eid in exchange_ids]
    await asyncio.gather(*[ad.load_markets() for ad in adapters])
    return adapters
