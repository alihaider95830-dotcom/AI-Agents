from __future__ import annotations

import os
import sys
from collections.abc import Callable

import httpx


API_URL = os.environ.get("API_URL", "").rstrip("/")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "").rstrip("/")
ADMIN_KEY = os.environ.get("ADMIN_KEY", "")


def _require_env() -> list[str]:
    missing = []
    for name, value in (
        ("API_URL", API_URL),
        ("FRONTEND_URL", FRONTEND_URL),
        ("ADMIN_KEY", ADMIN_KEY),
    ):
        if not value:
            missing.append(name)
    return missing


def _check(name: str, fn: Callable[[httpx.Client], None], client: httpx.Client) -> bool:
    try:
        fn(client)
    except Exception as exc:
        print(f"FAIL {name}: {exc}")
        return False
    print(f"PASS {name}")
    return True


def check_api_health(client: httpx.Client) -> None:
    response = client.get(f"{API_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def check_api_db_health(client: httpx.Client) -> None:
    response = client.get(f"{API_URL}/health/db")
    assert response.status_code == 200
    assert response.json()["db"] == "ok"


def check_docs_disabled(client: httpx.Client) -> None:
    response = client.get(f"{API_URL}/docs")
    assert response.status_code == 404


def check_openapi_disabled(client: httpx.Client) -> None:
    response = client.get(f"{API_URL}/openapi.json")
    assert response.status_code == 404


def check_auth_required(client: httpx.Client) -> None:
    response = client.get(f"{API_URL}/api/v1/me")
    assert response.status_code == 401


def check_cors_header(client: httpx.Client) -> None:
    response = client.options(
        f"{API_URL}/api/v1/reports",
        headers={
            "Origin": FRONTEND_URL,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" in response.headers


def check_webhook_rejects_invalid_signature(client: httpx.Client) -> None:
    response = client.post(
        f"{API_URL}/api/v1/billing/webhook",
        json={"type": "test"},
        headers={"Stripe-Signature": "invalid"},
    )
    assert response.status_code == 400


def check_admin_rejects_missing_key(client: httpx.Client) -> None:
    response = client.get(f"{API_URL}/api/v1/admin/stripe-events")
    assert response.status_code == 401


def check_admin_accepts_key(client: httpx.Client) -> None:
    response = client.get(
        f"{API_URL}/api/v1/admin/stripe-events",
        headers={"X-Admin-Key": ADMIN_KEY},
    )
    assert response.status_code == 200


def check_frontend_homepage(client: httpx.Client) -> None:
    response = client.get(FRONTEND_URL)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def check_frontend_pricing(client: httpx.Client) -> None:
    response = client.get(f"{FRONTEND_URL}/pricing")
    assert response.status_code == 200


def check_frontend_x_frame_options(client: httpx.Client) -> None:
    response = client.get(FRONTEND_URL)
    assert response.headers["x-frame-options"] == "DENY"


def check_frontend_x_content_type_options(client: httpx.Client) -> None:
    response = client.get(FRONTEND_URL)
    assert response.headers["x-content-type-options"] == "nosniff"


def check_api_ssl(client: httpx.Client) -> None:
    response = client.get(f"{API_URL}/health")
    assert response.status_code == 200


def check_frontend_ssl(client: httpx.Client) -> None:
    response = client.get(FRONTEND_URL)
    assert response.status_code == 200


def main() -> int:
    missing = _require_env()
    if missing:
        print(f"FAIL missing environment variables: {', '.join(missing)}")
        return 1

    checks: list[tuple[str, Callable[[httpx.Client], None]]] = [
        ("API health endpoint returns 200", check_api_health),
        ("API DB health endpoint returns db=ok", check_api_db_health),
        ("API /docs returns 404", check_docs_disabled),
        ("API /openapi.json returns 404", check_openapi_disabled),
        ("Unauthenticated /me returns 401", check_auth_required),
        ("CORS header present from frontend URL", check_cors_header),
        ("Webhook rejects invalid signature", check_webhook_rejects_invalid_signature),
        ("Admin endpoint rejects missing key", check_admin_rejects_missing_key),
        ("Admin endpoint accepts correct key", check_admin_accepts_key),
        ("Frontend homepage returns 200", check_frontend_homepage),
        ("Frontend /pricing returns 200", check_frontend_pricing),
        ("Frontend has X-Frame-Options: DENY", check_frontend_x_frame_options),
        (
            "Frontend has X-Content-Type-Options: nosniff",
            check_frontend_x_content_type_options,
        ),
        ("SSL certificate valid on API domain", check_api_ssl),
        ("SSL certificate valid on frontend domain", check_frontend_ssl),
    ]

    with httpx.Client(timeout=30) as client:
        passed = sum(1 for name, fn in checks if _check(name, fn, client))

    failed = len(checks) - passed
    if failed:
        print(f"✗ {failed} checks failed. Fix the above before launching.")
        return 1

    print(f"✓ All {len(checks)} checks passed. Ready to launch.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
