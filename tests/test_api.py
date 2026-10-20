import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
HEADERS = {"X-Internal-API-Key": "dev-internal-token"}


def test_customers_requires_token():
    r = client.get("/api/v1/customers")
    assert r.status_code == 401


def test_search_customers():
    r = client.get("/api/v1/customers?query=Customer&limit=5", headers=HEADERS)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_order_not_found():
    r = client.get("/api/v1/orders/99999", headers=HEADERS)
    assert r.status_code == 404


def test_inventory_not_found():
    r = client.get("/api/v1/inventory/NOPE", headers=HEADERS)
    assert r.status_code == 404
