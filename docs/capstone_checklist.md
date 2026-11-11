# Capstone requirements mapping

| Requirement | Implementation / evidence |
| --- | --- |
| Six specialized agents | `src/agents/*_agent.py`, all wired in `src/workflow/graph.py` |
| LangGraph routing and state | Structured supervisor, fallback rules, typed state, per-session checkpoint |
| Multi-turn conversations | Bounded history, follow-up retrieval context; workflow isolation test |
| RAG and source attribution | FAISS, local embeddings, eligible article filtering, per-article citations |
| 50–100 educational articles | Loader test verifies eligible article count; excluded manifest entries stay excluded |
| Category filtering | Shared FAISS index, specialist source preferences, and optional exact category constraint |
| Portfolio analysis | Value, allocations, fees, holding concentration, validated inputs |
| Goal planning | Monthly projection, required contributions, risk-appetite input, assumption labels |
| Market data | yfinance history, cache, retries, stale fallback, retrieval and price timestamps |
| News and tax | Real provider headlines with citations; independent Tax Agent with IRS-first retrieval and tax-specific instructions |
| Four-tab interface | Chat / Portfolio / Market / Goals, Plotly visualizations |
| Tests | Agents, router, workflow memory, arithmetic, market failure handling, ingestion, UI interactions |
| Documentation | README, technical design, demo script, `.env.example` |
| Demo video | Must be recorded by the project owner; see demo script |
| MCP server | Local stdio server with portfolio, savings, and market tools. See the README for client configuration and the protocol test. |
| Docker / cloud | Optional extensions outside the local submission. |

The project brief inconsistently describes tests and the two advanced agents as required versus optional. This implementation includes both advanced agents and automated tests. Live API verification and a recorded demo remain separate from offline automated tests. Expert review of educational sources and model answers is not implied by a passing test suite.
