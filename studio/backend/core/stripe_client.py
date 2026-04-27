from __future__ import annotations

from typing import Any

from backend.core.config import settings

try:
    import stripe as _stripe
except Exception:  # pragma: no cover - dependency is provided in deployed envs
    _stripe = None


class StripeUnavailableError(RuntimeError):
    pass


class StripeSignatureVerificationError(Exception):
    pass


class StripeCardError(Exception):
    def __init__(self, message: str, user_message: str | None = None) -> None:
        super().__init__(message)
        self.user_message = user_message or message


def _client():
    if _stripe is None:
        raise StripeUnavailableError("Stripe SDK is not installed")
    if settings.stripe_secret_key:
        _stripe.api_key = settings.stripe_secret_key
    return _stripe


def construct_webhook_event(payload: bytes, sig_header: str, secret: str | None) -> dict[str, Any]:
    stripe = _client()
    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=secret,
        )
    except stripe.error.SignatureVerificationError as exc:
        raise StripeSignatureVerificationError(str(exc)) from exc
    return dict(event)


def retrieve_subscription(subscription_id: str) -> Any:
    return _client().Subscription.retrieve(subscription_id)


def retrieve_event(event_id: str) -> dict[str, Any]:
    return dict(_client().Event.retrieve(event_id))


def list_open_invoices(subscription_id: str, limit: int = 1) -> Any:
    return _client().Invoice.list(
        subscription=subscription_id,
        status="open",
        limit=limit,
    )


def pay_invoice(invoice_id: str) -> Any:
    stripe = _client()
    try:
        return stripe.Invoice.pay(invoice_id)
    except stripe.error.CardError as exc:
        raise StripeCardError(str(exc), getattr(exc, "user_message", None)) from exc


def create_billing_portal_session(customer_id: str, return_url: str | None) -> Any:
    return _client().billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )


def create_checkout_session(**kwargs: Any) -> Any:
    return _client().checkout.Session.create(**kwargs)
