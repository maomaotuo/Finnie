"""Command-line conversation. Launch the web UI using the README instructions."""
from uuid import uuid4
from src.workflow.graph import build_graph

def main():
    graph=build_graph()
    # The same thread ID lets LangGraph restore conversation state on each turn.
    config={"configurable":{"thread_id":str(uuid4())}}
    print("Finnie · Financial education. Type 'quit' to exit.")
    while True:
        try: question=input("You: ").strip()
        except (EOFError, KeyboardInterrupt): break
        if question.lower() in {"quit","exit"}: break
        if not question: continue
        result=graph.invoke({"question":question,"agent_override":"auto"},config)
        label = "Finnie" if result.get("is_greeting") else f"Finnie ({result['selected_agent']})"
        print(f"\n{label}: {result['answer']}\n")
        for source in result.get("sources",[]): print(f"[{source['number']}] {source['title']}: {source['url']}")
if __name__ == "__main__": main()
