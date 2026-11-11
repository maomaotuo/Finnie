from unittest.mock import Mock
import pandas as pd
import pytest
import src.agents.market_data as market

def history():
    return pd.DataFrame({'Close':[100.,110.],'Volume':[1000.,2000.]},index=pd.to_datetime(['2026-01-01','2026-01-02'],utc=True))

def test_fetch_chart(monkeypatch):
    monkeypatch.setattr(market.yf,'Ticker',lambda _:Mock(history=lambda **_:history(),fast_info={'currency':'USD'}))
    r=market._fetch_market_chart('AAPL')
    assert r['latest_price']==110
    assert r['change_pct']==10
    r=market._fetch_market_chart('AAPL','1D')
    assert r['previous_close']==100
    assert len(r['prices'])==1

def test_fetch_errors(monkeypatch):
    assert 'error' in market._fetch_market_chart('')
    assert 'error' in market._fetch_market_chart('A','invalid')
    monkeypatch.setattr(market.yf,'Ticker',Mock(side_effect=RuntimeError))
    assert 'error' in market._fetch_market_chart('A')
    monkeypatch.setattr(market.yf,'Ticker',lambda _:Mock(history=lambda **_:pd.DataFrame()))
    assert 'error' in market._fetch_market_chart('A')

def test_cache_and_stale_fallback(monkeypatch):
    market._cache.clear()
    fetch=Mock(return_value={'symbol':'A','prices':[]})
    monkeypatch.setattr(market,'_fetch_with_retry',fetch)
    assert not market.get_market_chart('a')['cached']
    assert market.get_market_chart('A')['cached']
    fetch.assert_called_once()
    monkeypatch.setattr(market,'option',lambda *_:0)
    fetch.side_effect=market.MarketUnavailable
    assert market.get_market_chart('A')['stale']
    assert 'error' in market.get_market_chart('B')
    assert 'error' in market.get_market_chart('bad symbol')
    assert 'error' in market.get_market_chart('A','invalid')
