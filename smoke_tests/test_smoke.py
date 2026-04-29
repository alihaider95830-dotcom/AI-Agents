from __future__ import annotations

import os

import httpx
import pytest

API = os.environ["SMOKE_API_URL"].rstrip("/")
FRONTEND = os.environ["SMOKE_FRONTEND_URL"].rstrip("/")
ADMIN_KEY = os.environ["SMOKE_ADMIN_KEY"]


@pytest.fixture(scope="session")
def client():
    with httpx.Client(timeout=30) as http_client:
        yield http_client


def test_health_returns_ok(client):
    response = client.get(f"{API}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_db_connected(client):
    response = client.get(f"{API}/health/db")
    assert response.status_code == 200
    assert response.json()["db"] == "ok"


def test_protected_route_requires_auth(client):
    response = client.get(f"{API}/api/v1/me")
    assert response.status_code == 401


def test_reports_requires_auth(client):
    response = client.get(f"{API}/api/v1/reports")
    assert response.status_code == 401


def test_stream_requires_auth(client):
    response = client.get(f"{API}/api/v1/stream/fake-job-id")
    assert response.status_code in (401, 403)


def test_webhook_requires_signature(client):
    response = client.post(
        f"{API}/api/v1/billing/webhook",
        json={"type": "test"},
        headers={"Stripe-Signature": "invalid"},
    )
    assert response.status_code == 400


def test_admin_requires_key(client):
    response = client.get(f"{API}/api/v1/admin/stripe-events")
    assert response.status_code == 401


def test_admin_key_works(client):
    response = client.get(
        f"{API}/api/v1/admin/stripe-events",
        headers={"X-Admin-Key": ADMIN_KEY},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_health_returns_request_id(client):
    response = client.get(f"{API}/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers


def test_cors_header_present(client):
    response = client.options(
        f"{API}/api/v1/reports",
        headers={
            "Origin": FRONTEND,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" in response.headers


def test_docs_not_exposed_in_prod(client):
    response = client.get(f"{API}/docs")
    assert response.status_code in (404, 403)


def test_openapi_json_not_exposed(client):
    response = client.get(f"{API}/openapi.json")
    assert response.status_code in (404, 403)


def test_frontend_homepage_loads(client):
    response = client.get(FRONTEND)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_frontend_pricing_page_loads(client):
    response = client.get(f"{FRONTEND}/pricing")
    assert response.status_code == 200


def test_frontend_returns_security_headers(client):
    response = client.get(FRONTEND)
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_frontend_404_handled(client):
    response = client.get(f"{FRONTEND}/this-page-does-not-exist-xyz")
    assert response.status_code == 404
