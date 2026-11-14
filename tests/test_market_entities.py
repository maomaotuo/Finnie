from unittest.mock import Mock

import pytest
import src.agents.market_entity_extractor as extractor
import src.agents.market_symbol_resolver as resolver

def test_extractor_structured_and_empty(monkeypatch):
    assert extractor.extract_market_entity(' ').company is None
    monkeypatch.setattr(extractor,'get_extractor',lambda:Mock(invoke=lambda _:dict(company='Costco',symbol=None,period='1D')))
    assert extractor.extract_market_entity('Costco today').period=='1D'
    monkeypatch.setattr(extractor,'get_extractor',lambda:Mock(invoke=lambda _:extractor.MarketEntity(symbol='AAPL')))
    assert extractor.extract_market_entity('AAPL').symbol=='AAPL'

def test_extractor_model_cached(monkeypatch):
    extractor.get_extractor.cache_clear()
    model=Mock()
    monkeypatch.setattr(extractor,'get_llm',lambda:model)
    extractor.get_extractor()
    extractor.get_extractor()
    model.with_structured_output.assert_called_once()
    extractor.get_extractor.cache_clear()

def test_symbol_resolution(monkeypatch):
    quotes=[dict(symbol='COST',quoteType='EQUITY',shortname='Costco'),dict(symbol='ABC',quoteType='ETF',shortname='Other')]
    monkeypatch.setattr(resolver.yf,'Search',lambda **_:Mock(quotes=quotes))
    assert resolver.resolve_symbol(None) is None
    assert resolver.resolve_symbol('Costco')=='COST'
    assert resolver.resolve_symbol(None,'cost')=='COST'
    assert resolver.resolve_symbol(None,'UNKNOWN') is None
    assert resolver.resolve_symbol('Partial company name') is None
    monkeypatch.setattr(resolver.yf,'Search',lambda **_:Mock(quotes=[]))
    assert resolver.resolve_symbol('Unknown') is None
    monkeypatch.setattr(resolver.yf,'Search',Mock(side_effect=RuntimeError))
    assert resolver.resolve_symbol('Unknown') is None


@pytest.mark.parametrize("entity", [
    extractor.MarketEntity(company="Costco", period="1D"),
    extractor.MarketEntity(symbol="COSTCO", period="1D"),
    extractor.MarketEntity(period="1D"),
])
def test_costco_question_resolves_company_before_fetching_quote(monkeypatch, entity):
    import src.agents.market_agent as market

    monkeypatch.setattr(extractor, "extract_market_entity", Mock(return_value=entity))
    search = Mock(side_effect=RuntimeError("Search unavailable"))
    monkeypatch.setattr(resolver.yf, "Search", search)
    fetch = Mock(return_value={"error": "Quote unavailable in test"})
    monkeypatch.setattr(market, "get_market_chart", fetch)

    market.market_agent({"question": "Show me Costco stock today", "symbol": "AAPL"})
    fetch.assert_called_once_with("COST", "1D")
    search.assert_not_called()


def test_company_typo_prefers_close_company_name(monkeypatch):
    search = Mock(return_value=Mock(quotes=[
        {"symbol": "ABC", "quoteType": "EQUITY", "shortname": "Unrelated Company"},
        {"symbol": "MSFT", "quoteType": "EQUITY", "shortname": "Microsoft Corporation"},
    ]))
    monkeypatch.setattr(resolver.yf, "Search", search)
    assert resolver.resolve_symbol("Micorsoft") == "MSFT"
    assert search.call_args.kwargs["enable_fuzzy_query"] is True
    assert resolver.resolve_symbol(None, "MSFQ") is None
    assert search.call_args.kwargs["enable_fuzzy_query"] is False


def test_known_company_typo_resolves_without_search_results(monkeypatch):
    monkeypatch.setattr(resolver.yf, "Search", Mock(return_value=Mock(quotes=[])))
    assert resolver.resolve_symbol("Costoc") == "COST"


def test_misspelled_nvidia_why_question_uses_correct_quote_and_news(monkeypatch):
    import src.agents.market_agent as market

    question = "why sotock market all goes well except for Nevidia"
    monkeypatch.setattr(extractor, "extract_market_entity", Mock(return_value=
        extractor.MarketEntity(company="Nevidia", symbol="FNV", period="1D")))
    monkeypatch.setattr(resolver.yf, "Search", Mock(return_value=Mock(quotes=[
        {"symbol": "FNV", "quoteType": "EQUITY", "shortname": "Franco-Nevada Corporation"},
    ])))
    fetch = Mock(side_effect=lambda symbol, period: {
        "price_date": "2026-11-09", "change_pct": {"NVDA": -1.0, "SPY": 0.5}[symbol],
    })
    monkeypatch.setattr(market, "get_market_chart", fetch)
    news = Mock(return_value={"answer": "Company headlines", "sources": [{"url": "https://example.com"}]})
    import src.agents.news_agent as news_agent
    from src.workflow.graph import build_graph

    monkeypatch.setattr(news_agent, "summarize_company_news", news)
    graph = build_graph()
    config = {"configurable": {"thread_id": "market-news"}}
    events = list(graph.stream({"question": question, "agent_override": "market"}, config))
    assert [next(iter(event)) for event in events] == [
        "router", "market", "news", "combine_market_news", "remember",
    ]
    result = graph.get_state(config).values
    assert result["symbol"] == "NVDA"
    assert "SPY" in result["answer"] and "Company headlines" in result["answer"]
    assert "cannot by themselves establish what caused the move" in result["answer"]
    assert result["sources"]
    news.assert_called_once_with("NVDA", question, market_context=True)
    assert "NVDA changed -1.00%" in result["answer"]
    assert "changed +0.50%" in result["answer"]


@pytest.mark.parametrize("question, uses_news", [
    ("How is the U.S. stock market doing today?", False),
    ("Are U.S. stocks up or down today?", False),
    ("Why is the U.S. stock market down today?", True),
])
def test_us_market_overview_uses_benchmarks_without_a_ticker(monkeypatch, question, uses_news):
    import src.agents.market_agent as market
    import src.agents.news_agent as news
    import src.workflow.router as router
    from src.workflow.graph import build_graph

    llm = Mock(side_effect=AssertionError("Overview routing should be deterministic"))
    monkeypatch.setattr(router, "get_llm", llm)
    fetch = Mock(side_effect=lambda symbol, period: {
        "VTI": {"change_pct": -0.41, "price_date": "2026-11-10T15:55:00-05:00", "stale": True},
        "SPY": {"error": "Unavailable"},
    }[symbol])
    monkeypatch.setattr(market, "get_market_chart", fetch)
    headlines = Mock(return_value={"answer": "Recent benchmark headlines", "sources": []})
    monkeypatch.setattr(news, "summarize_company_news", headlines)

    result = build_graph().invoke(
        {"question": question, "symbol": "COST", "period": "1M"},
        {"configurable": {"thread_id": "market-overview"}},
    )
    assert result["selected_agent"] == "market"
    assert sorted(call.args for call in fetch.call_args_list) == [("SPY", "1D"), ("VTI", "1D")]
    assert "-0.41%" in result["answer"]
    assert "cached fallback" in result["answer"]
    assert "(SPY)** — session change unavailable" in result["answer"]
    assert "2026-11-10" in result["answer"]
    assert bool(result["market_comparison"]) == uses_news
    assert headlines.call_count == int(uses_news)
    llm.assert_not_called()


@pytest.mark.parametrize("quote_failed", [False, True])
def test_quote_and_news_request_answers_both_parts(monkeypatch, quote_failed):
    import src.agents.market_agent as market
    import src.agents.news_agent as news
    import src.workflow.router as router
    from src.workflow.graph import build_graph

    question = "what is NVDIA's stock price today? what news does it have today"
    monkeypatch.setattr(router, "get_llm", Mock(side_effect=AssertionError))
    monkeypatch.setattr(extractor, "extract_market_entity", Mock(return_value=
        extractor.MarketEntity(company="NVDIA", period="1D")))
    monkeypatch.setattr(resolver, "resolve_symbol", Mock(return_value="NVDA"))
    quote = {"error": "Quote unavailable"} if quote_failed else {
        "latest_price": 162.82, "currency": "USD", "change_pct": -2.03,
        "price_date": "2026-11-13", "retrieved_at": "2026-11-13",
    }
    fetch = Mock(return_value=quote)
    monkeypatch.setattr(market, "get_market_chart", fetch)
    headlines = Mock(return_value={"answer": "Nvidia headlines", "sources": [{"title": "Headline"}]})
    monkeypatch.setattr(news, "summarize_company_news", headlines)
    graph = build_graph()
    config = {"configurable": {"thread_id": "quote-and-news"}}
    result = graph.invoke({"question": question}, config)

    fetch.assert_called_once_with("NVDA", "1D")
    headlines.assert_called_once_with("NVDA", question, market_context=True, prefer_today=True)
    assert result["selected_agent"] == "market"
    assert ("Quote unavailable" if quote_failed else "162.82 USD") in result["answer"]
    assert "Nvidia headlines" in result["answer"]
    assert result["sources"] == [{"title": "Headline"}]

    following = graph.invoke({"question": "What is NVDA's stock price?", "agent_override": "market"}, config)
    assert following["market_quote"] == ""
    assert "Nvidia headlines" not in following["answer"]
    assert headlines.call_count == 1
