"""Recognize standalone questions about the latest broad U.S. market session."""
import re


# Match whole questions so company comparisons still use entity extraction.
_US_MARKET = r"(?:the\s+)?(?:(?:u\.?s\.?|united states)\s+)?(?:stock market|stocks|wall street|broader market|market)"
_SESSION = r"(?:\s+(?:today|right now|so far today))?"
_MARKET_UPDATE = re.compile(
    rf"(?:how\s+(?:is|are|was|were|did)\s+{_US_MARKET}"
    rf"(?:\s+(?:doing|performing|perform|do))?{_SESSION}"
    rf"|(?:is|are|was|were)\s+{_US_MARKET}\s+(?:up|down)(?:\s+or\s+(?:up|down))?{_SESSION}"
    rf"|(?:why\s+(?:is|are|was|were|did)\s+{_US_MARKET}"
    rf"\s+(?:up|down|rising|falling|rise|fall|drop|rally){_SESSION}))[?.!]*",
    re.IGNORECASE,
)


def is_market_overview(question: str) -> bool:
    return _MARKET_UPDATE.fullmatch(question.strip()) is not None
