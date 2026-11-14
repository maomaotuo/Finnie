"""Six-agent LangGraph with isolated session checkpoints and bounded memory."""
import logging
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from src.workflow.state import FinanceState
from src.workflow.router import workflow_router
from src.agents.finance_qa_agent import finance_qa_agent
from src.agents.portfolio_agent import portfolio_agent
from src.agents.market_agent import market_agent
from src.agents.goal_agent import goal_agent
from src.agents.news_agent import news_agent
from src.agents.tax_agent import tax_agent
from src.agents.base_agent import DISCLAIMER

# Wrap specialists at the workflow boundary so failures become readable chat replies.
def guarded(agent):
    def execute(state):
        try:
            return agent(state)
        except ValueError as exc:
            return {"answer": f"Please check your input: {exc}", "error": "validation"}
        except Exception as exc:
            logging.getLogger(__name__).warning("Agent unavailable (%s)", type(exc).__name__)
            return {"answer": "This service is temporarily unavailable. Please try again or use the portfolio and goal calculators.",
                    "error": "service_unavailable", "sources": []}
    return execute

def remember(state):
    history = state.get("history", []) + [
        {"role": "user", "content": state["question"]},
        {"role": "assistant", "content": state["answer"]},
    ]
    # Keep the last ten exchanges so the conversation context stays bounded.
    return {"history": history[-20:]}

def combine_market_news(state):
    """Combine the market result and the News Agent's sourced response."""
    market = state.get("market_quote") or state["market_comparison"]
    if state.get("market_comparison"):
        market += "\n\nHeadlines can provide context, but they cannot by themselves establish what caused the move."
    news = state["answer"].removesuffix(DISCLAIMER).rstrip()
    return {"answer": f"{market}\n\n{news}\n\n{DISCLAIMER}"}


def has_market_news(state):
    return bool(state.get("market_comparison") or state.get("market_quote"))


def build_graph(checkpointer=None):
    graph = StateGraph(FinanceState)
    graph.add_node("router", workflow_router)
    agents = {"finance_qa": finance_qa_agent, "portfolio": portfolio_agent,
              "market": market_agent, "goal": goal_agent, "news": news_agent, "tax": tax_agent}
    for name, agent in agents.items(): graph.add_node(name, guarded(agent))
    graph.add_node("remember", remember)
    graph.add_edge(START, "router")
    # The router chooses one specialist, or goes straight to memory for a greeting.
    graph.add_conditional_edges(
        "router",
        lambda state: "remember" if state.get("is_greeting") else state["selected_agent"],
        {**{name: name for name in agents}, "remember": "remember"},
    )
    graph.add_node("combine_market_news", combine_market_news)
    graph.add_conditional_edges(
        "market",
        lambda state: "news" if has_market_news(state) else "remember",
        ["news", "remember"],
    )
    graph.add_conditional_edges(
        "news",
        lambda state: "combine_market_news" if has_market_news(state) else "remember",
        ["combine_market_news", "remember"],
    )
    graph.add_edge("combine_market_news", "remember")
    for name in agents.keys() - {"market", "news"}:
        graph.add_edge(name, "remember")
    graph.add_edge("remember", END)
    # Checkpoints separate conversations by thread ID. The default store lives in memory.
    return graph.compile(checkpointer=checkpointer if checkpointer is not None else InMemorySaver())
