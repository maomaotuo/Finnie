
"""Test Finnie's Finance QA agent directly."""

from src.agents.finance_qa_agent import finance_qa_agent

QUESTIONS = [
    "What is an ETF?",
    "What is a designated Roth account?",
    "How is credit card interest calculated?",
    "How should I build an emergency fund?",
]


def main():
    for question in QUESTIONS:
        print("\n" + "=" * 70)
        print("QUESTION:", question)

        state = {
            "question": question,
            "selected_agent": "finance_qa",
            "answer": "",
            "sources": [],
        }

        result = finance_qa_agent(state)

        print("\nANSWER:")
        print(result.get("answer", ""))

        print("\nSOURCES:")
        for source in result.get("sources", []):
            print(source)


if __name__ == "__main__":
    main()
