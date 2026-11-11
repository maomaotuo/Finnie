from src.agents.finance_qa_agent import finance_qa_agent

questions = [
    "What is the difference between stocks, ETFs, and mutual funds?",
    "What is the difference between individual bonds and bond funds?",
    "How does diversification reduce investment risk?",
    "How should risk tolerance affect investment selection?",
    "How can I build a diversified portfolio using ETFs?",
]

for question in questions:
    print("\n" + "=" * 70)
    print("QUESTION:", question)

    result = finance_qa_agent({"question": question})

    print("\nANSWER:")
    print(result.get("answer", ""))

    print("\nSOURCES:")
    for source in result.get("sources", []):
        print(
            f"[{source['number']}] "
            f"{source['title']} "
            f"({source['article_id']})"
        )
        print(source.get("url", ""))
