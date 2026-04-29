from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.credits import TIER_LIMITS
from backend.core.logging import get_logger
from backend.core.redis_client import get_sync_redis
from backend.db.models import StripeEvent, UsageLog, User, UserTier

PROCESSED_STATUS = "processed"
FAILED_STATUS = "failed"
SKIPPED_STATUS = "skipped"
AGENCY_CREDIT_BALANCE = 9999


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _get_value(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _tier_value(user: User) -> str:
    tier = getattr(user, "tier", UserTier.FREE.value)
    return tier.value if hasattr(tier, "value") else str(tier)


def _assign_tier(user: User, tier: str) -> None:
    current_tier = getattr(user, "tier", None)
    if hasattr(current_tier, "value"):
        user.tier = UserTier(tier)
    else:
        user.tier = tier


def _monthly_credits_for_tier(tier: str) -> int:
    if tier == UserTier.AGENCY.value:
        return AGENCY_CREDIT_BALANCE
    monthly_reports = TIER_LIMITS[tier]["monthly_reports"]
    return int(monthly_reports or 0)


class WebhookProcessor:
    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger(__name__)
        self.redis = get_sync_redis()

    def is_already_processed(self, event_id: str) -> bool:
        event = self.db.get(StripeEvent, event_id)
        return event is not None and event.status == PROCESSED_STATUS

    def record_event(self, event_id: str, event_type: str, raw_payload: str) -> None:
        self._record_status(
            event_id=event_id,
            event_type=event_type,
            raw_payload=raw_payload,
            status=PROCESSED_STATUS,
            processed_at=_now(),
            error_message=None,
        )

    def record_failure(
        self,
        event_id: str,
        event_type: str,
        raw_payload: str,
        error: str,
    ) -> None:
        self._record_status(
            event_id=event_id,
            event_type=event_type,
            raw_payload=raw_payload,
            status=FAILED_STATUS,
            processed_at=None,
            error_message=error,
        )
        self.db.commit()

    def process(self, event: dict[str, Any]) -> str:
        event_id = str(event["id"])
        event_type = str(event["type"])
        raw_payload = json.dumps(event, default=str)

        if self.is_already_processed(event_id):
            self.logger.info("Skipping duplicate event %s", event_id)
            return SKIPPED_STATUS

        handlers: dict[str, Callable[[dict[str, Any]], None]] = {
            "checkout.session.completed": self._handle_checkout_completed,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "invoice.payment_failed": self._handle_payment_failed,
            "invoice.payment_succeeded": self._handle_payment_succeeded,
            "customer.subscription.paused": self._handle_subscription_paused,
        }

        handler = handlers.get(event_type)
        if handler is None:
            self.logger.debug("Skipping unknown Stripe event type %s", event_type)
            self._record_status(
                event_id=event_id,
                event_type=event_type,
                raw_payload=raw_payload,
                status=SKIPPED_STATUS,
                processed_at=_now(),
                error_message=None,
            )
            self.db.commit()
            return SKIPPED_STATUS

        try:
            handler(event)
            self.record_event(event_id, event_type, raw_payload)
            self.db.commit()
            return PROCESSED_STATUS
        except Exception as exc:
            self.db.rollback()
            self.record_failure(event_id, event_type, raw_payload, str(exc))
            self.logger.exception("Stripe webhook processing failed for %s", event_id)
            return FAILED_STATUS

    def _record_status(
        self,
        *,
        event_id: str,
        event_type: str,
        raw_payload: str,
        status: str,
        processed_at: datetime | None,
        error_message: str | None,
    ) -> None:
        event = self.db.get(StripeEvent, event_id)
        if event is None:
            event = StripeEvent(
                id=event_id,
                type=event_type,
                processed_at=processed_at,
                status=status,
                error_message=error_message,
                raw_payload=raw_payload,
            )
            self.db.add(event)
            return

        event.type = event_type
        event.processed_at = processed_at
        event.status = status
        event.error_message = error_message
        event.raw_payload = raw_payload
        self.db.add(event)

    def _get_user_by_customer_id(self, customer_id: str) -> User | None:
        result = self.db.execute(
            select(User).where(User.stripe_customer_id == customer_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            self.logger.warning("No user found for customer %s", customer_id)
        return user

    def _get_user_by_subscription_id(self, subscription_id: str) -> User | None:
        result = self.db.execute(
            select(User).where(User.stripe_subscription_id == subscription_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            self.logger.warning("No user found for subscription %s", subscription_id)
        return user

    def _apply_tier_upgrade(self, user: User, tier: str) -> None:
        if tier not in TIER_LIMITS:
            raise ValueError(f"Invalid tier {tier}")

        _assign_tier(user, tier)
        user.credits_remaining = _monthly_credits_for_tier(tier)
        self.db.add(user)
        self.db.add(
            UsageLog(
                user_id=user.id,
                report_id=None,
                action="tier_upgraded",
                delta=0,
            )
        )
        self.logger.info("User %s upgraded to %s", user.id, tier)

    def _apply_tier_downgrade(self, user: User) -> None:
        _assign_tier(user, UserTier.FREE.value)
        user.credits_remaining = _monthly_credits_for_tier(UserTier.FREE.value)
        user.stripe_subscription_id = None
        user.subscription_status = "canceled"
        self.db.add(user)
        self.db.add(
            UsageLog(
                user_id=user.id,
                report_id=None,
                action="tier_downgraded",
                delta=0,
            )
        )
        self.logger.info("User %s downgraded to free", user.id)

    def _publish_tier_change(self, user_id: str, new_tier: str) -> None:
        try:
            self.redis.publish(
                "tier_changes",
                json.dumps(
                    {
                        "user_id": str(user_id),
                        "tier": new_tier,
                        "timestamp": _now().isoformat(),
                    }
                ),
            )
        except Exception:
            self.logger.exception("Could not publish tier change for user %s", user_id)

    def _publish_payment_event(self, user_id: str, event_name: str) -> None:
        try:
            self.redis.publish(
                "payment_events",
                json.dumps(
                    {
                        "user_id": str(user_id),
                        "event": event_name,
                        "timestamp": _now().isoformat(),
                    }
                ),
            )
        except Exception:
            self.logger.exception("Could not publish payment event for user %s", user_id)

    def _handle_checkout_completed(self, event: dict[str, Any]) -> None:
        obj = event["data"]["object"]
        metadata = _get_value(obj, "metadata", {}) or {}
        user_id = metadata["user_id"]
        tier = metadata["tier"]
        subscription_id = _get_value(obj, "subscription")
        customer_id = _get_value(obj, "customer")

        lookup_user_id: Any = user_id
        try:
            lookup_user_id = uuid.UUID(str(user_id))
        except ValueError:
            pass

        user = self.db.get(User, lookup_user_id)
        if user is None:
            raise ValueError(f"User {user_id} not found for checkout event")

        user.stripe_subscription_id = subscription_id
        if customer_id:
            user.stripe_customer_id = customer_id
        user.subscription_status = "active"
        self._apply_tier_upgrade(user, tier)
        self._publish_tier_change(str(user.id), tier)

    def _handle_subscription_updated(self, event: dict[str, Any]) -> None:
        sub = event["data"]["object"]
        subscription_id = _get_value(sub, "id")
        user = self._get_user_by_subscription_id(subscription_id)
        if user is None:
            return

        status = _get_value(sub, "status")
        user.subscription_status = status
        self.db.add(user)

        if status == "active":
            metadata = _get_value(sub, "metadata", {}) or {}
            new_tier = metadata.get("tier")
            if new_tier and new_tier != _tier_value(user):
                self._apply_tier_upgrade(user, new_tier)
                self._publish_tier_change(str(user.id), new_tier)

        if status in ("canceled", "unpaid"):
            self._apply_tier_downgrade(user)
            self._publish_tier_change(str(user.id), UserTier.FREE.value)

    def _handle_subscription_deleted(self, event: dict[str, Any]) -> None:
        sub = event["data"]["object"]
        user = self._get_user_by_subscription_id(_get_value(sub, "id"))
        if user is None:
            return
        self._apply_tier_downgrade(user)
        self._publish_tier_change(str(user.id), UserTier.FREE.value)

    def _handle_payment_failed(self, event: dict[str, Any]) -> None:
        invoice = event["data"]["object"]
        user = self._get_user_by_customer_id(_get_value(invoice, "customer"))
        if user is None:
            return

        user.subscription_status = "past_due"
        self.db.add(user)
        self.db.add(
            UsageLog(
                user_id=user.id,
                report_id=None,
                action="payment_failed",
                delta=0,
            )
        )
        self.logger.info("Payment failed for user %s", user.id)
        self._publish_payment_event(str(user.id), "payment_failed")

    def _handle_payment_succeeded(self, event: dict[str, Any]) -> None:
        invoice = event["data"]["object"]
        if _get_value(invoice, "billing_reason") != "subscription_cycle":
            return

        user = self._get_user_by_customer_id(_get_value(invoice, "customer"))
        if user is None:
            return

        tier = _tier_value(user)
        user.subscription_status = "active"
        user.credits_remaining = _monthly_credits_for_tier(tier)
        self.db.add(user)
        self.db.add(
            UsageLog(
                user_id=user.id,
                report_id=None,
                action="credits_renewed",
                delta=user.credits_remaining,
            )
        )
        self.logger.info("Credits renewed for user %s on tier %s", user.id, tier)

    def _handle_subscription_paused(self, event: dict[str, Any]) -> None:
        sub = event["data"]["object"]
        user = self._get_user_by_subscription_id(_get_value(sub, "id"))
        if user is None:
            return

        user.subscription_status = "paused"
        _assign_tier(user, UserTier.FREE.value)
        user.credits_remaining = _monthly_credits_for_tier(UserTier.FREE.value)
        self.db.add(user)
        self.db.add(
            UsageLog(
                user_id=user.id,
                report_id=None,
                action="subscription_paused",
                delta=0,
            )
        )
        self._publish_tier_change(str(user.id), UserTier.FREE.value)
