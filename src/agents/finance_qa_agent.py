"""General financial education specialist using the shared RAG service."""
from src.rag.pipeline import answer_with_rag
from src.workflow.state import FinanceState

FINANCE_INSTRUCTIONS = (
    "Explain financial concepts, investment types, diversification, and retirement "
    "account basics in accessible language. Search broadly across financial "
    "education. Define unfamiliar terms and distinguish factual explanations "
    "from personalized recommendations. Do not invent performance figures."
)


def finance_qa_agent(state: FinanceState):
    return answer_with_rag(state, instructions=FINANCE_INSTRUCTIONS)
