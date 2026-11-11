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
    assert result["sources"]
    news.assert_called_once()
    ticker, news_question = news.call_args.args
    assert ticker == "NVDA"
    assert question in news_question
    assert "NVDA changed -1.00%" in news_question
    assert "changed +0.50%" in news_question
