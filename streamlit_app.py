import streamlit as st
import pandas as pd
from dataclasses import asdict

from arbitrage.config import AppSettings
from arbitrage.runner import scan_once


st.set_page_config(page_title="Arbitrage Scanner", page_icon=":money_with_wings:")

st.title(":money_with_wings: Arbitrage Opportunity Scanner")
st.caption("Cross-exchange and triangular scanner using CCXT")

st.sidebar.header("Configuration")
default = AppSettings()

exchanges = st.sidebar.multiselect(
    "Exchanges (ccxt ids)",
    options=["binance", "kucoin", "bybit", "okx", "gate", "htx"],
    default=default.exchanges,
)

symbols_str = st.sidebar.text_input(
    "Symbols (comma-separated)",
    value=",".join(default.symbols),
    help="e.g., BTC/USDT,ETH/USDT",
)

amount_quote = st.sidebar.number_input(
    "Quote amount per trade (e.g., USDT)", min_value=10.0, max_value=200000.0, value=float(default.amount_quote), step=10.0
)

min_profit_pct = st.sidebar.slider(
    "Minimum profit (%)",
    min_value=0.0,
    max_value=5.0,
    value=default.min_profit_pct * 100,
    step=0.05,
)

include_triangular = st.sidebar.checkbox("Include triangular opportunities", value=default.include_triangular)

run_btn = st.sidebar.button("Scan now")

if run_btn:
    settings = AppSettings(
        exchanges=exchanges,
        symbols=[s.strip().upper() for s in symbols_str.split(",") if s.strip()],
        amount_quote=float(amount_quote),
        min_profit_pct=min_profit_pct / 100.0,
        include_triangular=include_triangular,
    )

    with st.status("Scanning exchanges...", expanded=True) as status:
        st.write(f"Exchanges: {', '.join(settings.exchanges)}")
        st.write(f"Symbols: {', '.join(settings.symbols)} | Amount: {settings.amount_quote}")
        try:
            ops = scan_once(settings)
            status.update(label="Scan complete", state="complete")
        except Exception as e:
            status.update(label="Scan failed", state="error")
            st.exception(e)
            ops = []

    if ops:
        df = pd.DataFrame([
            {
                "type": o.kind,
                "symbol": o.symbol,
                "buy_exchange": o.buy_exchange,
                "sell_exchange": o.sell_exchange,
                "profit_%": round(o.profit_pct * 100, 3),
                "profit_abs": round(o.profit_abs_quote, 4),
                "amount_quote": round(o.amount_quote, 4),
                "buy_price": round(o.effective_buy_price or 0, 8),
                "sell_price": round(o.effective_sell_price or 0, 8),
                "path": " -> ".join([f"{s}:{side}" for s, side in (o.path or [])]) if o.path else "",
            }
            for o in ops
        ])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No opportunities found with current settings.")
else:
    st.info("Configure settings in the sidebar and click 'Scan now'.")
