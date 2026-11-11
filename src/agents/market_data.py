"""
Finnie - Market Data Service

Fetch historical stock and ETF prices using yfinance.
Returns structured data for Streamlit charts.

Supported periods:
1W, 1M, 3M, 6M, 1Y, 5Y
"""

from datetime import datetime, timezone
import math

import yfinance as yf


PERIODS = {
    "1D": "1d",
    "1W": "5d",
    "1M": "1mo",
    "3M": "3mo",
    "6M": "6mo",
    "1Y": "1y",
    "5Y": "5y",
}



def _fetch_market_chart(symbol: str, period: str = "1M") -> dict:
    symbol = symbol.strip().upper()
    period = period.upper()

    if not symbol:
        return {"error": "Stock or ETF symbol is required."}

    if period not in PERIODS:
        return {"error": f"Unsupported period: {period}"}

    try:
        ticker = yf.Ticker(symbol)
        is_intraday = period == "1D"

        history = ticker.history(
            period="5d" if is_intraday else PERIODS[period],
            interval="5m" if is_intraday else "1d",
            auto_adjust=True,
            prepost=False,
        )

        if history.empty:
            return {"error": f"No market data found for {symbol}"}

        if is_intraday:
            # Use the latest available trading session.
            session_dates = history.index.date
            latest_date = session_dates[-1]
            history = history[session_dates == latest_date]

            # Previous daily close is the reference for 1D change.
            daily_history = ticker.history(
                period="10d",
                interval="1d",
                auto_adjust=True,
            )

            previous_days = daily_history[
                daily_history.index.date < latest_date
            ]

            previous_close = (
                float(previous_days["Close"].iloc[-1])
                if not previous_days.empty
                else None
            )
        else:
            previous_close = None

        prices = []

        for index, row in history.iterrows():
            close = float(row["Close"])

            if not math.isfinite(close):
                continue

            volume = float(row["Volume"])

            prices.append({
                "date": (
                    index.isoformat()
                    if is_intraday
                    else index.date().isoformat()
                ),
                "close": round(close, 2),
                "volume": (
                    int(volume)
                    if math.isfinite(volume)
                    else 0
                ),
            })

        if not prices:
            return {"error": "No valid price data found."}

        valid_closes = [
            float(row["Close"])
            for _, row in history.iterrows()
            if math.isfinite(float(row["Close"]))
        ]

        latest_close = valid_closes[-1]

        if is_intraday:
            baseline = previous_close
        else:
            baseline = valid_closes[0]

        change_pct = (
            (latest_close - baseline) / baseline * 100
            if baseline is not None and baseline > 0
            else None
        )

        try:
            currency = ticker.fast_info.get("currency") or "USD"
        except Exception:
            currency = "USD"

        return {
            "symbol": symbol,
            "period": period,
            "currency": currency,
            "latest_price": round(latest_close, 2),
            "price_date": prices[-1]["date"],
            "change_pct": (
                round(change_pct, 2)
                if change_pct is not None
                else None
            ),
            "previous_close": (
                round(previous_close, 2)
                if previous_close is not None
                else None
            ),
            "prices": prices,
            "retrieved_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

    except Exception as exc:
        return {
            "symbol": symbol,
            "error": f"Failed to retrieve market data: {exc}",
        }



# Bounded process cache shared by chat and dashboard. Never substitutes invented prices.
from collections import OrderedDict
from copy import deepcopy
from threading import RLock
from time import monotonic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.core.config import option
_cache = OrderedDict()
_cache_lock = RLock()

class MarketUnavailable(Exception):
    pass

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.3, max=2),
       retry=retry_if_exception_type(MarketUnavailable), reraise=True)
def _fetch_with_retry(symbol, period):
    result = _fetch_market_chart(symbol, period)
    if "error" in result:
        raise MarketUnavailable(result["error"])
    return result

def get_market_chart(symbol: str, period: str = "1M", *, refresh: bool = False) -> dict:
    import re
    symbol = symbol.strip().upper()
    period = period.upper()
    if not re.fullmatch(r"[A-Z0-9^][A-Z0-9.^=\-]{0,19}", symbol):
        return {"error": "Enter a valid ticker symbol."}
    if period not in PERIODS:
        return {"error": f"Unsupported period: {period}"}
    key = (symbol, period)
    # Use elapsed time for cache expiry so wall-clock changes do not affect freshness.
    now = monotonic()
    ttl = float(option("market_cache_ttl", 1800))
    with _cache_lock:
        cached = _cache.get(key)
        if cached:
            _cache.move_to_end(key)
        if cached and not refresh and now - cached[0] < ttl:
            # Give callers a copy so edits to chart data cannot alter the shared cache.
            return {**deepcopy(cached[1]), "cached": True, "stale": False}
    try:
        data = _fetch_with_retry(symbol, period)
    # If retries fail, return the last successful result with a stale-data flag.
    except MarketUnavailable:
        if cached:
            return {**deepcopy(cached[1]), "cached": True, "stale": True,
                    "warning": "Provider unavailable; showing previously retrieved data. Check the price date."}
        return {"error": "Market data is unavailable. The symbol may be invalid or the provider may be rate limited. Please retry later."}
    with _cache_lock:
        _cache[key] = (monotonic(), deepcopy(data))
        _cache.move_to_end(key)
        while len(_cache) > 128: _cache.popitem(last=False)
    return {**data, "cached": False, "stale": False}


if __name__ == "__main__":
    for symbol in ["AAPL", "MSFT", "VOO"]:
        result = get_market_chart(symbol, "1M")

        print(f"\n{'=' * 50}")
        print(f"Symbol: {symbol}")

        if "error" in result:
            print("Error:", result["error"])
            continue

        print("Latest price:", result["latest_price"])
        print("Currency:", result["currency"])
        print("Price date:", result["price_date"])
        print("1-month change:", result["change_pct"], "%")
        print("Chart points:", len(result["prices"]))
        print("First point:", result["prices"][0])
        print("Last point:", result["prices"][-1])
