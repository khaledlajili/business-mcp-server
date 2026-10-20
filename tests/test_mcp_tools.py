import pytest
from mcp import Client
from app.mcp_server import mcp


@pytest.mark.asyncio
async def test_list_tools():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        names = {t.name for t in tools.tools}
        expected = {
            "search_customers",
            "get_order",
            "check_inventory",
            "create_quote",
            "get_sales_summary",
            "create_support_ticket",
        }
        assert expected.issubset(names)


@pytest.mark.asyncio
async def test_search_customers_tool():
    async with Client(mcp) as client:
        result = await client.call_tool("search_customers", {"query": "Customer", "limit": 2})
        assert result.is_error is False
        assert len(result.content) > 0
