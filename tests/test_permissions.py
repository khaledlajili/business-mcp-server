import pytest
from mcp import Client
from app.mcp_server import mcp
from app.config import settings


@pytest.mark.asyncio
async def test_read_token_can_search():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_customers",
            {"query": "Customer", "limit": 1, "token": settings.mcp_read_token},
        )
        assert result.is_error is False


@pytest.mark.asyncio
async def test_read_token_cannot_create_quote():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "create_quote",
            {
                "customer_id": 1,
                "items": [{"sku": "SKU-001", "quantity": 1}],
                "request_id": "perm-test-1",
                "token": settings.mcp_read_token,
            },
        )
        assert result.is_error is True


@pytest.mark.asyncio
async def test_write_token_can_create_quote():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "create_quote",
            {
                "customer_id": 1,
                "items": [{"sku": "SKU-001", "quantity": 1}],
                "request_id": "perm-test-write-1",
                "token": settings.mcp_write_token,
            },
        )
        assert result.is_error is False


@pytest.mark.asyncio
async def test_invalid_token_rejected():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_customers",
            {"query": "x", "token": "bad-token"},
        )
        assert result.is_error is True
