"""LLM supervisor with an explicit manual route and deterministic outage fallback."""
import re
import logging
from pydantic import BaseModel, Field
from src.core.llm import get_llm
from src.agents.base_agent import conversation_context
from src.workflow.state import AgentName
AGENTS = ("finance_qa", "portfolio", "market", "goal", "news", "tax")
GREETING = re.compile(
    r"(?:hi|hey|hello|good morning|good afternoon|good evening)"
    r"(?:[, ]+finnie| there)?[.!?👋\s]*",
    re.IGNORECASE,
)


class RoutingDecision(BaseModel):
    agent: AgentName = Field(description="Best specialized agent for this turn")
def fallback_route(question, previous="finance_qa"):
    q = question.lower()
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
             "goal_analysis": {}, "market_data": {}, "market_comparison": "", "is_greeting": False}
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
    if override in AGENTS:
        return {**reset, "selected_agent": override}
    try:
        # Structured output limits the model to one of the registered specialist names.
        decision = get_llm().with_structured_output(RoutingDecision, method="json_schema").invoke(
            "Route this financial education conversation to exactly one specialist: "
            "finance_qa (definitions, ETFs, retirement account basics), portfolio (holdings and allocation), "
            "market (prices and trends), goal (savings projections), news (headlines and recent company developments, such as what a company is doing with AI), "
            "tax (tax-specific rules). Use prior conversation to resolve brief follow-ups. A new standalone definition question goes to finance_qa even after news.\n"
            f"History: {conversation_context(state)}\nQuestion: {state['question']}"
        )
        agent = decision.agent if isinstance(decision, RoutingDecision) else RoutingDecision.model_validate(decision).agent
    except Exception as exc:
        logging.getLogger(__name__).warning("Router fallback (%s)", type(exc).__name__)
        # Keyword rules keep routing available when the model call fails.
        agent = fallback_route(state["question"], state.get("selected_agent", "finance_qa"))
    return {**reset, "selected_agent": agent}
