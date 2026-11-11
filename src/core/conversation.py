"""Bound conversational context shared by routing and answer generation."""


def conversation_context(state):
    history = state.get("history", [])[-8:]
    return "\n".join(
        f"{turn['role']}: {turn['content'][:2000]}" for turn in history
    )
