# Finnie verification

## Submission check

The full suite passed with **81 tests** and **91% coverage** across the runtime modules measured by the [README coverage command](../README.md#tests). The measured scope includes agents, orchestration, core services, calculators, and RAG retrieval and generation. Streamlit UI tests run in the suite alongside the backend tests.

The suite covers portfolio quote refresh, broad U.S. market updates, quote and news requests in one turn, sourced explanations of market moves, and voice transcript review before submission. External providers are mocked in these tests. Rehearse the [demo prompts](demo_script.md) to confirm the deployed app can reach the providers when you record.

## Earlier automated checks (November 6, 2026)

52 tests passed. Runtime backend coverage: 89.72%. Coverage includes agents, workflow, core configuration/model helpers, calculations, and the retriever; it excludes the UI, index-building and source-curation scripts. Streamlit UI flows are exercised separately by AppTest in the same suite. The 80% coverage gate passed. Python compilation passed.

Verified behaviors include portfolio arithmetic and invalid inputs, repeated-ticker aggregation, missing fees, zero and negative return projections, all routing categories, manual route overrides, isolated sessions, bounded history, stale-source reset, citation deduplication, curated article loading, category filters, market caching and stale fallbacks, and UI portfolio/goal/chat interactions.

## Live integration spot checks

Using the existing local configuration, Gemini responded successfully and Yahoo Finance returned AAPL historical prices. A real automatic-route ETF question returned two article sources; a follow-up comparing it with a mutual fund returned three sources and preserved four history entries. The news agent returned five linked articles. See `live_verification.json` for metadata.

The first grounded answer took approximately 43 seconds including embedding initialization; the follow-up took approximately 35 seconds. These are single-run observations, not a controlled performance benchmark. Live model latency remains a demo consideration. The spot checks establish connectivity and response flow; they do not constitute expert financial review or a comprehensive answer-quality evaluation.

The FAISS adapter emits an upstream `langchain-community` deprecation warning. The existing integration still passes retrieval and automated checks; migration is a future maintenance task.
