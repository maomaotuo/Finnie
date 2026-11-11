import json

from streamlit.testing.v1 import AppTest

import src.agents.market_data as market_data
import src.agents.market_symbol_resolver as resolver
import src.agents.news_agent as news

def test_ui_portfolio_goals_and_chat(monkeypatch):
    quotes_requested = []

    def quote(symbol, period, *, refresh=False):
        if not refresh:
            return {"error": "Offline test"}
        quotes_requested.append(symbol)
        return {
            "latest_price": 100.0, "currency": "USD", "price_date": "2026-11-06",
            "stale": symbol == "VOO",
        }

    monkeypatch.setattr(market_data, "get_market_chart", quote)
    app=AppTest.from_file('../src/web_app/app.py',default_timeout=30).run()
    assert not app.exception
    assert len(app.tabs)==4
    next(b for b in app.button if b.label=='Load illustrative sample portfolio').click().run()
    assert not app.exception
    assert any(m.value=='$8,500.00' for m in app.metric)
    next(b for b in app.button if b.label == "Analyze holdings").click().run()
    assert not app.exception
    assert sorted(quotes_requested) == ["AAPL", "MSFT", "VOO"]
    assert any(m.label == "Portfolio value" and m.value == "$2,300.00" for m in app.metric)
    assert any("cache" in warning.value for warning in app.tabs[1].warning)
    assert all(holding["price"] == 100.0 for holding in app.session_state.holdings)
    next(b for b in app.button if b.label=='Calculate projection').click().run()
    assert not app.exception
    assert any(m.label=='Required monthly contribution' for m in app.metric)
    app.selectbox(key='specialist').select('goal').run()
    app.chat_input[0].set_value('Am I on track?').run()
    assert not app.exception
    assert len(app.chat_message)==2
    assert app.selectbox(key='specialist').value == 'auto'



def test_market_overview_switches_to_requested_symbol(monkeypatch):
    def quote(symbol, period):
        return {
            "symbol": symbol, "period": period, "latest_price": 100, "currency": "USD",
            "change_pct": 1.2, "price_date": "2026-11-06", "retrieved_at": "2026-11-07",
            "prices": [{"date": "2026-11-06", "close": 100}],
        }

    monkeypatch.setattr(market_data, "get_market_chart", quote)
    monkeypatch.setattr(resolver, "resolve_symbol", lambda name: {"Costco": "COST", "Apple": "AAPL"}[name])

    news_requests = []

    class Ticker:
        def __init__(self, symbol):
            news_requests.append(symbol)
            company = {"COST": "Costco", "AAPL": "Apple"}[symbol]
            self.news = [{
                "title": f"Sample {company} headline",
                "link": f"https://example.com/{company.lower()}",
            }]

    monkeypatch.setattr(news.yf, "Ticker", Ticker)
    monkeypatch.setattr(news, "generate", lambda prompt, fallback: fallback)
    from streamlit import cache_data
    cache_data.clear()
    app = AppTest.from_file("../src/web_app/app.py", default_timeout=30).run()
    assert not app.exception
    overview = app.tabs[2].dataframe[0].value
    assert len(overview) == 10
    assert overview["Symbol"].nunique() == 10
    assert (overview["Latest price"] == "100.00 USD").all()

    next(field for field in app.text_input if field.label == "Company name or ticker").set_value("Costco")
    next(button for button in app.button if button.label == "Look up market data").click().run()
    assert not app.exception
    assert not app.tabs[2].dataframe
    assert app.tabs[2].metric[0].label == "COST · latest available price"
    assert app.tabs[2].metric[1].label == "1D change"
    assert all(field.label != "History period" for field in app.selectbox)
    chart = app.tabs[2].get("plotly_chart")[0]
    buttons = json.loads(chart.proto.spec)["layout"]["updatemenus"][0]["buttons"]
    assert [button["label"] for button in buttons] == ["1D", "1W", "1M", "3M", "6M", "1Y", "5Y"]
    assert any("Sample Costco headline" in item.value for item in app.tabs[2].markdown)
    assert app.tabs[2].get("link_button")[0].proto.url == "https://example.com/costco"
    app.run()
    assert news_requests == ["COST"]

    next(field for field in app.text_input if field.label == "Company name or ticker").set_value("Apple")
    next(button for button in app.button if button.label == "Look up market data").click().run()
    assert app.tabs[2].metric[0].label == "AAPL · latest available price"
    assert [button.proto.url for button in app.tabs[2].get("link_button")] == ["https://example.com/apple"]
    assert news_requests == ["COST", "AAPL"]
    cache_data.clear()
