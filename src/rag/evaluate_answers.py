"""Evaluate Finnie's Finance Q&A answer quality."""

import re

from src.agents.finance_qa_agent import finance_qa_agent
from src.rag.retriever import get_retriever


EVAL_CASES = [
    {
        "question": "What is a designated Roth account?",
        "concept_groups": [
            ["401(k)", "403(b)", "457(b)"],
            ["tax", "income"],
            ["distribution", "withdrawal"],
        ],
    },
    {
        "question": "How is credit card interest calculated?",
        "concept_groups": [
            ["daily balance", "average daily"],
            ["APR", "annual percentage rate"],
            ["interest"],
        ],
    },
    {
        "question": "What is an ETF?",
        "concept_groups": [
            ["exchange-traded fund", "ETF"],
            ["stocks", "bonds", "assets"],
            ["exchange", "trading"],
        ],
    },
    {
        "question": "How should I build an emergency fund?",
        "concept_groups": [
            ["savings", "save"],
            ["emergency", "unexpected"],
            ["expenses", "income"],
        ],
    },
    {
        "question": "What is the difference between individual bonds and bond funds?",
        "concept_groups": [
            ["individual bonds"],
            ["bond funds", "funds"],
            ["diversification", "diversified"],
            ["fees", "expense ratio", "costs"],
        ],
    },
]


def extract_answer(result):
    """Support the result format used by Finnie's agent."""
    if isinstance(result, str):
        return result

    if isinstance(result, dict):
        for key in ("answer", "response", "final_answer"):
            value = result.get(key)
            if isinstance(value, str):
                return value

    raise ValueError(
        "Cannot extract answer. Inspect finance_qa_agent's return format."
    )


def evaluate():
    retriever = get_retriever()

    total_coverage = 0.0
    valid_citations = 0
    citation_count = 0

    for case in EVAL_CASES:
        question = case["question"]

        # Use the same basic state structure as your agent tests.
        state = {"question": question}

        result = finance_qa_agent(state)
        answer = extract_answer(result)

        groups = case["concept_groups"]
        # Count expected concept groups represented by at least one matching term.
        matched = sum(
            any(term.lower() in answer.lower() for term in group)
            for group in groups
        )

        coverage = matched / len(groups)
        total_coverage += coverage

        # Retrieve article IDs separately to check whether citations refer to returned evidence.
        documents = retriever.invoke(question)
        retrieved_ids = {
            doc.metadata.get("article_id")
            for doc in documents
        }

        sources = (
            result.get("sources", [])
            if isinstance(result, dict)
            else []
        )

        for source in sources:
            if not isinstance(source, dict):
                continue

            article_id = source.get("article_id")
            citation_count += 1

            if article_id in retrieved_ids:
                valid_citations += 1

        print(f"\nQuestion: {question}")
        print(f"Concept coverage: {coverage:.0%}")
        print(f"Citations checked: {len(sources)}")
        print(f"Answer preview: {answer[:300]}")

    total = len(EVAL_CASES)

    print("\n" + "=" * 60)
    print("FINNIE ANSWER QUALITY EVALUATION")
    print("=" * 60)
    print(f"Questions: {total}")
    print(f"Average concept coverage: {total_coverage / total:.2%}")

    if citation_count:
        print(
            f"Citation source validity: "
            f"{valid_citations / citation_count:.2%}"
        )
    else:
        print("Citation source validity: Not measured (no sources found)")


if __name__ == "__main__":
    evaluate()
