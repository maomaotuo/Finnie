"""LLM supervisor with an explicit manual route and deterministic outage fallback."""
import re
import logging
from typing import Literal
from pydantic import BaseModel, Field
from src.core.llm import get_llm
from src.agents.base_agent import conversation_context
from src.agents.market_overview import is_market_overview
from src.workflow.state import AgentName
AGENTS = ("finance_qa", "portfolio", "market", "goal", "news", "tax")
GREETING = re.compile(
    r"(?:hi|hey|hello|good morning|good afternoon|good evening)"
    r"(?:[, ]+finnie| there)?[.!?👋\s]*",
    re.IGNORECASE,
)


class RoutingDecision(BaseModel):
    agent: AgentName = Field(description="Best first specialist for this turn")
    market_news: Literal["none", "headlines", "explain_move"] = Field(
        default="none", description="News work needed after a Market Analysis result",
    )


def fallback_market_news(question):
    if re.search(r"\bwhy\b", question, re.IGNORECASE):
        return "explain_move"
    if re.search(r"\b(news|headlines)\b", question, re.IGNORECASE):
        return "headlines"
    return "none"

def fallback_route(question, previous="finance_qa"):
    q = question.lower()
    if is_market_overview(q) or (
        re.search(r"\b(price|quote|trading at)\b", q) and fallback_market_news(q) == "headlines"
    ):
        return "market"
    for agent, pattern in [
        ("news", r"\b(news|headlines)\b"),
        ("portfolio", r"\b(portfolio|holdings|allocation)\b"),
        ("goal", r"\b(goal|save|saving|afford|monthly contribution|retire in)\b"),
        ("tax", r"\b(tax|taxes|capital gains|deductible)\b"),
        ("market", r"\b(price|quote|ticker|market|stock today|chart)\b"),
    ]:
        if re.search(pattern, q): return agent
    if re.search(r"\b(it|that|those|them|instead|also)\b", q) and previous in AGENTS:
        return previous
    return "finance_qa"
def workflow_router(state):
    # Clear per-turn outputs so a new answer does not inherit old citations or calculations.
    reset = {"sources": [], "answer": "", "error": "", "portfolio_analysis": {},
             "goal_analysis": {}, "market_data": {}, "market_comparison": "", "market_quote": "", "market_news": "none", "is_greeting": False}
    # Standalone greetings can be answered immediately without a model or specialist.
    if GREETING.fullmatch(state["question"].strip()):
        return {
            **reset,
            "is_greeting": True,
            "answer": "Hi! I’m Finnie. What would you like to explore today? "
                      "We can talk about investing basics, your portfolio, or a savings goal.",
        }
    # A specialist explicitly selected in the sidebar takes precedence over model routing.
    override = state.get("agent_override", "auto")
    if override in AGENTS and override != "market":
        return {**reset, "selected_agent": override}
    try:
        # Structured output limits the model to one of the registered specialist names.
        decision = get_llm().with_structured_output(RoutingDecision, method="json_schema").invoke(
            "Choose the first specialist for this financial education request: "
            "finance_qa (definitions, ETFs, retirement account basics), portfolio (holdings and allocation), "
            "market (prices, trends, and broad stock market performance), goal (savings projections), news (headlines and recent company developments, such as what a company is doing with AI), "
            "tax (tax-specific rules). Use prior conversation to resolve brief follow-ups. A new standalone definition question goes to finance_qa even after news.\n"
            "Choose market first for market performance, requests combining quotes and news, "
            "or requests for drivers behind a price move. For market, set market_news to headlines "
            "when the user also wants news, explain_move when they want the reason for a move "
            "even if phrased without a question word, and none for market data alone. "
            "Choose news for standalone headline or company development requests. "
            f"Specialist override: {override}.\n"
            f"History: {conversation_context(state)}\nQuestion: {state['question']}"
        )
        if not isinstance(decision, RoutingDecision):
            decision = RoutingDecision.model_validate(decision)
        agent = "market" if override == "market" else decision.agent
        market_news = decision.market_news
    except Exception as exc:
        logging.getLogger(__name__).warning("Router fallback (%s)", type(exc).__name__)
        # Keyword rules keep routing available when the model call fails.
        agent = "market" if override == "market" else fallback_route(
            state["question"], state.get("selected_agent", "finance_qa"),
        )
        market_news = fallback_market_news(state["question"])
    return {**reset, "selected_agent": agent, "market_news": market_news if agent == "market" else "none"}
