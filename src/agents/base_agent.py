"""Shared, bounded conversational context and graceful generation failure."""
import logging
from src.core.llm import get_llm, response_text
from src.core.conversation import conversation_context
DISCLAIMER = "Educational information only; not personalized investment, legal, or tax advice."
logger = logging.getLogger(__name__)
def generate(prompt, fallback):
    try:
        return response_text(get_llm().invoke(prompt))
    except Exception as exc:
        logger.warning("Generation unavailable (%s)", type(exc).__name__)
        return fallback
