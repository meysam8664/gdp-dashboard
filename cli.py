from __future__ import annotations

import argparse
from typing import List

from arbitrage.config import AppSettings
from arbitrage.runner import scan_once


def parse_args() -> AppSettings:
    parser = argparse.ArgumentParser(description="Arbitrage opportunity scanner")
    parser.add_argument("--exchanges", type=str, default=",".join(AppSettings().exchanges), help="Comma-separated ccxt exchange ids")
    parser.add_argument("--symbols", type=str, default=",".join(AppSettings().symbols), help="Comma-separated trading symbols (e.g., BTC/USDT,ETH/USDT)")
    parser.add_argument("--amount-quote", type=float, default=AppSettings().amount_quote, help="Quote currency amount per trade (e.g., USDT)")
    parser.add_argument("--min-profit-pct", type=float, default=AppSettings().min_profit_pct, help="Minimum profit % to display (0.01 = 1%)")
    parser.add_argument("--no-triangular", action="store_true", help="Disable triangular scanning")

    ns = parser.parse_args()
    settings = AppSettings(
        exchanges=[x.strip() for x in ns.exchanges.split(",") if x.strip()],
        symbols=[x.strip().upper() for x in ns.symbols.split(",") if x.strip()],
        amount_quote=ns.amount_quote,
        min_profit_pct=ns.min_profit_pct,
        include_triangular=(not ns.no_triangular),
    )
    return settings


def main() -> None:
    settings = parse_args()
    ops = scan_once(settings)
    if not ops:
        print("No opportunities found.")
        return
    print(f"Found {len(ops)} opportunities:")
    for o in ops[:50]:
        if o.kind == "cross":
            print(
                f"[CROSS] {o.symbol} | buy:{o.buy_exchange} sell:{o.sell_exchange} "
                f"profit:{o.profit_pct*100:.2f}% abs:{o.profit_abs_quote:.2f} on {o.amount_quote:.2f}"
            )
        else:
            path = " -> ".join([f"{s}:{side}" for s, side in (o.path or [])])
            print(
                f"[TRI] {path} | profit:{o.profit_pct*100:.2f}% abs:{o.profit_abs_quote:.2f} "
                f"on {o.amount_quote:.2f}"
            )


if __name__ == "__main__":
    main()
