from __future__ import annotations

import asyncio
from typing import Dict, Iterable, List, Optional, Tuple

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

try:
    import ccxt.async_support as ccxt  # type: ignore
except Exception:  # pragma: no cover - ccxt import errors handled at runtime
    ccxt = None  # type: ignore


class CCXTManager:
    """Manages async CCXT exchange instances with caching and graceful close."""

    def __init__(self, request_timeout: int = 10_000, retries: int = 2):
        self._instances: Dict[str, "ccxt.Exchange"] = {}
        self._request_timeout = request_timeout
        self._retries = max(1, int(retries))

    async def get(self, exchange_id: str):
        if ccxt is None:
            raise RuntimeError("ccxt is not installed or failed to import")
        if exchange_id in self._instances:
            return self._instances[exchange_id]
        if not hasattr(ccxt, exchange_id):
            raise ValueError(f"Unknown exchange id: {exchange_id}")
        klass = getattr(ccxt, exchange_id)
        inst = klass({
            "enableRateLimit": True,
            "timeout": self._request_timeout,
        })
        # Load markets lazily on first use of fetch_ticker
        self._instances[exchange_id] = inst
        return inst

    async def ensure_markets(self, exchange_id: str):
        ex = await self.get(exchange_id)
        if getattr(ex, "markets", None):
            return
        try:
            await ex.load_markets()
        except Exception as e:
            logger.warning(f"load_markets failed for {exchange_id}: {e}")

    async def fetch_ticker(self, exchange_id: str, symbol: str) -> Optional[dict]:
        ex = await self.get(exchange_id)

        @retry(
            reraise=True,
            stop=stop_after_attempt(1),  # default; we'll loop manually based on self._retries to keep async context
            wait=wait_exponential(multiplier=0.2, min=0.2, max=1.5),
            retry=retry_if_exception_type(Exception),
        )
        async def _attempt() -> Optional[dict]:
            await self.ensure_markets(exchange_id)
            unified = symbol
            if getattr(ex, "market", None):
                try:
                    unified = ex.market(symbol)["symbol"]
                except Exception:
                    pass
            return await ex.fetch_ticker(unified)

        last_error: Optional[Exception] = None
        for i in range(self._retries):
            try:
                return await _attempt()
            except Exception as e:
                last_error = e
                logger.debug(f"fetch_ticker error {exchange_id} {symbol} (attempt {i+1}/{self._retries}): {e}")
                await asyncio.sleep(min(1.5, 0.2 * (2 ** i)))
        logger.debug(f"fetch_ticker failed after {self._retries} attempts: {exchange_id} {symbol}: {last_error}")
        return None

    async def batch_fetch_tickers(self, requests: List[Tuple[str, str]], max_concurrency: int = 10) -> Dict[Tuple[str, str], Optional[dict]]:
        sem = asyncio.Semaphore(max_concurrency)
        results: Dict[Tuple[str, str], Optional[dict]] = {}

        async def _one(ex_id: str, sym: str):
            async with sem:
                res = await self.fetch_ticker(ex_id, sym)
                results[(ex_id, sym)] = res

        await asyncio.gather(*[_one(e, s) for e, s in requests])
        return results

    async def close_all(self):
        tasks = []
        for ex in list(self._instances.values()):
            try:
                tasks.append(ex.close())
            except Exception:
                pass
        self._instances.clear()
        if tasks:
            try:
                await asyncio.gather(*tasks)
            except Exception:
                pass
