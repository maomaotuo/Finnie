"""Exercise tool discovery and calls through a real local MCP subprocess."""

import asyncio
from pathlib import Path
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def test_mcp_stdio_tools():
    async def run():
        server = Path(__file__).resolve().parents[1] / "mcp_server.py"
        params = StdioServerParameters(command=sys.executable, args=[str(server)])
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                discovered = await session.list_tools()
                tools = {tool.name: tool for tool in discovered.tools}
                assert set(tools) == {
                    "finnie_analyze_portfolio", "finnie_project_goal", "finnie_market_quote",
                }
                assert all(tool.annotations.readOnlyHint for tool in tools.values())

                goal = await session.call_tool("finnie_project_goal", {
                    "target": 1200, "years": 1, "monthly": 100, "annual_return_pct": 0,
                })
                assert not goal.isError
                assert goal.structuredContent["projected_value"] == 1200
                assert goal.structuredContent["on_track"] is True

                portfolio = await session.call_tool("finnie_analyze_portfolio", {
                    "holdings": [
                        {"symbol": "AAA", "quantity": 2, "price": 50, "asset_type": "stock"},
                        {"symbol": "BBB", "quantity": 1, "price": 100, "asset_type": "bond"},
                    ],
                })
                assert not portfolio.isError
                assert portfolio.structuredContent["total_value"] == 200
                assert portfolio.structuredContent["asset_allocation_pct"] == {"stock": 50, "bond": 50}

                invalid = await session.call_tool("finnie_project_goal", {
                    "target": 0, "years": 1,
                })
                assert invalid.isError

    asyncio.run(asyncio.wait_for(run(), timeout=20))
