"""Expose Finnie's read-only financial education tools over local MCP stdio."""

from typing import Annotated, Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from src.agents.market_data import get_market_chart
from src.agents.market_symbol_resolver import resolve_symbol
from src.utils.calculators import analyze_portfolio, project_goal

# FastMCP turns registered Python functions into tools an MCP client can discover.
mcp = FastMCP("Finnie")
READ_ONLY = ToolAnnotations(readOnlyHint=True)
Period = Literal["1D", "1W", "1M", "3M", "6M", "1Y", "5Y"]


# The client sees this input schema and FastMCP validates each holding before the call.
class Holding(BaseModel):
    symbol: str
    quantity: float = Field(gt=0)
    price: float = Field(gt=0, description="User-supplied price per unit")
    asset_type: Literal["stock", "etf", "bond", "cash", "mutual_fund", "other"]
    expense_ratio_pct: float | None = Field(default=None, ge=0, le=100)


@mcp.tool(annotations=READ_ONLY, structured_output=True)
def finnie_analyze_portfolio(
    holdings: Annotated[list[Holding], Field(min_length=1)],
) -> dict[str, Any]:
    """Calculate allocation, concentration, and fees from supplied holdings and prices."""
    return analyze_portfolio([holding.model_dump() for holding in holdings])


@mcp.tool(annotations=READ_ONLY, structured_output=True)
def finnie_project_goal(
    target: float,
    years: float,
    initial: float = 0,
    monthly: float = 0,
    annual_return_pct: float = 5,
) -> dict[str, Any]:
    """Project savings with a constant annual return and end-of-month contributions.

    Amounts use the same currency. The return assumption is a percentage.
    Results exclude taxes, fees, inflation, and volatility.
    """
    result = project_goal(target, years, initial, monthly, annual_return_pct)
    # Return a compact summary for the client model rather than every chart point.
    result.pop("trajectory")
    return result


@mcp.tool(annotations=READ_ONLY, structured_output=True)
def finnie_market_quote(
    company_or_ticker: Annotated[str, Field(min_length=1, max_length=100)],
    period: Period = "1D",
) -> dict[str, Any]:
    """Get the latest available Yahoo Finance price and period change for a stock or ETF."""
    # Resolve a company name to the provider ticker before asking for prices.
    symbol = resolve_symbol(company_or_ticker.strip().lstrip("$"))
    if not symbol:
        raise ValueError("Could not resolve the company or ticker. Check the spelling.")
    quote = get_market_chart(symbol, period)
    if "error" in quote:
        raise ValueError(quote["error"])
    return {
        **{key: value for key, value in quote.items() if key != "prices"},
        "source": "Yahoo Finance via yfinance",
        "note": "Prices may be delayed. Historical prices are adjusted.",
    }


if __name__ == "__main__":
    # The client starts this process and exchanges protocol messages over stdin and stdout.
    mcp.run(transport="stdio")
