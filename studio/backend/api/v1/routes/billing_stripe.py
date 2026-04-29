from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_active_user, get_db
from backend.core import stripe_client
from backend.core.config import settings
from backend.core.logging import get_logger
from backend.core.webhook_processor import WebhookProcessor
from backend.db.models import User
from backend.db.session import SyncSessionLocal

router = APIRouter(prefix="/billing")
logger = get_logger(__name__)


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool | str]:
    del db
    body = await request.body()
    signature = request.headers.get("Stripe-Signature", "")

    try:
        event = stripe_client.construct_webhook_event(
            payload=body,
            sig_header=signature,
            secret=settings.stripe_webhook_secret,
        )
    except stripe_client.StripeSignatureVerificationError as exc:
        logger.warning("Invalid Stripe signature: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid signature") from exc
    except stripe_client.StripeWebhookPayloadError as exc:
        logger.warning("Invalid Stripe webhook payload: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid payload") from exc

    def run_processor() -> str:
        with SyncSessionLocal() as sync_db:
            processor = WebhookProcessor(sync_db)
            return processor.process(dict(event))

    result = await asyncio.to_thread(run_processor)

    if result == "failed":
        logger.error("Webhook processing failed for event %s", event["id"])

    return {"received": True, "status": result}


@router.get("/payment-status")
async def get_payment_status(
    current_user: User = Depends(get_current_active_user),
) -> dict[str, bool | str | None]:
    subscription_status = current_user.subscription_status
    return {
        "subscription_status": subscription_status,
        "is_past_due": subscription_status == "past_due",
        "is_paused": subscription_status == "paused",
        "tier": current_user.tier.value
        if hasattr(current_user.tier, "value")
        else str(current_user.tier),
        "action_required": subscription_status in ("past_due", "paused"),
    }


@router.post("/retry-payment", response_model=None)
async def retry_payment(
    current_user: User = Depends(get_current_active_user),
):
    if current_user.stripe_subscription_id is None:
        return JSONResponse(
            status_code=400,
            content={"error": "No active subscription"},
        )

    if current_user.subscription_status not in ("past_due", "unpaid"):
        return JSONResponse(
            status_code=400,
            content={"error": "No payment retry needed"},
        )

    invoices = await asyncio.to_thread(
        stripe_client.list_open_invoices,
        current_user.stripe_subscription_id,
    )
    invoice_items = getattr(invoices, "data", None)
    if invoice_items is None and isinstance(invoices, dict):
        invoice_items = invoices.get("data")
    invoice_items = invoice_items or []

    if not invoice_items:
        return JSONResponse(
            status_code=400,
            content={"error": "No open invoice found"},
        )

    invoice = invoice_items[0]
    invoice_id = getattr(invoice, "id", None)
    if invoice_id is None and isinstance(invoice, dict):
        invoice_id = invoice.get("id")
    if not invoice_id:
        return JSONResponse(
            status_code=400,
            content={"error": "Open invoice has no ID"},
        )

    try:
        await asyncio.to_thread(stripe_client.pay_invoice, str(invoice_id))
    except stripe_client.StripeCardError as exc:
        return JSONResponse(
            status_code=402,
            content={
                "error": "Payment method declined",
                "detail": str(exc.user_message),
            },
        )

    return {"retry_initiated": True, "invoice_id": str(invoice_id)}


@router.post("/portal", response_model=None)
async def create_customer_portal(
    current_user: User = Depends(get_current_active_user),
):
    if current_user.stripe_customer_id is None:
        return JSONResponse(
            status_code=400,
            content={"error": "No Stripe customer found"},
        )

    session = await asyncio.to_thread(
        stripe_client.create_billing_portal_session,
        customer_id=current_user.stripe_customer_id,
        return_url=str(settings.frontend_url) if settings.frontend_url else None,
    )
    portal_url = getattr(session, "url", None)
    if portal_url is None and isinstance(session, dict):
        portal_url = session.get("url")

    return {"portal_url": str(portal_url)}


# ---------------------------------------------------------------------------
# Checkout
# ---------------------------------------------------------------------------

class _CheckoutRequest(BaseModel):
    price_id: str
    success_url: str
    cancel_url: str


@router.post("/checkout")
async def create_checkout(
    body: _CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, str]:
    del db
    customer = await asyncio.to_thread(
        stripe_client.get_or_create_customer,
        current_user,
    )
    customer_id = getattr(customer, "id", None)
    if customer_id is None and isinstance(customer, dict):
        customer_id = customer.get("id")

    session = await asyncio.to_thread(
        stripe_client.create_checkout_session,
        customer=str(customer_id),
        line_items=[{"price": body.price_id, "quantity": 1}],
        mode="subscription",
        success_url=body.success_url,
        cancel_url=body.cancel_url,
    )
    session_url = getattr(session, "url", None)
    if session_url is None and isinstance(session, dict):
        session_url = session.get("url")

    return {"checkout_url": str(session_url)}


# ---------------------------------------------------------------------------
# Subscription detail
# ---------------------------------------------------------------------------

@router.get("/subscription")
async def get_subscription(
    current_user: User = Depends(get_current_active_user),
) -> dict[str, str | bool | int | None]:
    if current_user.stripe_subscription_id is None:
        return {"status": "none"}

    sub = await asyncio.to_thread(
        stripe_client.retrieve_subscription,
        current_user.stripe_subscription_id,
    )
    return {
        "status": (
            getattr(sub, "status", None)
            or (sub.get("status") if isinstance(sub, dict) else None)
        ),
        "current_period_end": (
            getattr(sub, "current_period_end", None)
            or (sub.get("current_period_end") if isinstance(sub, dict) else None)
        ),
        "cancel_at_period_end": (
            getattr(sub, "cancel_at_period_end", None)
            or (sub.get("cancel_at_period_end") if isinstance(sub, dict) else None)
        ),
    }
