"""Typed contracts shared by the router, agents, and interface."""
from typing import TypedDict, Literal, NotRequired, Any
AgentName = Literal["finance_qa", "portfolio", "market", "goal", "news", "tax"]
# Nodes return partial updates to this shared state. A thread checkpoint carries it between turns.
class FinanceState(TypedDict, total=False):
    question: str
    selected_agent: AgentName
    agent_override: str
    answer: str
    is_greeting: bool
    portfolio: list[dict[str, Any]]
    portfolio_analysis: dict[str, Any]
    sources: list[dict[str, Any]]
    symbol: str
    period: str
    market_news: Literal["none", "headlines", "explain_move"]
    market_comparison: str
    market_quote: str
    market_data: dict[str, Any]
    goal: dict[str, Any]
    goal_analysis: dict[str, Any]
    history: list[dict[str, str]]
    category: str
    error: str
