import asyncio
from typing import Dict, List

import streamlit as st
from loguru import logger

from arbitrage.engine import scan_once
from arbitrage.models import FeeModel, ScanConfig

# Optimize asyncio loop for Linux
try:
    import uvloop  # type: ignore
    uvloop.install()
except Exception:
    pass


st.set_page_config(
    page_title="آربیتراژ یار حرفه‌ای",
    page_icon=":money_with_wings:",
    layout="wide",
)


@st.cache_resource
def get_default_exchanges() -> List[str]:
    # A conservative default set; some exchanges may be geo/region restricted
    return [
        "binance",
        "kraken",
        "kucoin",
        "bybit",
        "okx",
    ]


@st.cache_resource
def get_default_pairs() -> List[str]:
    return [
        "BTC/USDT",
        "ETH/USDT",
        "SOL/USDT",
        "XRP/USDT",
        "ETH/BTC",
    ]


st.markdown(
    """
    # آربیتراژ یار حرفه‌ای
    موتور هوشمند کشف فرصت‌های آربیتراژ بین صرافی‌ها و داخل هر صرافی.
    """
)

with st.sidebar:
    st.header("پیکربندی")
    exchanges = st.multiselect("صرافی‌ها", options=get_default_exchanges(), default=get_default_exchanges())
    pairs = st.multiselect("نمادها (Symbols)", options=get_default_pairs(), default=get_default_pairs())
    slippage_bps = st.slider("اسلیپیج (bps)", 0, 100, 10, step=5)
    taker_fee_bps = st.slider("کارمزد تیکر عمومی (bps)", 0, 50, 10, step=5)
    auto_refresh = st.toggle("اسکن خودکار هر ۳۰ ثانیه")
    if auto_refresh:
        st.autorefresh(interval=30_000, key="auto_refresh")

fee_overrides: Dict[str, FeeModel] = {ex: FeeModel(taker_fee_rate=taker_fee_bps / 10_000.0) for ex in exchanges}

st.divider()

cols = st.columns([1, 1])
scan_clicked = cols[0].button("اسکن کن", use_container_width=True)
reset_clicked = cols[1].button("پاک‌سازی نتایج", use_container_width=True)

if reset_clicked:
    st.session_state.pop("last_results", None)

should_scan = scan_clicked or auto_refresh

if should_scan and exchanges and pairs:
    with st.spinner("در حال اسکن همزمان بازارها..."):
        cfg = ScanConfig(
            exchange_ids=exchanges,
            symbols=pairs,
            fee_overrides=fee_overrides,
            max_concurrency=10,
            request_timeout_ms=12_000,
            retries=1,
            slippage_bps=slippage_bps,
        )
        try:
            cross, tri = asyncio.run(scan_once(cfg))
            st.session_state["last_results"] = {"cross": cross, "tri": tri}
        except Exception as e:
            st.error(f"خطا در اسکن: {e}")

results = st.session_state.get("last_results")

if results:
    cross = results.get("cross", [])
    tri = results.get("tri", {})

    st.subheader("فرصت‌های بین صرافی (Cross-Exchange)")
    if not cross:
        st.info("فعلا فرصتی یافت نشد.")
    else:
        import pandas as pd

        df = pd.DataFrame([
            {
                "نماد": o.symbol,
                "صرافی خرید": o.buy_exchange,
                "قیمت خرید": o.buy_price,
                "صرافی فروش": o.sell_exchange,
                "قیمت فروش": o.sell_price,
                "اسپرد ناخالص %": round(o.gross_spread_pct, 3),
                "اسپرد خالص %": round(o.est_net_spread_pct, 3),
                "سود خالص به ازای هر واحد": round(o.est_net_profit_per_unit, 6),
            }
            for o in cross
        ])
        st.dataframe(df, use_container_width=True)

    st.subheader("فرصت‌های مثلثی داخل صرافی (Triangular)")
    empty = True
    for ex_id, opps in tri.items():
        if not opps:
            continue
        empty = False
        with st.expander(f"{ex_id}"):
            import pandas as pd

            df = pd.DataFrame([
                {
                    "مسیر": " -> ".join(o.path),
                    "ضریب ناخالص": round(o.gross_multiplier, 6),
                    "ضریب خالص": round(o.est_net_multiplier, 6),
                    "دارایی مبنا": o.base_asset,
                }
                for o in opps
            ])
            st.dataframe(df, use_container_width=True)
    if empty:
        st.info("فرصت مثلثی قابل نمایش پیدا نشد.")

st.caption(
    "هشدار: این ابزار صرفا جهت تحلیل و کشف فرصت‌ها است و اجرای معامله و انتقال بین صرافی‌ها را انجام نمی‌دهد. ریسک‌ها (کارمزد برداشت/واریز، تأخیر شبکه، محدودیت برداشت، KYC و ...) را قبل از هر اقدامی بسنجید."
)

