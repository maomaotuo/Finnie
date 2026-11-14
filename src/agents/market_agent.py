"""Market node reuses the validated, cached chart data service."""
import re
from concurrent.futures import ThreadPoolExecutor

from src.agents.market_data import get_market_chart
from src.agents.base_agent import DISCLAIMER
from src.agents.market_overview import is_market_overview

_US_BENCHMARKS = (
    ("VTI", "Broad U.S. stock market"),
    ("SPY", "S&P 500 large-cap stocks"),
)


def requests_quote_and_news(question):
    """Recognize explicit requests for both a quote and headlines."""
    return bool(
        re.search(r"\b(?:price|quote|trading at|how much (?:is|does))\b", question, re.IGNORECASE)
        and re.search(r"\b(?:news|headlines)\b", question, re.IGNORECASE)
    )


def _us_market_overview(question):
    with ThreadPoolExecutor(max_workers=len(_US_BENCHMARKS)) as pool:
        quotes = list(pool.map(lambda item: get_market_chart(item[0], "1D"), _US_BENCHMARKS))

    rows = []
    available = False
    for (symbol, label), quote in zip(_US_BENCHMARKS, quotes):
        change = quote.get("change_pct")
        if change is None:
            rows.append(f"- **{label} ({symbol})** — session change unavailable.")
            continue
        available = True
        cached = " · cached fallback" if quote.get("stale") else ""
        rows.append(f"- **{label} ({symbol})** — {change:+.2f}% as of `{quote['price_date']}`{cached}")

    if not available:
        return {"answer": "U.S. market session changes are temporarily unavailable. Please try again shortly."}

    overview = (
        "**U.S. stocks · Latest available trading session**\n\n"
        + "\n".join(rows)
        + "\n\nYahoo Finance via yfinance. ETF moves are measured from the prior close. "
          "Quotes may be delayed. When markets are closed, dates reflect the latest available session."
    )
    if re.match(r"why\b", question.strip(), re.IGNORECASE):
        return {"symbol": "SPY", "period": "1D", "market_comparison": overview}
    return {"answer": f"{overview}\n\n{DISCLAIMER}"}

def market_agent(state):
    symbol=state.get("symbol", "")
    period=state.get("period", "1M")
    question = state.get("question", "")
    if is_market_overview(question):
        return _us_market_overview(question)
    # An asset named in this turn takes priority over the ticker saved in the dashboard.
    if question.strip():
        from src.agents.market_entity_extractor import extract_market_entity
        from src.agents.market_symbol_resolver import resolve_symbol

        entity = extract_market_entity(question)
        period = entity.period
        if entity.company or entity.symbol:
            explicit_symbol = entity.symbol
            if explicit_symbol and not re.search(
                rf"(?<![\w.-]){re.escape(explicit_symbol)}(?![\w.-])", question, re.IGNORECASE
            ):
                explicit_symbol = None
            symbol = resolve_symbol(entity.company, explicit_symbol)
        elif re.search(r"\bcostco\b", question, re.IGNORECASE):
            symbol = resolve_symbol("Costco")
    if not symbol:
        return {"answer": "I couldn't identify a listed stock or ETF. Try a company name or ticker such as Costco or COST."}
    include_news = requests_quote_and_news(question)
    data=get_market_chart(symbol,period)
    if "error" in data:
        if include_news:
            return {"symbol": symbol, "period": period, "market_data": data,
                    "market_quote": f"{symbol} quote: {data['error']}"}
        return {"answer": data["error"], "market_data": data}
    change=f"{data['change_pct']:+.2f}%" if data['change_pct'] is not None else "unavailable"
    if re.search(r"\bwhy\b", question, re.IGNORECASE):
        benchmark = data if symbol == "SPY" else get_market_chart("SPY", period)
        comparison = f"Over {period}, {symbol} changed {change} through {data['price_date']}."
        if benchmark.get("change_pct") is not None:
            comparison += (
                f" SPY, a proxy for large U.S. stocks, changed "
                f"{benchmark['change_pct']:+.2f}% through {benchmark['price_date']}."
            )
        if (
            symbol != "SPY"
            and data["change_pct"] is not None and data["change_pct"] < 0
            and benchmark.get("change_pct") is not None and benchmark["change_pct"] < 0
            and data["price_date"][:10] == benchmark["price_date"][:10]
        ):
            comparison += " Both fell over this window."
        return {"symbol": symbol, "period": period, "market_data": data,
                "market_comparison": comparison}
    quote = (
        f"{symbol}: latest available price {data['latest_price']:,.2f} {data['currency']}. "
        f"Change over {period}: {change}. Price timestamp: {data['price_date']}. "
        f"Retrieved: {data['retrieved_at']}. Prices may be delayed and historical prices are adjusted. "
        + (data.get("warning", ""))
        + f"\n\n**Example:** At the displayed quote, one share of {symbol} would cost "
          f"{data['latest_price']:,.2f} {data['currency']} before any fees."
    )
    result = {"symbol": symbol, "period": period, "market_data": data}
    if include_news:
        return {**result, "market_quote": quote}
    return {**result, "answer": f"{quote}\n\n{DISCLAIMER}"}
