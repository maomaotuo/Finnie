# Finnie technical design

## State and agent contracts

`FinanceState` is a typed partial dictionary. Every invocation supplies `question`; optional fields include `agent_override`, `portfolio`, `goal`, `symbol`, `period`, and `category`. Agent outputs update `answer`, `sources`, and their domain payload (`portfolio_analysis`, `goal_analysis`, or `market_data`). The router clears turn-specific outputs so citations and metrics from a prior turn cannot leak into a new answer.

`build_graph()` compiles START → router → selected specialist → remember → END with an in-memory LangGraph checkpointer. Market movement explanations and combined quote-and-news requests follow Market → News → combine results → remember. News reuses the ticker resolved by Market. For explanations, News uses the observed comparison and cited reporting to assess possible drivers and displays recent headlines for context. Invoke with `{"configurable": {"thread_id": "unique-session-id"}}`. A structured Gemini decision selects one of six specialists and indicates whether a market request needs headlines or a price-move explanation. Manual selection sets the first specialist. The supervisor still evaluates news intent for Market. If Gemini is unavailable, deterministic rules select the route and use the previous specialist for simple follow-ups. The UI allocates a graph per session; terminal users get one graph per process. This favors reliable local evaluation over durable multi-user infrastructure.

The memory node bounds state history to 20 user/assistant entries; prompts use at most eight recent entries and truncate each entry. The shared RAG pipeline expands ambiguous follow-up searches using the previous user question. Earlier assistant replies remain generation context and are excluded from search text. Portfolio and goals retain structured dashboard inputs. The Goal agent can use assumptions stated in the current question and fill in omitted fields from the saved goal. Market chat gives an explicitly named asset priority over the dashboard ticker.

## RAG

Local Markdown educational summaries plus eligible JSON articles are loaded, split into 500-character chunks with 100-character overlap, embedded using normalized `all-MiniLM-L6-v2` CPU embeddings, and stored in FAISS. JSON sources must appear as `candidate` in the manifest, contain at least 1,000 characters, and not be resource directories. Excluded or unreviewed sources are not silently promoted.

Finance Q&A and Tax Education are independent graph nodes. Both call `src.rag.pipeline.answer_with_rag` with their own instructions. The shared pipeline builds the search query, retrieves evidence, assigns citation numbers, and generates a grounded answer. Neither specialist invokes the other. Tax Education also owns its jurisdiction and tax-year guidance and appends its standard footer once.

`src.rag.retriever` loads one FAISS store per process. Its search views share that store and return up to five chunks by default. Finance Q&A searches across financial education. Tax Education searches IRS-hosted sources first, tax-category sources second, and the broader corpus third. Each fallback runs only if the previous search returns no chunks within the distance cutoff; metadata preference does not establish relevance or sufficiency. A user-selected category remains an exact constraint at every tier. Filtered search considers up to 100 nearest candidates before applying metadata constraints. Other specialists continue to use their calculators and market or news services.

Citations are deduplicated by article ID, then URL, then title. Chat shows the smallest FAISS distance among the retrieved chunks for each source. Lower distances indicate closer matches to the query. Both RAG specialists answer supported parts and identify missing evidence. Tax distinguishes stable concepts from year-specific rules and limits IRS-based answers to U.S. federal tax. Retrieval discards chunks with a FAISS distance above `retrieval_max_distance` (default `0.90`, configurable in `config.yaml` or through `RETRIEVAL_MAX_DISTANCE`). If no passage passes the cutoff, the pipeline asks the user to rephrase without calling Gemini to generate an answer. The default was spot-checked against the current index and embedding model. A broader evaluation would be needed to calibrate it across topics. Pickle-based FAISS metadata must remain a trusted local artifact.

## Calculations

`analyze_portfolio(holdings)` accepts dictionaries with `symbol`, `quantity`, `price`, `asset_type`, and optional `expense_ratio_pct`. It validates finite positive positions, groups repeated tickers, calculates value and allocation, asset-type allocation, Herfindahl concentration (100 × sum of squared weights), effective holding count (inverse sum of squared weights), and value-weighted fees when all fund expense ratios are known. It does not estimate ETF constituents or expected returns. Percentages are calculated before rounding.

`project_goal(target, years, initial=0, monthly=0, annual_return_pct=5, risk_appetite="moderate")` converts effective annual return to a monthly rate, uses end-of-month contributions, returns a monthly trajectory, projected value, required contribution, and shortfall. Zero return uses the exact linear case. Negative assumed returns are supported within bounded inputs. Years round to the nearest month. Risk appetite is recorded without implying guaranteed returns.

## External services and failures

Gemini clients and the FAISS retriever initialize lazily. LLM retries are bounded and request timeout is 45 seconds. Generation failure returns deterministic explanations where possible. Workflow wrappers turn service failures into safe user messages and log exception type rather than credentials or raw prompts.

Market data uses the existing adjusted yfinance price-history adapter behind a shared, thread-locked, bounded 128-entry cache. Default TTL is 30 minutes. Requests retry up to three times with exponential backoff. Expired data is shown only with an explicit stale warning when refresh fails. Prices are never fabricated. Intraday change uses the prior trading day's adjusted close; longer periods compare first and last available closes. News only summarizes real returned headlines with links and publication timestamps; failures do not generate substitute news.

## Configuration and performance

`config.yaml` supplies defaults; environment variables override corresponding upper-case keys. `.env` loads without overwriting process variables. Paths resolve relative to the project rather than the launch directory. Embeddings and retrievers are cached; FAISS indexing is a separate offline command. No production latency or load benchmarks are claimed. The browser session stores financial inputs in memory; use sample portfolios during demonstrations.

## MCP integration

The local stdio server exposes the existing portfolio calculator, savings projection, and market quote service as typed MCP tools. MCP clients discover each tool and its input schema, then receive structured results. The server operates independently of Streamlit and LangGraph. Calculator calls run locally, while market quotes use Yahoo Finance.

## Extension points

Durable checkpointing and authentication would be needed for hosted accounts. A calibrated retrieval evaluation set, financial expert review, scheduled corpus refresh, exact dependency locking, provider monitoring, and load tests would be needed for production readiness.
