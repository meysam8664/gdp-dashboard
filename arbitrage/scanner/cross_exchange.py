from __future__ import annotations

import asyncio
from typing import Dict, List

from arbitrage.config import AppSettings
from arbitrage.exchanges.ccxt_adapter import CCXTExchangeAdapter
from arbitrage.logging import get_logger
from arbitrage.models import Opportunity, simulate_buy_with_quote_budget, simulate_sell_base_for_quote, OrderBook


_LOG = get_logger(__name__)


async def _fetch_symbol_books(adapters: List[CCXTExchangeAdapter], symbol: str) -> Dict[str, OrderBook]:
    results: Dict[str, OrderBook] = {}

    async def fetch_one(ad: CCXTExchangeAdapter):
        if not ad.has_symbol(symbol):
            return
        ob = await ad.fetch_order_book(symbol)
        if ob and ob.bids and ob.asks:
            results[ad.exchange_id] = ob

    await asyncio.gather(*[fetch_one(ad) for ad in adapters])
    return results


async def find_cross_exchange_opportunities(
    adapters: List[CCXTExchangeAdapter],
    settings: AppSettings,
) -> List[Opportunity]:
    ops: List[Opportunity] = []

    for symbol in settings.symbols:
        books_by_ex = await _fetch_symbol_books(adapters, symbol)
        if len(books_by_ex) < 2:
            continue

        # Pre-compute buy/sell fills for each exchange
        fills = {}
        proceeds = {}
        for ex_id, ob in books_by_ex.items():
            fill = simulate_buy_with_quote_budget(ob, settings.amount_quote * (1 - 1e-9))
            if not fill:
                continue
            fees_buy = settings.taker_fee(ex_id)
            # Apply taker fee on the quote spent: cost increases by (1+fee)
            fill_cost_with_fee = fill.spent_quote * (1 + fees_buy)
            fills[ex_id] = (fill, fill_cost_with_fee)

        for ex_id, ob in books_by_ex.items():
            buy_fill_tuple = fills.get(ex_id)
            if not buy_fill_tuple:
                continue
            base_to_sell = buy_fill_tuple[0].filled_base
            proceeds_sell = simulate_sell_base_for_quote(ob, base_to_sell)
            if not proceeds_sell:
                continue
            fees_sell = settings.taker_fee(ex_id)
            proceeds_with_fee = proceeds_sell.received_quote * (1 - fees_sell)
            proceeds[ex_id] = (proceeds_sell, proceeds_with_fee)

        # Evaluate all pairs buy on A, sell on B
        for buy_ex, (buy_fill, buy_cost_q) in fills.items():
            for sell_ex, (sell_proceeds, sell_quote_q) in proceeds.items():
                if buy_ex == sell_ex:
                    continue
                profit_abs = sell_quote_q - buy_cost_q
                if buy_cost_q <= 0:
                    continue
                profit_pct = profit_abs / buy_cost_q
                if profit_pct >= settings.min_profit_pct:
                    ops.append(Opportunity(
                        kind="cross",
                        symbol=symbol,
                        amount_quote=buy_cost_q,
                        profit_abs_quote=profit_abs,
                        profit_pct=profit_pct,
                        buy_exchange=buy_ex,
                        sell_exchange=sell_ex,
                        effective_buy_price=buy_fill.avg_price_buy,
                        effective_sell_price=sell_proceeds.avg_price_sell,
                    ))
    # Sort descending by profit
    ops.sort(key=lambda o: o.profit_pct, reverse=True)
    return ops
