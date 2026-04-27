from __future__ import annotations

from typing import Any

from sqlalchemy import select

from backend.core import stripe_client
from backend.core.credits import TIER_LIMITS
from backend.core.logging import get_logger
from backend.db.models import UsageLog, User, UserTier
from backend.db.session import SyncSessionLocal
from backend.workers.celery_app import celery_app

AGENCY_CREDIT_BALANCE = 9999
logger = get_logger(__name__)


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


def _credits_for_tier(tier: str) -> int:
    if tier == UserTier.AGENCY.value:
        return AGENCY_CREDIT_BALANCE
    return int(TIER_LIMITS[tier]["monthly_reports"] or 0)


def _upgrade_user(user: User, tier: str) -> None:
    if tier not in TIER_LIMITS:
        raise ValueError(f"Invalid tier {tier}")
    _assign_tier(user, tier)
    user.credits_remaining = _credits_for_tier(tier)


def _downgrade_user(user: User) -> None:
    _assign_tier(user, UserTier.FREE.value)
    user.credits_remaining = _credits_for_tier(UserTier.FREE.value)
    user.stripe_subscription_id = None


@celery_app.task(name="reconcile_subscriptions")
def reconcile_subscriptions() -> dict[str, int]:
    users_checked = 0
    reconciled_status = 0
    reconciled_tier = 0
    inconsistencies_flagged = 0
    errors = 0

    with SyncSessionLocal() as db:
        subscribed_users = (
            db.execute(select(User).where(User.stripe_subscription_id.is_not(None)))
            .scalars()
            .all()
        )

        for user in subscribed_users:
            users_checked += 1
            try:
                old_status = user.subscription_status
                old_tier = _tier_value(user)
                subscription = stripe_client.retrieve_subscription(
                    user.stripe_subscription_id
                )
                stripe_status = _get_value(subscription, "status")
                changed = False

                if stripe_status != user.subscription_status:
                    user.subscription_status = stripe_status
                    reconciled_status += 1
                    changed = True
                    logger.info(
                        "Reconciled user %s: %s -> %s",
                        user.id,
                        old_status,
                        stripe_status,
                    )

                if stripe_status == "active":
                    metadata = _get_value(subscription, "metadata", {}) or {}
                    tier_from_stripe = metadata.get("tier", old_tier)
                    if tier_from_stripe != _tier_value(user):
                        _upgrade_user(user, tier_from_stripe)
                        db.add(
                            UsageLog(
                                user_id=user.id,
                                report_id=None,
                                action="tier_upgraded",
                                delta=0,
                            )
                        )
                        reconciled_tier += 1
                        changed = True
                        logger.info(
                            "Reconciled tier for user %s: %s -> %s",
                            user.id,
                            old_tier,
                            tier_from_stripe,
                        )

                if stripe_status in ("canceled", "unpaid", "incomplete_expired"):
                    if _tier_value(user) != UserTier.FREE.value:
                        _downgrade_user(user)
                        user.subscription_status = stripe_status
                        db.add(
                            UsageLog(
                                user_id=user.id,
                                report_id=None,
                                action="tier_downgraded",
                                delta=0,
                            )
                        )
                        reconciled_tier += 1
                        changed = True
                        logger.info(
                            "Reconciled tier for user %s: %s -> free",
                            user.id,
                            old_tier,
                        )

                if changed:
                    db.add(user)
                db.commit()
            except Exception:
                db.rollback()
                errors += 1
                logger.exception(
                    "Failed to reconcile subscription for user %s",
                    user.id,
                )

        inconsistent_users = (
            db.execute(
                select(User).where(
                    User.stripe_subscription_id.is_(None),
                    User.tier != UserTier.FREE,
                )
            )
            .scalars()
            .all()
        )

        for user in inconsistent_users:
            inconsistencies_flagged += 1
            logger.warning(
                "User %s has tier=%s but no subscription ID",
                user.id,
                _tier_value(user),
            )

    return {
        "users_checked": users_checked,
        "reconciled_status": reconciled_status,
        "reconciled_tier": reconciled_tier,
        "inconsistencies_flagged": inconsistencies_flagged,
        "errors": errors,
    }
