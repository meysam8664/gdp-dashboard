from __future__ import annotations

import asyncio
from typing import Dict, List, Optional, Tuple

from arbitrage.config import AppSettings
from arbitrage.exchanges.ccxt_adapter import CCXTExchangeAdapter
from arbitrage.logging import get_logger
from arbitrage.models import Opportunity, OrderBook, simulate_buy_with_quote_budget, simulate_sell_base_for_quote


_LOG = get_logger(__name__)


def _pair_key(symbol: str) -> Tuple[str, str]:
    base, quote = symbol.split("/")
    return base, quote


async def _collect_books_for_exchange(ad: CCXTExchangeAdapter, symbols: List[str]) -> Dict[str, OrderBook]:
    books: Dict[str, OrderBook] = {}
    async def f(sym: str):
        if not ad.has_symbol(sym):
            return
        ob = await ad.fetch_order_book(sym)
        if ob and ob.bids and ob.asks:
            books[sym] = ob
    await asyncio.gather(*[f(s) for s in symbols])
    return books


def _try_triangle(
    start_quote: str,
    amount_start_quote: float,
    ob_ab: OrderBook,  # A/B => price in B per A
    ob_bc: OrderBook,  # B/C
    ob_ac: OrderBook,  # A/C
    fee: float,
) -> Optional[Opportunity]:
    # The triangle path options starting and ending in C (start_quote)
    # We want C = start_quote. If A/C exists, it means price in C per A.
    A, B = _pair_key(ob_ab.symbol)
    b2, C = _pair_key(ob_bc.symbol)
    a2, c2 = _pair_key(ob_ac.symbol)
    if b2 != B or a2 != A or c2 != C:
        return None

    # Path 1: C -> A (buy A with C via A/C asks), A -> B (sell A for B via A/B bids), B -> C (sell B for C via B/C bids)
    # Step 1: buy A with C using A/C asks
    fill_a = simulate_buy_with_quote_budget(ob_ac, amount_start_quote)
    if not fill_a:
        return None
    fill_a_cost = fill_a.spent_quote * (1 + fee)  # taker fee on buy

    # Step 2: sell A for B using A/B bids
    proceeds_b = simulate_sell_base_for_quote(ob_ab, fill_a.filled_base)
    if not proceeds_b:
        return None
    proceeds_b_after_fee = proceeds_b.received_quote * (1 - fee)

    # Step 3: sell B for C using B/C bids
    # We need to sell B amount for C, so construct a fake orderbook where price=C per B and bids from ob_bc
    proceeds_c = simulate_sell_base_for_quote(ob_bc, proceeds_b_after_fee)  # treating B as base
    if not proceeds_c:
        return None
    proceeds_c_after_fee = proceeds_c.received_quote * (1 - fee)

    profit_abs = proceeds_c_after_fee - fill_a_cost
    profit_pct = profit_abs / fill_a_cost if fill_a_cost > 0 else 0.0

    if profit_pct <= 0:
        return None

    return Opportunity(
        kind="triangular",
        symbol=f"{A}/{C} | {A}/{B} | {B}/{C}",
        amount_quote=fill_a_cost,
        profit_abs_quote=profit_abs,
        profit_pct=profit_pct,
        path=[(ob_ac.symbol, "BUY"), (ob_ab.symbol, "SELL"), (ob_bc.symbol, "SELL")],
    )


async def find_triangular_opportunities(
    adapters: List[CCXTExchangeAdapter],
    settings: AppSettings,
) -> List[Opportunity]:
    if not settings.include_triangular:
        return []

    start_quote = "USDT"  # We limit triangles around USDT for tractability

    opportunities: List[Opportunity] = []

    for ad in adapters:
        # Build a small candidate set from markets: pick a few bases seen with USDT and their cross-pairs
        markets = ad.markets if hasattr(ad, "markets") else {}
        bases = [base for (base, quote) in (s.split("/") for s in markets.keys()) if quote == start_quote]
        # Limit breadth to keep it fast
        bases = sorted(set(bases))[:8]
        # Gather symbols: A/USDT for A in bases; Then for every pair of bases A,B include A/B if exists (in any orientation)
        candidate_symbols: List[str] = []
        for base in bases:
            sym = f"{base}/{start_quote}"
            if sym in markets:
                candidate_symbols.append(sym)
        for i in range(len(bases)):
            for j in range(i + 1, len(bases)):
                a, b = bases[i], bases[j]
                if f"{a}/{b}" in markets:
                    candidate_symbols.append(f"{a}/{b}")
                if f"{b}/{a}" in markets:
                    candidate_symbols.append(f"{b}/{a}")

        if not candidate_symbols:
            continue

        books = await _collect_books_for_exchange(ad, candidate_symbols)
        fee = settings.taker_fee(ad.exchange_id)

        # Build triangles: for each pair A,B among bases, need A/B (or B/A) and A/USDT, B/USDT
        for i in range(len(bases)):
            for j in range(i + 1, len(bases)):
                A, B = bases[i], bases[j]
                sym_ac = f"{A}/{start_quote}"
                sym_bc = f"{B}/{start_quote}"
                if sym_ac not in books or sym_bc not in books:
                    continue
                # choose direction that matches available cross symbol
                if f"{A}/{B}" in books:
                    ob_ab = books[f"{A}/{B}"]
                    ob_bc = books[sym_bc]  # B/C
                    ob_ac = books[sym_ac]  # A/C
                    maybe = _try_triangle(start_quote, settings.amount_quote, ob_ab, ob_bc, ob_ac, fee)
                    if maybe and maybe.profit_pct >= settings.min_profit_pct:
                        opportunities.append(maybe)
                elif f"{B}/{A}" in books:
                    # We have B/A, but _try_triangle expects A/B and B/C and A/C; we can skip for brevity
                    continue

    opportunities.sort(key=lambda o: o.profit_pct, reverse=True)
    return opportunities
