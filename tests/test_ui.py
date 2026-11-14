import json
from base64 import b64encode
from types import SimpleNamespace

import requests
from streamlit.testing.v1 import AppTest

import src.agents.market_data as market_data
import src.agents.market_symbol_resolver as resolver
import src.agents.news_agent as news
import src.web_app.chat_composer as voice


def test_voice_question_is_reviewed_before_chat_submission(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_TRANSCRIPTION_MODEL", "whisper-1")
    monkeypatch.setattr(market_data, "get_market_chart", lambda *args: {"error": "Offline test"})
    requests_made = []

    def mock_post(url, **kwargs):
        requests_made.append(kwargs)
        response = requests.Response()
        response.status_code = 200
        response._content = b'{"text":"Good morning"}'
        return response

    monkeypatch.setattr(requests, "post", mock_post)
    event = {"recording": None, "question": None}
    rendered = []

    def mock_composer(**kwargs):
        import streamlit as st

        if event["recording"] is not None:
            st.session_state[kwargs["key"]] = SimpleNamespace(recording=event["recording"])
            kwargs["on_recording_change"]()
            event["recording"] = None
        rendered.append(kwargs["data"]["result"])
        question, event["question"] = event["question"], None
        return SimpleNamespace(question=question)

    monkeypatch.setattr(voice, "composer", mock_composer)
    app = AppTest.from_file("../src/web_app/app.py", default_timeout=30).run()
    assert not app.exception
    assert not requests_made

    event["recording"] = {
        "audio": b64encode(b"test WebM").decode(),
        "mime": "audio/webm;codecs=opus",
    }
    app.run()
    assert not app.exception
    assert not app.chat_message
    assert app.session_state.chat_transcription["text"] == "Good morning"
    assert len(requests_made) == 1
    assert requests_made[0]["data"]["model"] == "whisper-1"
    assert requests_made[0]["files"]["file"] == ("question.webm", b"test WebM", "audio/webm")

    app.run()
    assert rendered[-1]["text"] == "Good morning"
    event["question"] = "Hi"
    app.run()
    assert not app.exception
    assert app.session_state.messages[0]["content"] == "Hi"
    assert len(app.chat_message) == 2
    assert len(requests_made) == 1
    assert rendered[-1] is None


def test_ui_portfolio_goals_and_chat(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
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
    price_table = app.tabs[1].dataframe[1].value.set_index("Ticker")
    assert price_table.loc["AAPL", "Unit price (USD)"] == 100.0
    assert price_table.loc["AAPL", "Holding value (USD)"] == 1000.0
    assert price_table.loc["VOO", "Source"] == "Cached Yahoo Finance quote"
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
