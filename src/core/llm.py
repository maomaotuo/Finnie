"""Lazy model construction lets calculators and dashboards work without API credentials."""
from functools import lru_cache
from src.core.config import option
@lru_cache(maxsize=1)
def get_llm():
    # Create the model client only when a caller needs it, then reuse it.
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(model=option("gemini_model"),
                                  max_retries=2, timeout=45)
def response_text(response):
    text = response.text
    if isinstance(text, str):
        return str(text)
    return text() if callable(text) else str(text)
