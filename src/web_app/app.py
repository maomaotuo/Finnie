"""Finnie capstone interface. Run: python -m streamlit run src/web_app/app.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import json
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pandas as pd
import plotly.express as px
import streamlit as st
from src.core.config import ROOT, option
from src.core.transcription import transcribe_question
from src.workflow.graph import build_graph, guarded
from src.agents.market_symbol_resolver import resolve_symbol
from src.agents.market_data import get_market_chart
from src.agents.news_agent import summarize_company_news
from src.utils.calculators import analyze_portfolio, number, project_goal
from src.agents.base_agent import DISCLAIMER

DEFAULT_MARKET_SYMBOLS = (
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "COST", "SPY", "VOO",
)
MARKET_PRICED_ASSETS = {"stock", "etf", "mutual_fund"}


def price_portfolio(holdings):
    """Fetch one quote per ticker and prepare a USD valuation."""
    periods = {}
    for holding in holdings:
        symbol = str(holding["symbol"] or "").strip().upper()
        if not symbol:
            raise ValueError("Each holding needs a ticker or label.")
        holding["symbol"] = symbol
        if number(holding["quantity"], f"{symbol} quantity") == 0:
            raise ValueError(f"{symbol} quantity must be positive.")
        if holding["asset_type"] in MARKET_PRICED_ASSETS:
            # Mutual funds generally publish a daily price after market close.
            periods[symbol] = "1W" if holding["asset_type"] == "mutual_fund" else "1D"

    symbols = sorted(periods)
    with ThreadPoolExecutor(max_workers=5) as pool:
        quotes = dict(zip(symbols, pool.map(
            lambda symbol: get_market_chart(symbol, periods[symbol], refresh=True), symbols
        )))

    for holding in holdings:
        quote = quotes.get(holding["symbol"]) if holding["asset_type"] in MARKET_PRICED_ASSETS else None
        if quote is None:
            if holding["asset_type"] == "cash":
                holding["price"] = 1.0
            continue
        symbol = holding["symbol"]
        if "error" in quote:
            raise ValueError(f"Couldn't fetch a price for {symbol}. Check the ticker and try again.")
        if quote["currency"] != "USD":
            raise ValueError(f"{symbol} is quoted in {quote['currency']}. This portfolio is valued in USD.")
        holding["price"] = quote["latest_price"]

    return holdings, [
        {
            "Ticker": symbol,
            "Price (USD)": quote["latest_price"],
            "Price timestamp": quote["price_date"],
            "Source": "Cached Yahoo Finance quote" if quote.get("stale") else "Yahoo Finance",
        }
        for symbol, quote in quotes.items()
    ]


@st.cache_data(ttl=300, show_spinner=False)
def default_market_quotes():
    """Fetch the watchlist concurrently and cache the overview across reruns."""
    with ThreadPoolExecutor(max_workers=5) as pool:
        return list(pool.map(get_market_chart, DEFAULT_MARKET_SYMBOLS, ("1D",) * len(DEFAULT_MARKET_SYMBOLS)))


def market_history_figure(quote, history):
    """Build chart buttons from intraday bars and slices of daily history."""
    ranges = {}
    if quote["period"] == "1D":
        ranges["1D"] = pd.DataFrame(quote["prices"])
    if history:
        daily = pd.DataFrame(history["prices"])
        dates = pd.to_datetime(daily["date"])
        latest = dates.max()
        for label, offset in (
            ("1W", pd.DateOffset(weeks=1)),
            ("1M", pd.DateOffset(months=1)),
            ("3M", pd.DateOffset(months=3)),
            ("6M", pd.DateOffset(months=6)),
            ("1Y", pd.DateOffset(years=1)),
        ):
            ranges[label] = daily.loc[dates >= latest - offset]
        ranges["5Y"] = daily
    if not ranges:
        ranges[quote["period"]] = pd.DataFrame(quote["prices"])

    symbol = quote["symbol"]
    initial_period = next(iter(ranges))
    currency = quote["currency"]
    figure = px.line(ranges[initial_period], x="date", y="close",
                     markers=len(ranges[initial_period]) == 1)
    figure.update_traces(
        line={"color": "#2563eb", "width": 2.5},
        marker={"color": "#2563eb", "size": 7},
        hovertemplate=f"%{{y:,.2f}} {currency}<extra></extra>",
    )
    figure.update_layout(
        template="plotly_white",
        title={"text": f"{symbol} · {initial_period} price history", "x": 0.025,
               "font": {"size": 21, "color": "#0f172a"}},
        height=430,
        margin={"l": 68, "r": 24, "t": 108, "b": 45},
        font={"color": "#475569"},
        paper_bgcolor="#ffffff",
        plot_bgcolor="#f8fafc",
        hovermode="x unified",
        hoverlabel={"bgcolor": "#ffffff", "font_color": "#0f172a"},
        xaxis={"title": None, "showgrid": False, "type": "date"},
        yaxis={"title": f"Price ({currency})", "gridcolor": "#e2e8f0",
               "tickformat": ",.2f", "zeroline": False},
        updatemenus=[{
            "type": "buttons", "direction": "right", "active": 0,
            "x": 0, "y": 1.16, "xanchor": "left", "yanchor": "top",
            "bgcolor": "#f1f5f9", "bordercolor": "#cbd5e1", "borderwidth": 1,
            "font": {"color": "#1e293b", "size": 11},
            "buttons": [
                {
                    "label": period,
                    "method": "update",
                    "args": [
                        {"x": [frame["date"].tolist()], "y": [frame["close"].tolist()],
                         "mode": "lines+markers" if len(frame) == 1 else "lines"},
                        {"title.text": f"{symbol} · {period} price history",
                         "xaxis.autorange": True, "yaxis.autorange": True},
                    ],
                }
                for period, frame in ranges.items()
            ],
        }],
    )
    return figure


st.set_page_config(page_title="Finnie · Financial education", page_icon="📈", layout="wide")
st.title("📈 Finnie")
st.markdown("Explore investments, understand your portfolio, and plan your savings.")
st.caption(DISCLAIMER)
# Streamlit reruns this file on interaction. Session state preserves the graph and saved inputs.
if "graph" not in st.session_state:
    st.session_state.graph=build_graph()
    st.session_state.thread_id=str(uuid4())
    st.session_state.messages=[]
    st.session_state.holdings=[]
    st.session_state.goal={}
    st.session_state.symbol=""

def clear_voice_draft():
    st.session_state.pop("voice_transcript", None)
    # A new widget key clears the previous recording on the next rerun.
    st.session_state.voice_recording_version = st.session_state.get("voice_recording_version", 0) + 1


# Reset the specialist before rendering its widget.
if st.session_state.pop("reset_specialist", False):
    st.session_state.specialist = "auto"

with st.sidebar:
    st.header("Chat settings")
    st.caption("Choose who answers your next question. Finnie returns to Automatic after that.")
    specialist_labels = {
        "auto": "Automatic",
        "finance_qa": "Finance Q&A",
        "portfolio": "Portfolio Analysis",
        "market": "Market Analysis",
        "goal": "Goal Planning",
        "news": "News",
        "tax": "Tax Education",
    }
    agent = st.selectbox(
        "Who should answer?",
        list(specialist_labels),
        format_func=specialist_labels.__getitem__,
        key="specialist",
        help="Automatic lets Finnie choose a specialist for each question.",
    )
    with st.expander("Advanced search settings"):
        category = st.text_input(
            "Knowledge category filter (optional)",
            help="Limits Finance Q&A and Tax to an exact knowledge-base category. Leave blank for the default search.",
        )
    # Reset the conversation checkpoint and visible messages while keeping dashboard inputs.
    if st.button("Clear conversation", help="Clears chat history. Your portfolio, goals, and market selection stay available."):
        st.session_state.graph=build_graph()
        st.session_state.thread_id=str(uuid4())
        st.session_state.messages=[]
        clear_voice_draft()
        st.rerun()

chat, portfolio, market, goals = st.tabs(["💬 Chat", "🥧 Portfolio", "📊 Market", "🎯 Goals"])
with portfolio:
    st.subheader("Explore your holdings")
    st.caption("Enter tickers and quantities. Analyze holdings fetches prices for stocks, ETFs, and mutual funds. Enter cash as a USD amount in Quantity.")
    if st.button("Load illustrative sample portfolio"):
        st.session_state.holdings=json.loads((ROOT/"src/data/sample_portfolios/sample_portfolio.json").read_text())["holdings"]
        st.session_state.portfolio_inputs = st.session_state.holdings
        st.session_state.portfolio_quotes = []
        st.session_state.portfolio_sample = True
        st.session_state.pop("holdings_editor", None)
    inputs = st.session_state.setdefault("portfolio_inputs", st.session_state.holdings)
    frame=pd.DataFrame(inputs, columns=["symbol","quantity","price","asset_type","expense_ratio_pct"])
    frame["price"] = pd.to_numeric(frame["price"], errors="coerce").where(
        ~frame["asset_type"].isin(MARKET_PRICED_ASSETS | {"cash"})
    )
    edited=st.data_editor(frame, num_rows="dynamic", key="holdings_editor", hide_index=True,
        column_config={"asset_type":st.column_config.SelectboxColumn("Asset type", options=["stock","etf","bond","cash","mutual_fund","other"]),
                       "quantity":st.column_config.NumberColumn(min_value=0.0),
                       "price":st.column_config.NumberColumn("Manual USD price (bonds and other)", min_value=0.0, format="$%.2f"),
                       "expense_ratio_pct":st.column_config.NumberColumn("Expense ratio (%)", min_value=0.0,max_value=100.0, help="Enter 0.03 for 0.03%.")})
    if st.button("Analyze holdings", type="primary"):
        try:
            holdings = edited.astype(object).where(pd.notna(edited), None).to_dict("records")
            with st.spinner("Retrieving portfolio prices…"):
                holdings, quotes = price_portfolio(holdings)
            analyze_portfolio(holdings)
            st.session_state.holdings = holdings
            st.session_state.portfolio_quotes = quotes
            st.session_state.portfolio_sample = False
        except ValueError as exc:
            st.error(str(exc))
    if st.session_state.holdings:
        result=analyze_portfolio(st.session_state.holdings)
        sample = st.session_state.get("portfolio_sample", False)
        st.caption("Illustrative sample prices. Select Analyze holdings to fetch quotes." if sample else "Latest successful analysis. Select Analyze holdings again to refresh quotes.")
        a,b,c=st.columns(3)
        a.metric("Portfolio value", f"${result['total_value']:,.2f}", border=True)
        b.metric("Largest position",f"{result['largest_position']['allocation_pct']}%", border=True)
        c.metric("Weighted expense ratio", "Unknown" if result['weighted_expense_ratio_pct'] is None else f"{result['weighted_expense_ratio_pct']}%", border=True)
        st.plotly_chart(px.pie(pd.DataFrame(result["positions"]), names="symbol", values="value", title="Holding allocation", hole=0.48), width="stretch")
        allocation=pd.DataFrame(list(result["asset_allocation_pct"].items()),columns=["Asset type","Allocation (%)"])
        st.plotly_chart(px.bar(allocation,x="Asset type",y="Allocation (%)",title="Allocation by asset type"),width="stretch")
        st.dataframe(pd.DataFrame(result["positions"]),hide_index=True)
        quotes = st.session_state.get("portfolio_quotes", [])
        if quotes:
            if any(quote["Source"] == "Cached Yahoo Finance quote" for quote in quotes):
                st.warning("Some quotes came from the cache after a market data request failed. Check their timestamps.")
            st.caption("Prices may be delayed. When the market is closed, the last available price is used.")
            st.dataframe(pd.DataFrame(quotes), hide_index=True)
        st.caption(f"Concentration score: {result['concentration_score']}/100 (sum of squared holding weights; higher means more concentrated). Effective holdings: {result['effective_holdings']}. These metrics do not inspect underlying ETF holdings or measure overall investment risk.")
def select_watchlist_symbol():
    rows = st.session_state.market_watchlist.selection.rows
    if rows:
        st.session_state.market_watchlist_symbol = DEFAULT_MARKET_SYMBOLS[rows[0]]


def show_market_overview():
    for key in ("chart", "market_history", "market_news"):
        st.session_state.pop(key, None)


with market:
    st.subheader("Market explorer")
    st.caption("Browse the watchlist or search a company to explore its price history.")
    with st.form("market_lookup"):
        search_column, submit_column = st.columns([4, 1], vertical_alignment="bottom")
        with search_column:
            ticker = st.text_input("Company name or ticker", value=st.session_state.symbol,
                                   placeholder="Costco or COST",
                                   help="Company names can include common typos. Check the ticker shown in the result.")
        with submit_column:
            lookup = st.form_submit_button("Look up market data", type="primary", width="stretch")
    # Resolve the name first so the quote provider receives a ticker such as COST.
    selected_symbol = st.session_state.pop("market_watchlist_symbol", None)
    if lookup or selected_symbol:
        with st.spinner("Retrieving market data…"):
            symbol = selected_symbol or resolve_symbol(ticker.strip().lstrip("$"))
            history = None
            if symbol:
                # Intraday bars supply 1D. One daily history request supplies all longer ranges.
                with ThreadPoolExecutor(max_workers=2) as pool:
                    intraday_job = pool.submit(get_market_chart, symbol, "1D")
                    history_job = pool.submit(get_market_chart, symbol, "5Y")
                    data = intraday_job.result()
                    daily = history_job.result()
                if "error" not in daily:
                    history = daily
                    if "error" in data:
                        data = daily
            else:
                data = {"error": "Couldn't resolve that company name or ticker. Check the spelling and try again."}
        st.session_state.pop("market_news", None)
        if "error" in data:
            st.session_state.pop("chart", None)
            st.session_state.pop("market_history", None)
            st.error(data["error"])
        else:
            st.session_state.symbol=data["symbol"]
            st.session_state.period=data["period"]
            st.session_state.chart=data
            st.session_state.market_history=history
    if st.session_state.get("chart"):
        st.button("Back to market overview", on_click=show_market_overview)
        data=st.session_state.chart
        if data.get("stale"): st.warning(data["warning"])
        a,b=st.columns(2)
        a.metric(f"{data['symbol']} · latest available price",f"{data['latest_price']:,.2f} {data['currency']}", border=True)
        change = data["change_pct"]
        b.metric(f"{data['period']} change", "Unavailable" if change is None else f"{change:+.2f}%",
                 border=True)
        history = st.session_state.get("market_history")
        if history and history is not data and history.get("stale"):
            st.warning("Longer ranges use previously retrieved history.")
        st.plotly_chart(market_history_figure(data, history), width="stretch",
                        theme=None, config={"displaylogo": False})
        st.caption(f"Price timestamp: {data['price_date']} · Retrieved: {data['retrieved_at']} · Yahoo Finance via yfinance. Historical prices are adjusted. Quotes may be delayed. Cache duration: 30 minutes.")
        symbol = data["symbol"]
        st.markdown(f"#### Recent news for {symbol}")
        st.caption("Summary from Finnie’s News Agent with links to the original headlines.")
        # Save the result so unrelated Streamlit reruns do not repeat the news request.
        if "market_news" not in st.session_state:
            with st.spinner(f"Reading recent {symbol} headlines…"):
                st.session_state.market_news = guarded(
                    lambda _: summarize_company_news(symbol, f"Summarize the recent news for {symbol}.")
                )({})
        news = st.session_state.get("market_news")
        if news:
            st.markdown(news["answer"])
            for article in news.get("sources", []):
                st.link_button(f"[{article['number']}] {article['title']}", article["url"])
                st.caption(f"{article['publisher']} · {article['published_at']}")
    else:
        st.markdown("#### Market overview")
        st.caption("Select a row to open its chart and recent news, or search for another company.")
        with st.spinner("Loading default quotes…"):
            quotes = default_market_quotes()
        rows = []
        for symbol, quote in zip(DEFAULT_MARKET_SYMBOLS, quotes):
            available = "error" not in quote
            change = quote.get("change_pct")
            rows.append({
                "Symbol": symbol,
                "Latest price": f"{quote['latest_price']:,.2f} {quote['currency']}" if available else "Unavailable",
                "Session change": f"{change:+.2f}%" if change is not None else "—",
                "Price timestamp": quote.get("price_date", "—"),
                "Status": "Cached fallback" if quote.get("stale") else ("Available" if available else "Unavailable"),
            })
        st.dataframe(
            rows, hide_index=True, width="stretch", key="market_watchlist",
            on_select=select_watchlist_symbol, selection_mode="single-row",
        )
        st.caption("Yahoo Finance · Latest available trading session. Prices may be delayed. "
                   "On weekends and market holidays, timestamps reflect the last available session.")
with goals:
    st.subheader("Plan a savings goal")
    st.caption("See how your starting balance and monthly contributions could grow toward a target.")
    with st.form("goal_planner"):
        target=st.number_input("Target amount ($)",min_value=1.0,value=50000.0,step=1000.0)
        years=st.number_input("Timeline (years)",min_value=1.0/12,max_value=100.0,value=10.0,step=0.5)
        initial=st.number_input("Current savings ($)",min_value=0.0,value=5000.0,step=100.0)
        monthly=st.number_input("Monthly contribution ($)",min_value=0.0,value=250.0,step=25.0)
        risk=st.selectbox("Risk appetite",["conservative","moderate","aggressive"],index=1)
        rate=st.number_input("Assumed annual return (%)",min_value=-50.0,max_value=50.0,value=5.0,step=0.25)
        plan=st.form_submit_button("Calculate projection", type="primary")
    # Keep the submitted assumptions available for the chart and later chat questions.
    if plan:
        st.session_state.goal=dict(target=target,years=years,initial=initial,monthly=monthly,annual_return_pct=rate,risk_appetite=risk)
    if st.session_state.goal:
        result=project_goal(**st.session_state.goal)
        a,b,c=st.columns(3)
        a.metric("Projected balance",f"${result['projected_value']:,.2f}", border=True)
        monthly_extra = round(result["monthly"] - result["required_monthly"], 2)
        surplus = round(result["projected_value"] - result["target"], 2)
        b.metric(
            "Required monthly contribution",
            f"${result['required_monthly']:,.2f}",
            delta=f"${monthly_extra:,.2f} extra per month" if monthly_extra > 0 else None,
            border=True,
        )
        if surplus > 0:
            c.metric("Projected surplus", f"${surplus:,.2f}", border=True)
        else:
            c.metric("Projected shortfall", f"${result['shortfall']:,.2f}", border=True)
        projection = pd.DataFrame(result["trajectory"]).rename(columns={
            "month": "Month", "balance": "Projected balance", "contributions": "Total contributions",
        })
        chart = px.line(
            projection, x="Month", y=["Projected balance", "Total contributions"],
            labels={"value": "Amount ($)", "variable": "Series"}, title="Savings over time",
        )
        chart.add_hline(y=result["target"], line_dash="dash", line_color="#64748b",
                        annotation_text=f"Goal · ${result['target']:,.0f}")
        st.plotly_chart(chart, width="stretch")
        st.caption("Constant assumed return with contributions at month end. Excludes taxes, fees, inflation, and volatility. Returns are not guaranteed. Risk appetite does not determine a guaranteed return.")
with chat:
    st.subheader("Learn with Finnie")
    st.caption("Ask about money, your portfolio, a company, or a savings goal.")
    starter = None
    if not st.session_state.messages:
        st.markdown("**Try a question**")
        for example in (
            "What is an ETF?",
            "How does compound interest work?",
            "What is a long-term capital gain?",
        ):
            if st.button(example, key=f"chat_starter_{example}"):
                starter = example
    # Recreate the chat display from saved messages after each Streamlit rerun.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("market_news_workflow"):
                st.caption("Specialists: Market → News")
            elif message.get("agent"):
                st.caption("Specialist: " + specialist_labels.get(message["agent"], message["agent"]))
            sources = message.get("sources", [])
            if sources:
                with st.expander(f"Sources ({len(sources)})"):
                    for source in sources:
                        label = f"[{source.get('number', '')}] {source['title']}"
                        url = source.get("url", "")
                        if url.startswith(("https://", "http://")):
                            st.link_button(label, url)
                        else:
                            st.markdown(label)
                        distance = source.get("faiss_distance")
                        if distance is not None:
                            st.caption(f"Match distance {distance:.3f} · lower is closer")
    voice_question = None
    with st.expander("Ask by voice"):
        if option("openai_api_key", "").strip():
            st.caption("Record your question, then select Transcribe to send the recording to OpenAI.")
            version = st.session_state.get("voice_recording_version", 0)
            recording = st.audio_input("Record your question", key=f"voice_recording_{version}")
            if st.button("Transcribe", disabled=recording is None):
                st.session_state.pop("voice_transcript", None)
                try:
                    with st.spinner("Transcribing your recording…"):
                        st.session_state.voice_transcript = transcribe_question(recording.getvalue())
                except ValueError as exc:
                    st.error(str(exc))
            if "voice_transcript" in st.session_state:
                draft = st.text_area("Review your question", key="voice_transcript")
                if st.button("Send voice question", disabled=not draft.strip()):
                    voice_question = draft.strip()
                    clear_voice_draft()
        else:
            st.caption("Set OPENAI_API_KEY in the app configuration to enable transcription.")
    question = st.chat_input("Ask Finnie a question…") or starter or voice_question
    if question:
        # Give the selected specialist the current dashboard inputs alongside the question.
        payload={"question":question,"agent_override":agent,"portfolio":st.session_state.holdings,
                 "goal":st.session_state.goal,"symbol":st.session_state.symbol,
                 "period":st.session_state.get("period","1M"),"category":category.strip()}
        with st.spinner("Finnie is working…"):
            result=st.session_state.graph.invoke(payload,{"configurable":{"thread_id":st.session_state.thread_id}})
        if agent != "auto" and not result.get("is_greeting"):
            st.session_state.reset_specialist = True
        # Save display messages before rerunning so the reply appears in the chat history.
        st.session_state.messages.extend([{"role":"user","content":question},
            {"role":"assistant","content":result["answer"],"agent":None if result.get("is_greeting") else result["selected_agent"],"sources":result.get("sources",[]),"market_news_workflow":bool(result.get("market_comparison"))}])
        st.rerun()
