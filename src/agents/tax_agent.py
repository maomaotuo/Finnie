"""Tax specialist with authority-first retrieval and explicit tax-context rules."""
from src.agents.base_agent import DISCLAIMER
from src.rag.pipeline import RetrievalPolicy, answer_with_rag
from src.workflow.state import FinanceState

TAX_NOTE = (
    "Tax treatment depends on jurisdiction and tax year; confirm current rules "
    "with the relevant tax authority."
)
TAX_POLICY = RetrievalPolicy(
    preferred_categories=("tax", "taxes", "taxation"),
    preferred_source_domains=("irs.gov",),
)
TAX_INSTRUCTIONS = (
    "Explain tax concepts directly and distinguish definitions from personalized "
    "tax calculations. Label IRS-based explanations as U.S. federal tax education; "
    "never apply U.S. rules to other jurisdictions. If the user asks about another "
    "country and the evidence is U.S.-only, explain that evidence limitation. "
    "For specific rates, brackets, or tax calculations, identify the jurisdiction "
    "and tax year and ask for missing details when needed. The absence of current-year "
    "brackets must not prevent explaining supported concepts or holding periods. "
    "Never invent rates, thresholds, or exceptions. Do not repeat earlier refusals "
    "when the current evidence answers the question. Do not add a disclaimer or "
    "generic jurisdiction warning; the application appends those once."
)


def tax_agent(state: FinanceState):
    result = answer_with_rag(state, instructions=TAX_INSTRUCTIONS, policy=TAX_POLICY)
    answer = result["answer"].replace(TAX_NOTE, "").replace(DISCLAIMER, "").strip()
    result["answer"] = answer + "\n\n" + TAX_NOTE + " " + DISCLAIMER
    return result
