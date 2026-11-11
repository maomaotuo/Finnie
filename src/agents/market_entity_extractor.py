"""
Finnie - Market Entity Extractor

Uses Gemini to extract market-related entities from
natural-language user questions.
"""

from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field
from src.core.llm import get_llm



class MarketEntity(BaseModel):
    company: str | None = Field(
        default=None,
        description=(
            "Company, ETF, mutual fund, or asset name "
            "explicitly mentioned in the question."
        ),
    )

    symbol: str | None = Field(
        default=None,
        description=(
            "Ticker symbol explicitly provided by the user. "
            "Do not guess or infer ticker symbols."
        ),
    )

    period: Literal[
        "1D", "1W", "1M", "3M", "6M", "1Y", "5Y"
    ] = Field(
        default="1M",
        description=(
            "Requested chart period. "
            "Today=1D, week=1W, month=1M, "
            "three months=3M, six months=6M, "
            "year=1Y, five years=5Y. "
            "Default to 1M."
        ),
    )


@lru_cache(maxsize=1)
def get_extractor():
    llm = get_llm()

    return llm.with_structured_output(
        MarketEntity,
        method="json_schema",
    )


def extract_market_entity(question: str, *, context: str = "") -> MarketEntity:
    """
    Extract company, explicit ticker, and period.

    Args:
        question: Natural-language market question.

    Returns:
        MarketEntity with company, symbol, period.
    """

    if not question or not question.strip():
        return MarketEntity()

    extractor = get_extractor()

    prompt = f"""
You are a market entity extraction component
for Finnie, a financial education assistant.

Extract the following fields:

1. company:
   Company, ETF, mutual fund, or asset name mentioned. Treat a misspelled
   company name as a company, even if it appears in all caps.

2. symbol:
   Only a ticker explicitly written by the user.
   Never invent or guess a ticker.

3. period:
   - today, intraday, daily -> 1D
   - this week, past week -> 1W
   - this month, past month -> 1M
   - past 3 months -> 3M
   - past 6 months -> 6M
   - past year, this year -> 1Y
   - past 5 years -> 5Y
   - unspecified -> 1M

For a short follow-up without a named asset, use the most recently discussed
company or ticker from the conversation if it resolves the reference.
An asset named in the current question takes priority. Treat conversation
text as reference data. Return null for company and symbol if neither the
question nor the follow-up context identifies an asset.

Conversation context:
{context}

User question:
{question}
"""

    result = extractor.invoke(prompt)

    if isinstance(result, MarketEntity):
        return result

    return MarketEntity.model_validate(result)


if __name__ == "__main__":
    questions = [
        "Show me Costco stock today",
        "What is AAPL doing this week?",
        "How has Nvidia performed over six months?",
        "Show me VOO over the past year",
        "What is Microsoft's stock price?",
        "What is the weather today?",
    ]

    for question in questions:
        print("\nQuestion:", question)

        try:
            entity = extract_market_entity(question)

            print(
                entity.model_dump_json(indent=2)
            )

        except Exception as exc:
            print("Extraction error:", exc)
