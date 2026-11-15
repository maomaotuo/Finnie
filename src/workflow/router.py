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
MOVE_EXPLANATION = re.compile(
    r"\b(?:why\b|what\s+(?:drove|caused|explains)\b|"
    r"what(?:'s|’s|\s+is|\s+was)\s+behind\b|"
    r"explain\s+(?:the\s+)?(?:reason|drivers?|factors?)\b)",
    re.IGNORECASE,
)
TAX_TOPIC = re.compile(
    r"\b(?:tax(?:es|ed|able|ation)?|deductible|deductions?|capital\s+(?:gains?|loss(?:es)?))\b"
    r"|\b(?:long|short)[\s\-‐‑–]+term\s+(?:capital\s+)?gains?\b"
    r"|\bholding[\s\-]+periods?\b",
    re.IGNORECASE,
)


class RoutingDecision(BaseModel):
    agent: AgentName = Field(description="Specialist best suited to the user's primary intent")
    market_news: Literal["none", "headlines", "explain_move"] = Field(
        default="none", description="News work needed after a Market Analysis result",
    )


def fallback_market_news(question):
    if MOVE_EXPLANATION.search(question):
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
        ("tax", TAX_TOPIC),
        ("market", r"\b(price|quote|ticker|market|stock today|chart)\b"),
    ]:
        if re.search(pattern, q):
            return agent
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
            "Read the full request and choose the specialist best suited to the user's primary intent. "
            "Use relevant conversation history to interpret brief follow-ups. "
            "Use tax for tax concepts, treatment, and rules, including capital-gain definitions, "
            "holding periods for tax classification, and comparisons of short-term and long-term gains. "
            "Use finance_qa for general financial definitions, ETF basics, and how retirement accounts work. "
            "If the request asks about taxes on an ETF or retirement account, use tax. "
            "For example, 'What is a Roth IRA?' goes to finance_qa, and "
            "'Are Roth IRA withdrawals taxable?' goes to tax. "
            "Use portfolio for holdings and allocation, and goal for savings projections. "
            "For each new standalone question, use its own intent.\n"
            "Choose market when the answer needs price or performance data, including when the user "
            "also asks for headlines or an explanation of a price move. For market, set market_news to headlines "
            "when the user also wants news, explain_move when they want the reason for a move "
            "even if phrased without a question word, and none for market data alone. "
            "Choose news for standalone headline or company development requests, "
            "such as what a company is doing with AI. "
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
    # Recover an explicit request for a price-move explanation if the model
    # chose Market but omitted the News handoff. Other intents stay model-driven.
    if agent == "market" and market_news == "none" and MOVE_EXPLANATION.search(state["question"]):
        market_news = "explain_move"
    # Resolve overlap between the two educational specialists.
    if agent == "finance_qa" and TAX_TOPIC.search(state["question"]):
        agent = "tax"
    return {**reset, "selected_agent": agent, "market_news": market_news if agent == "market" else "none"}
