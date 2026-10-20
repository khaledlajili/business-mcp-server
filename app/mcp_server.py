from typing import Any

import httpx
from mcp.server import MCPServer

from app.auth import require_scope
from app.config import settings
from app.database import AsyncSessionLocal
from app.audit import write_audit

mcp = MCPServer("Northstar Trading")

API_BASE = "http://127.0.0.1:8000"
INTERNAL_HEADERS = {"X-Internal-API-Key": settings.internal_api_token}
TIMEOUT = httpx.Timeout(10.0)


async def _call_api(method: str, path: str, **kwargs) -> dict[str, Any] | list:
    async with httpx.AsyncClient(base_url=API_BASE, headers=INTERNAL_HEADERS, timeout=TIMEOUT) as client:
        response = await client.request(method, path, **kwargs)
        if response.status_code >= 400:
            detail = (
                response.json().get("detail", response.text)
                if response.headers.get("content-type", "").startswith("application/json")
                else response.text
            )
            raise RuntimeError(f"API error {response.status_code}: {detail}")
        return response.json() if response.content else {}


async def _audit(actor: str, tool: str, outcome: str, request_id: str | None = None):
    async with AsyncSessionLocal() as db:
        await write_audit(db, actor, tool, outcome, request_id)


def _actor_from_token(token: str) -> str:
    if token == settings.mcp_read_token:
        return "mcp-read"
    if token == settings.mcp_write_token:
        return "mcp-write"
    return "unknown"


@mcp.tool()
async def search_customers(query: str = "", limit: int = 10, token: str = "") -> list:
    """Search customers by name or email. Read-only."""
    try:
        require_scope(token, "customers:read")
        result = await _call_api("GET", "/api/v1/customers", params={"query": query, "limit": min(limit, 50)})
        await _audit(_actor_from_token(token), "search_customers", "success")
        return result
    except Exception as e:
        await _audit(_actor_from_token(token), "search_customers", "denied" if "scope" in str(e).lower() or "token" in str(e).lower() else "error")
        raise


@mcp.tool()
async def get_order(order_id: int, token: str = "") -> dict:
    """Return an order and its line items. Read-only."""
    try:
        require_scope(token, "orders:read")
        result = await _call_api("GET", f"/api/v1/orders/{order_id}")
        await _audit(_actor_from_token(token), "get_order", "success")
        return result
    except Exception as e:
        await _audit(_actor_from_token(token), "get_order", "denied" if "scope" in str(e).lower() or "token" in str(e).lower() else "error")
        raise


@mcp.tool()
async def check_inventory(sku: str, token: str = "") -> dict:
    """Return product and stock quantity. Read-only."""
    try:
        require_scope(token, "inventory:read")
        result = await _call_api("GET", f"/api/v1/inventory/{sku}")
        await _audit(_actor_from_token(token), "check_inventory", "success")
        return result
    except Exception as e:
        await _audit(_actor_from_token(token), "check_inventory", "denied" if "scope" in str(e).lower() or "token" in str(e).lower() else "error")
        raise


@mcp.tool()
async def create_quote(customer_id: int, items: list[dict], request_id: str, token: str = "") -> dict:
    """Create a draft quote only. Requires quotes:write."""
    try:
        require_scope(token, "quotes:write")
        payload = {"customer_id": customer_id, "items": items, "request_id": request_id}
        result = await _call_api("POST", "/api/v1/quotes", json=payload)
        await _audit(_actor_from_token(token), "create_quote", "success", request_id)
        return result
    except Exception as e:
        await _audit(_actor_from_token(token), "create_quote", "denied" if "scope" in str(e).lower() or "token" in str(e).lower() else "error", request_id)
        raise


@mcp.tool()
async def get_sales_summary(start_date: str, end_date: str, token: str = "") -> dict:
    """Sales summary for a date range. Read-only."""
    try:
        require_scope(token, "sales:read")
        result = await _call_api("GET", "/api/v1/sales/summary", params={"start_date": start_date, "end_date": end_date})
        await _audit(_actor_from_token(token), "get_sales_summary", "success")
        return result
    except Exception as e:
        await _audit(_actor_from_token(token), "get_sales_summary", "denied" if "scope" in str(e).lower() or "token" in str(e).lower() else "error")
        raise


@mcp.tool()
async def create_support_ticket(customer_id: int, subject: str, description: str, request_id: str, token: str = "") -> dict:
    """Create an open support ticket. Requires tickets:write."""
    try:
        require_scope(token, "tickets:write")
        payload = {"customer_id": customer_id, "subject": subject, "description": description, "request_id": request_id}
        result = await _call_api("POST", "/api/v1/support-tickets", json=payload)
        await _audit(_actor_from_token(token), "create_support_ticket", "success", request_id)
        return result
    except Exception as e:
        await _audit(_actor_from_token(token), "create_support_ticket", "denied" if "scope" in str(e).lower() or "token" in str(e).lower() else "error", request_id)
        raise
