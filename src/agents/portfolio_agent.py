"""Portfolio analysis combines verified arithmetic with optional explanation."""
from src.agents.base_agent import generate, conversation_context, DISCLAIMER
from src.utils.calculators import analyze_portfolio

def portfolio_agent(state):
    if not state.get("portfolio"):
        return {"answer":"Add your holdings in the Portfolio tab, then ask me about allocation or concentration. For example: Which holding makes up the largest share of my portfolio?"}
    # Calculate the numbers in Python. The model receives the results to explain them.
    analysis=analyze_portfolio(state["portfolio"])
    fallback=(f"Your supplied holdings total ${analysis['total_value']:,.2f}. "
              f"For example, your largest position is {analysis['largest_position']['symbol']} "
              f"at {analysis['largest_position']['allocation_pct']}%. "
              "These are user-supplied illustrative prices. Holding-level concentration does not measure underlying ETF diversification.")
    answer=generate(f"Explain these verified portfolio metrics to a beginner. Use only supplied numbers; "
                    f"never infer ETF underlying exposure or recommend a specific investment. Prices are user supplied. "
                    "Include one short Example using a supplied holding or metric to illustrate the main point. "
                    f"History: {conversation_context(state)}\nQuestion: {state['question']}\nMetrics: {analysis}", fallback)
    return {"answer":answer+"\n\n"+DISCLAIMER,"portfolio_analysis":analysis}
