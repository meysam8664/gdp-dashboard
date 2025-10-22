from __future__ import annotations

import asyncio
from typing import Dict, Iterable, List, Optional, Tuple

from loguru import logger

from .exchanges.ccxt_connector import CCXTManager
from .models import (
    CrossExchangeOpportunity,
    FeeModel,
    ScanConfig,
    Ticker,
    TriangularOpportunity,
)


def _apply_fees(price: float, fee_rate: float, is_buy: bool) -> float:
    if is_buy:
        return price * (1.0 + fee_rate)
    return price * (1.0 - fee_rate)


def _safe_float(value) -> Optional[float]:
    try:
        if value is None:
            return None
        v = float(value)
        if v != v:  # NaN check
            return None
        return v
    except Exception:
        return None


async def fetch_tickers(manager: CCXTManager, exchange_ids: List[str], symbols: List[str], max_concurrency: int) -> Dict[str, Dict[str, Ticker]]:
    reqs = [(ex, sym) for ex in exchange_ids for sym in symbols]
    raw = await manager.batch_fetch_tickers(reqs, max_concurrency=max_concurrency)
    out: Dict[str, Dict[str, Ticker]] = {ex: {} for ex in exchange_ids}
    for (ex, sym), data in raw.items():
        bid = _safe_float(data.get("bid")) if data else None
        ask = _safe_float(data.get("ask")) if data else None
        ts = int(data.get("timestamp")) if data and data.get("timestamp") else None
        out[ex][sym] = Ticker(exchange_id=ex, symbol=sym, bid=bid, ask=ask, timestamp=ts)
    return out


def compute_cross_exchange_opportunities(
    tickers: Dict[str, Dict[str, Ticker]],
    symbols: List[str],
    fee_overrides: Dict[str, FeeModel],
    slippage_bps: float,
) -> List[CrossExchangeOpportunity]:
    slippage_rate = slippage_bps / 10_000.0
    opps: List[CrossExchangeOpportunity] = []
    for sym in symbols:
        # Gather bids and asks across exchanges
        best_buy: Optional[Tuple[str, float]] = None
        best_sell: Optional[Tuple[str, float]] = None
        for ex_id, ticker_map in tickers.items():
            t = ticker_map.get(sym)
            if not t:
                continue
            if t.ask is not None:
                if best_buy is None or t.ask < best_buy[1]:
                    best_buy = (ex_id, t.ask)
            if t.bid is not None:
                if best_sell is None or t.bid > best_sell[1]:
                    best_sell = (ex_id, t.bid)
        if not best_buy or not best_sell:
            continue
        buy_ex, buy_price_raw = best_buy
        sell_ex, sell_price_raw = best_sell
        if buy_ex == sell_ex:
            continue
        # Apply fees and conservative slippage estimate
        buy_fee = fee_overrides.get(buy_ex, FeeModel()).taker_fee_rate
        sell_fee = fee_overrides.get(sell_ex, FeeModel()).taker_fee_rate
        buy_price = _apply_fees(buy_price_raw * (1.0 + slippage_rate), buy_fee, is_buy=True)
        sell_price = _apply_fees(sell_price_raw * (1.0 - slippage_rate), sell_fee, is_buy=False)
        if buy_price <= 0:
            continue
        gross_spread = (sell_price_raw - buy_price_raw) / buy_price_raw
        net_spread = (sell_price - buy_price) / buy_price
        if net_spread <= 0:
            continue
        opps.append(
            CrossExchangeOpportunity(
                symbol=sym,
                buy_exchange=buy_ex,
                sell_exchange=sell_ex,
                buy_price=buy_price_raw,
                sell_price=sell_price_raw,
                gross_spread_pct=gross_spread * 100.0,
                est_net_spread_pct=net_spread * 100.0,
                est_net_profit_per_unit=(sell_price - buy_price),
            )
        )
    opps.sort(key=lambda o: o.est_net_spread_pct, reverse=True)
    return opps


def _tri_paths_from_symbols(symbols: List[str]) -> List[Tuple[str, str, str]]:
    # Build naive triangles like (BASE/QUOTE, ALT/QUOTE, ALT/BASE)
    # e.g., (BTC/USDT, ETH/USDT, ETH/BTC)
    paths: List[Tuple[str, str, str]] = []
    by_quote: Dict[str, List[Tuple[str, str]]] = {}
    for sym in symbols:
        if "/" not in sym:
            continue
        base, quote = sym.split("/")
        by_quote.setdefault(quote, []).append((base, sym))
    for quote, base_syms in by_quote.items():
        bases = {b for b, _ in base_syms}
        for b1 in bases:
            for b2 in bases:
                if b1 == b2:
                    continue
                s1 = f"{b1}/{quote}"
                s2 = f"{b2}/{quote}"
                s3 = f"{b2}/{b1}"
                if s1 in symbols and s2 in symbols and s3 in symbols:
                    paths.append((s1, s2, s3))
    # Deduplicate
    uniq = []
    seen = set()
    for p in paths:
        if p in seen:
            continue
        seen.add(p)
        uniq.append(p)
    return uniq


def compute_triangular_opportunities(
    exchange_id: str,
    ticker_map: Dict[str, Ticker],
    symbols: List[str],
    fee_model: FeeModel,
    slippage_bps: float,
) -> List[TriangularOpportunity]:
    slippage_rate = slippage_bps / 10_000.0
    paths = _tri_paths_from_symbols(symbols)
    opps: List[TriangularOpportunity] = []
    if not paths:
        return opps
    fee = fee_model.taker_fee_rate
    for s1, s2, s3 in paths:
        t1, t2, t3 = ticker_map.get(s1), ticker_map.get(s2), ticker_map.get(s3)
        if not t1 or not t2 or not t3:
            continue
        # Use conservative rates with slippage and taker fees on each hop
        if t1.ask is None or t2.bid is None:
            continue
        # Path: start with quote asset, buy base1 with quote via s1 (use ask),
        # then swap base1->base2 via s3 (if s3 quoted as base2/base1 use bid),
        # then sell base2 back to quote via s2 (use bid)
        buy1 = t1.ask * (1.0 + slippage_rate)
        # Determine if s3 is base2/base1 or base1/base2
        b2, b1_or_quote = s3.split("/")
        # s3 is base2/base1, use bid to sell base1 for base2
        if t3.bid is None or t2.bid is None:
            continue
        rate2 = t3.bid * (1.0 - slippage_rate)
        sell3 = t2.bid * (1.0 - slippage_rate)
        gross_mult = (1.0 / buy1) * rate2 * sell3
        # Apply taker fee on each hop multiplicatively
        net_mult = gross_mult * (1.0 - fee) ** 3
        if net_mult > 1.0:
            opps.append(
                TriangularOpportunity(
                    exchange_id=exchange_id,
                    path=(s1, s3, s2),
                    gross_multiplier=gross_mult,
                    est_net_multiplier=net_mult,
                    base_asset=s1.split("/")[1],
                )
            )
    opps.sort(key=lambda o: o.est_net_multiplier, reverse=True)
    return opps


async def scan_once(cfg: ScanConfig) -> Tuple[List[CrossExchangeOpportunity], Dict[str, List[TriangularOpportunity]]]:
    manager = CCXTManager(request_timeout=cfg.request_timeout_ms, retries=cfg.retries)
    try:
        tickers = await fetch_tickers(manager, cfg.exchange_ids, cfg.symbols, cfg.max_concurrency)
        cross = compute_cross_exchange_opportunities(
            tickers=tickers,
            symbols=cfg.symbols,
            fee_overrides=cfg.fee_overrides,
            slippage_bps=cfg.slippage_bps,
        )
        tri: Dict[str, List[TriangularOpportunity]] = {}
        for ex in cfg.exchange_ids:
            tri[ex] = compute_triangular_opportunities(
                exchange_id=ex,
                ticker_map=tickers.get(ex, {}),
                symbols=cfg.symbols,
                fee_model=cfg.fee_overrides.get(ex, FeeModel()),
                slippage_bps=cfg.slippage_bps,
            )
        return cross, tri
    finally:
        try:
            await manager.close_all()
        except Exception:
            logger.debug("Error during manager.close_all()")
