from src.rag.retriever import get_retriever

QUESTIONS = [
    "What is a designated Roth account?",
    "How is credit card interest calculated?",
    "What is a required minimum distribution?",
    "How should I build an emergency fund?",
    "What is an ETF?",
]


def main():
    retriever = get_retriever()

    for question in QUESTIONS:
        print(f"\n{'=' * 70}")
        print(f"QUESTION: {question}")

        docs = retriever.invoke(question)

        for i, doc in enumerate(docs, 1):
            print(f"\nRESULT {i}")
            print("Title:", doc.metadata.get("title", "Unknown"))
            print("Article ID:", doc.metadata.get("article_id", "N/A"))
            print("Source URL:", doc.metadata.get("source_url", "N/A"))
            print("Content:", doc.page_content[:350])


if __name__ == "__main__":
    main()
