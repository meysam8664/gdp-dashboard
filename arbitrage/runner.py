from __future__ import annotations

import asyncio
from typing import List, Tuple

from arbitrage.config import AppSettings
from arbitrage.exchanges.ccxt_adapter import create_adapters, CCXTExchangeAdapter
from arbitrage.logging import setup_logging, get_logger
from arbitrage.models import Opportunity
from arbitrage.scanner.cross_exchange import find_cross_exchange_opportunities
from arbitrage.scanner.triangular import find_triangular_opportunities


_LOG = get_logger(__name__)


async def _run_scan_async(settings: AppSettings) -> List[Opportunity]:
    timeout_ms = int(settings.request_timeout_seconds * 1000)
    adapters: List[CCXTExchangeAdapter] = []
    try:
        adapters = await create_adapters(settings.exchanges, timeout_ms=timeout_ms)
        cross_ops, tri_ops = await asyncio.gather(
            find_cross_exchange_opportunities(adapters, settings),
            find_triangular_opportunities(adapters, settings),
        )
        return sorted(cross_ops + tri_ops, key=lambda o: o.profit_pct, reverse=True)
    finally:
        await asyncio.gather(*[ad.close() for ad in adapters if ad])


def scan_once(settings: AppSettings) -> List[Opportunity]:
    setup_logging()
    try:
        asyncio.get_running_loop()
        # If there's already a loop, create a new task and run; but for simplicity we use new loop
        # This is uncommon in CLI/Streamlit contexts
        return asyncio.run(_run_scan_async(settings))
    except RuntimeError:
        return asyncio.run(_run_scan_async(settings))
