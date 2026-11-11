"""Evaluate Finnie's RAG retrieval quality."""

from src.rag.retriever import get_retriever


EVAL_CASES = [
    {
        "question": "What is a designated Roth account?",
        "expected_ids": ["retirement_001"],
    },
    {
        "question": "How is credit card interest calculated?",
        "expected_ids": ["credit_003"],
    },
    {
        "question": "What is a required minimum distribution?",
        "expected_ids": ["retirement_008"],
    },
    {
        "question": "How should I build an emergency fund?",
        "expected_ids": ["saving_001", "basics_009"],
    },
    {
        "question": "What is an ETF?",
        "expected_ids": ["basics_003", "investing_014"],
    },
    {
        "question": "What is the difference between stocks, ETFs, and mutual funds?",
        "expected_ids": ["investing_006"],
    },
    {
        "question": "What is the difference between individual bonds and bond funds?",
        "expected_ids": ["investing_007"],
    },
    {
        "question": "How does diversification reduce investment risk?",
        "expected_ids": ["investing_010", "investing_011"],
    },
    {
        "question": "How should risk tolerance affect investment selection?",
        "expected_ids": ["investing_009", "investing_014"],
    },
    {
        "question": "How can I build a diversified portfolio using ETFs?",
        "expected_ids": ["investing_014"],
    },
]


def evaluate():
    retriever = get_retriever()

    hits = 0
    reciprocal_rank_sum = 0.0

    for index, case in enumerate(EVAL_CASES, start=1):
        documents = retriever.invoke(case["question"])

        retrieved_ids = [
            doc.metadata.get("article_id")
            for doc in documents
        ]

        expected = set(case["expected_ids"])

        # Compare the returned article IDs with the known sources for this question.
        matching_ranks = [
            rank
            for rank, article_id in enumerate(retrieved_ids, start=1)
            if article_id in expected
        ]

        hit = bool(matching_ranks)
        # A match near the top scores higher. No match contributes zero.
        reciprocal_rank = (
            1.0 / min(matching_ranks)
            if matching_ranks
            else 0.0
        )

        hits += int(hit)
        reciprocal_rank_sum += reciprocal_rank

        print(f"\n{index}. {case['question']}")
        print(f"Expected: {case['expected_ids']}")
        print(f"Retrieved: {retrieved_ids}")
        print(f"Hit: {'PASS' if hit else 'FAIL'}")
        print(f"Reciprocal rank: {reciprocal_rank:.3f}")

    total = len(EVAL_CASES)

    hit_rate = hits / total
    mrr = reciprocal_rank_sum / total

    print("\n" + "=" * 60)
    print("FINNIE RAG RETRIEVAL EVALUATION")
    print("=" * 60)
    print(f"Questions evaluated: {total}")
    print(f"Hit Rate@5: {hit_rate:.2%}")
    print(f"MRR@5: {mrr:.3f}")


if __name__ == "__main__":
    evaluate()
