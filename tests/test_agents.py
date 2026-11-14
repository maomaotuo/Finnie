from unittest.mock import Mock
import pytest
from langchain_core.documents import Document
from src.agents.goal_agent import goal_agent
from src.agents.portfolio_agent import portfolio_agent
import src.agents.base_agent as base
import src.agents.finance_qa_agent as qa
import src.rag.pipeline as rag
import src.agents.market_agent as market
import src.agents.news_agent as news
from src.agents.tax_agent import tax_agent

def test_goal_agent():
    assert 'Goals tab' in goal_agent({})['answer']
    r=goal_agent({'goal':dict(target=1200,years=1,annual_return_pct=0,monthly=100)})
    assert r['goal_analysis']['on_track']
    assert 'month end' in r['answer']

def test_portfolio_fallback(monkeypatch):
    monkeypatch.setattr(base,'get_llm',Mock(side_effect=RuntimeError))
    assert 'Portfolio tab' in portfolio_agent({})['answer']
    r=portfolio_agent({'question':'Analyze','portfolio':[dict(symbol='A',quantity=1,price=100,asset_type='stock')]})
    assert r['portfolio_analysis']['total_value']==100
    assert '100.00' in r['answer']

def test_generate_and_context(monkeypatch):
    monkeypatch.setattr(base,'get_llm',lambda:Mock(invoke=lambda _:Mock(text='answer')))
    assert base.generate('prompt','fallback')=='answer'
    assert 'user: hi' in base.conversation_context({'history':[dict(role='user',content='hi')]})

def test_qa_citations_and_memory(monkeypatch):
    docs=[Document(page_content='ETF information',metadata=dict(title='ETF',source_url='https://example.org',article_id='one'))]*2
    retriever=Mock(invoke=lambda _:docs)
    model=Mock(invoke=lambda _:Mock(text='An ETF is a fund [1].'))
    monkeypatch.setattr(rag,'get_retriever',lambda category:retriever)
    monkeypatch.setattr(rag,'get_llm',lambda:model)
    r=qa.finance_qa_agent(dict(question='Explain it',history=[dict(role='user',content='ETF')]))
    assert len(r['sources'])==1
    assert r['sources'][0]['number']==1
    assert '[1]' in r['answer']
    monkeypatch.setattr(rag,'get_retriever',lambda category:Mock(invoke=lambda _:[]))
    assert qa.finance_qa_agent({'question':'Unknown'})['sources']==[]

def test_tax(monkeypatch):
    import src.agents.tax_agent as tax
    monkeypatch.setattr(tax,'answer_with_rag',lambda *args, **kwargs:dict(answer='Tax education',sources=[]))
    assert 'tax year' in tax_agent({'question':'Tax?'})['answer']

def test_market(monkeypatch):
    monkeypatch.setattr(market,'get_market_chart',lambda *_:dict(latest_price=100,currency='USD',change_pct=2,price_date='2026-01-01',retrieved_at='now'))
    assert '100.00' in market.market_agent({'symbol':'AAPL'})['answer']
    monkeypatch.setattr(market,'get_market_chart',lambda *_:dict(error='Unavailable'))
    assert market.market_agent({'symbol':'AAPL'})['answer']=='Unavailable'

def test_market_extract(monkeypatch):
    import src.agents.market_entity_extractor as extractor
    import src.agents.market_symbol_resolver as resolver
    monkeypatch.setattr(extractor,'extract_market_entity',lambda _:Mock(company=None,symbol=None,period='1M'))
    monkeypatch.setattr(resolver,'resolve_symbol',lambda *_:None)
    assert 'ticker' in market.market_agent({'question':'Show stocks'})['answer']

def test_news(monkeypatch):
    assert 'ticker' in news.news_agent({})['answer']
    monkeypatch.setattr(news.yf,'Ticker',Mock(side_effect=RuntimeError))
    assert 'unavailable' in news.news_agent({'symbol':'A'})['answer']
    monkeypatch.setattr(news.yf,'Ticker',lambda _:Mock(news=[]))
    assert news.news_agent({'symbol':'A'})['sources']==[]
    monkeypatch.setattr(news.yf,'Ticker',lambda _:Mock(news=[{'content':{'title':'Headline','canonicalUrl':{'url':'https://example.org'},'pubDate':'today','provider':{'displayName':'Publisher'}}}]))
    monkeypatch.setattr(base,'get_llm',Mock(side_effect=RuntimeError))
    monkeypatch.setattr(news, "extract_market_entity", lambda *args, **kwargs: Mock(company=None, symbol=None))
    r=news.news_agent({'symbol':'A','question':'News?'})
    assert r['sources'][0]['title']=='Headline'
    assert '[1]' in r['answer']


def test_news_resolves_company_from_chat_without_market_selection(monkeypatch):
    extract = Mock(return_value=Mock(company="Apple", symbol=None))
    resolve = Mock(return_value="AAPL")
    summarize = Mock(return_value={"answer": "Apple headlines", "sources": []})
    monkeypatch.setattr(news, "extract_market_entity", extract)
    monkeypatch.setattr(news, "resolve_symbol", resolve)
    monkeypatch.setattr(news, "summarize_company_news", summarize)

    question = "What is APPLE doing with AI?"
    assert news.news_agent({"question": question})["answer"] == "Apple headlines"
    resolve.assert_called_once_with("Apple", None)
    summarize.assert_called_once_with("AAPL", question)


def test_market_handoff_shows_provider_headlines_without_requiring_causal_evidence(monkeypatch):
    ticker = Mock(return_value=Mock(news=[
        {"content": {
            "title": "Nvidia announces a new chip",
            "canonicalUrl": {"url": "https://example.org/nvidia"},
            "pubDate": "2026-11-13T12:00:00Z",
            "provider": {"displayName": "Example News"},
        }},
    ]))
    monkeypatch.setattr(news.yf, "Ticker", ticker)
    generate = Mock()
    monkeypatch.setattr(news, "generate", generate)
    result = news.news_agent({
        "symbol": "NVDA",
        "question": "Why did Nvidia move differently from the market?",
        "market_comparison": "NVDA fell 2% and SPY fell 0.4%.",
    })
    assert "Recent headlines for NVDA" in result["answer"]
    assert "[1] Nvidia announces a new chip" in result["answer"]
    assert "Example News, 2026-11-13" in result["answer"]
    assert result["sources"][0]["url"] == "https://example.org/nvidia"
    ticker.assert_called_once_with("NVDA")
    generate.assert_not_called()


def test_goal_agent_uses_chat_assumptions_without_saved_goal(monkeypatch):
    import src.agents.goal_agent as goals

    llm = Mock()
    llm.with_structured_output.return_value.invoke.return_value = goals.GoalInputs(
        target=1200, years=1, initial=0, monthly=80, annual_return_pct=0,
        risk_appetite="moderate",
    )
    monkeypatch.setattr(goals, "get_llm", lambda: llm)
    reply = goals.goal_agent({
        "question": "`1,200 target, a 1-year timeline, `0 in current savings, "
                    "$80 per month, and a 0% assumed annual return. Leave risk appetite at Moderate."
    })
    result = reply["goal_analysis"]
    assert result["projected_value"] == 960
    assert result["required_monthly"] == 100
    assert result["shortfall"] == 240
