"""
Finnie - Market Symbol Resolver

Resolve company names and explicit tickers
using Yahoo Finance search.
"""

import logging
from difflib import SequenceMatcher, get_close_matches

import yfinance as yf


# Verified against https://investor.costco.com/company-profile/.
COMPANY_ALIASES = {
    "costco": "COST",
    # Verified against NVIDIA Investor Relations FAQs.
    "nvidia": "NVDA",
    "costco wholesale": "COST",
    "costco wholesale corporation": "COST",
}

SUPPORTED_TYPES = {"EQUITY", "ETF", "MUTUALFUND"}


def resolve_symbol(
    company: str | None,
    explicit_symbol: str | None = None,
) -> str | None:
    """
    Resolve an asset to a Yahoo Finance ticker.

    Examples:
        Costco -> COST
        Nvidia -> NVDA
        AAPL -> AAPL
        VOO -> VOO
    """

    query = (explicit_symbol or company or "").strip()

    if not query:
        return None

    alias = COMPANY_ALIASES.get(query.casefold())
    if alias:
        return alias

    # Use known company names as a fallback when the provider returns no matches.
    nearby_aliases = (
        get_close_matches(query.casefold(), COMPANY_ALIASES, n=1, cutoff=0.8)
        if not explicit_symbol and len(query) >= 5 else []
    )
    local_match = COMPANY_ALIASES[nearby_aliases[0]] if nearby_aliases else None

    try:
        search = yf.Search(
            query=query,
            max_results=10,
            news_count=0,
            enable_fuzzy_query=not explicit_symbol,
        )

        candidates = [
            quote
            for quote in search.quotes
            if quote.get("symbol")
            and quote.get("quoteType") in SUPPORTED_TYPES
        ]

        if not candidates:
            if explicit_symbol and company and company.casefold().strip() != query.casefold():
                return resolve_symbol(company)
            return local_match

        if explicit_symbol:
            normalized = explicit_symbol.upper().strip()

            # Require exact match for explicit tickers.
            for quote in candidates:
                if quote["symbol"].upper() == normalized:
                    return quote["symbol"]

            # A company name can be misclassified as a ticker, especially in all caps.
            if company and company.casefold().strip() != query.casefold():
                return resolve_symbol(company)
            company = company or query

        # Company-name search: prefer exact name matches.
        normalized_company = company.lower().strip()

        for quote in candidates:
            name = (
                quote.get("shortname")
                or quote.get("longname")
                or ""
            ).lower()

            if quote["symbol"].casefold() == normalized_company or name == normalized_company:
                return quote["symbol"]

        # Prefer a matching company-name prefix for names like "Toyota".
        for quote in candidates:
            for field in ("shortname", "longname"):
                name = (quote.get(field) or "").casefold()
                if name.startswith(normalized_company + " "):
                    return quote["symbol"]
        if explicit_symbol:
            return None
        # A closely matching company name can outrank unrelated search suggestions.
        best_symbol, best_score = local_match, 0.8
        for quote in candidates:
            for field in ("shortname", "longname"):
                name = (quote.get(field) or "").casefold().strip()
                if not name:
                    continue
                score = max(
                    SequenceMatcher(None, normalized_company, name).ratio(),
                    SequenceMatcher(None, normalized_company, name.split()[0]).ratio(),
                )
                if score > best_score:
                    best_symbol, best_score = quote["symbol"], score
        return best_symbol

    except Exception as exc:
        logging.getLogger(__name__).warning("Symbol resolution failed (%s)", type(exc).__name__)
        return local_match


if __name__ == "__main__":
    tests = [
        ("Costco", None),
        ("Nvidia", None),
        ("Microsoft", None),
        ("Toyota", None),
        (None, "AAPL"),
        (None, "VOO"),
        ("NonexistentCompanyXYZ123", None),
    ]

    for company, symbol in tests:
        resolved = resolve_symbol(company, symbol)
        print(
            f"Company={company}, "
            f"Ticker={symbol} -> {resolved}"
        )
