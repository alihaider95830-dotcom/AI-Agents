from __future__ import annotations

import json
import uuid
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from backend.core.webhook_processor import WebhookProcessor
from backend.db.models import StripeEvent, User


class QueryResult:
    def __init__(self, scalar=None):
        self._scalar = scalar

    def scalar_one_or_none(self):
        return self._scalar


class FakeSession:
    def __init__(self):
        self.users_by_id = {}
        self.users_by_customer = {}
        self.users_by_subscription = {}
        self.stripe_events = {}
        self.added = []
        self.committed = False
        self.rolled_back = False

    def get(self, model, key):
        if model is StripeEvent:
            return self.stripe_events.get(key)
        if model is User:
            return self.users_by_id.get(key) or self.users_by_id.get(str(key))
        return None

    def add(self, instance):
        self.added.append(instance)
        if isinstance(instance, StripeEvent):
            self.stripe_events[instance.id] = instance

    def execute(self, statement):
        compiled = str(statement)
        param_values = list(statement.compile().params.values())
        if "stripe_customer_id" in compiled:
            for value in param_values:
                if value in self.users_by_customer:
                    return QueryResult(self.users_by_customer[value])
        if "stripe_subscription_id" in compiled:
            for value in param_values:
                if value in self.users_by_subscription:
                    return QueryResult(self.users_by_subscription[value])
        return QueryResult(None)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


@pytest.fixture
def redis_mock():
    return Mock()


@pytest.fixture
def processor(redis_mock, monkeypatch):
    db = FakeSession()
    monkeypatch.setattr(
        "backend.core.webhook_processor.get_sync_redis",
        lambda: redis_mock,
    )
    return WebhookProcessor(db)


def make_user(**overrides):
    data = {
        "id": uuid.uuid4(),
        "tier": "free",
        "credits_remaining": 2,
        "stripe_customer_id": "cus_123",
        "stripe_subscription_id": "sub_123",
        "subscription_status": "active",
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def checkout_event(user_id, tier="pro"):
    return {
        "id": "evt_checkout",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"user_id": str(user_id), "tier": tier},
                "customer": "cus_123",
                "subscription": "sub_new",
            }
        },
    }


def subscription_event(status="active", tier="pro"):
    return {
        "id": "evt_sub",
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_123",
                "status": status,
                "metadata": {"tier": tier},
            }
        },
    }


def test_duplicate_event_is_skipped(processor):
    processor.is_already_processed = Mock(return_value=True)
    processor._handle_checkout_completed = Mock()

    result = processor.process(checkout_event(uuid.uuid4()))

    assert result == "skipped"
    processor._handle_checkout_completed.assert_not_called()


def test_new_event_is_processed(processor):
    user = make_user()
    processor.db.users_by_id[user.id] = user
    processor.is_already_processed = Mock(return_value=False)
    processor.record_event = Mock()

    result = processor.process(checkout_event(user.id))

    assert result == "processed"
    processor.record_event.assert_called_once()


def test_failed_handler_records_failure(processor):
    processor.is_already_processed = Mock(return_value=False)
    processor._handle_checkout_completed = Mock(side_effect=ValueError("User not found"))
    processor.record_failure = Mock()

    result = processor.process(checkout_event(uuid.uuid4()))

    assert result == "failed"
    assert processor.db.rolled_back is True
    processor.record_failure.assert_called_once()
    assert "User not found" in processor.record_failure.call_args.args[3]


def test_unknown_event_type_is_skipped(processor):
    processor._handle_checkout_completed = Mock()

    result = processor.process({"id": "evt_unknown", "type": "customer.created"})

    assert result == "skipped"
    processor._handle_checkout_completed.assert_not_called()


def test_checkout_completed_upgrades_user(processor):
    user = make_user(tier="free", credits_remaining=0)
    processor.db.users_by_id[user.id] = user

    processor._handle_checkout_completed(checkout_event(user.id, tier="pro"))

    assert user.tier == "pro"
    assert user.subscription_status == "active"
    assert user.stripe_subscription_id == "sub_new"
    assert user.credits_remaining == 20


def test_checkout_completed_user_not_found(processor):
    result = processor.process(checkout_event(uuid.uuid4()))

    assert result == "failed"


def test_checkout_completed_invalid_tier(processor):
    user = make_user()
    processor.db.users_by_id[user.id] = user

    with pytest.raises(ValueError):
        processor._handle_checkout_completed(checkout_event(user.id, tier="enterprise"))


def test_subscription_updated_active_same_tier(processor):
    user = make_user(tier="pro", subscription_status="past_due")
    processor.db.users_by_subscription[user.stripe_subscription_id] = user

    processor._handle_subscription_updated(subscription_event(status="active", tier="pro"))

    assert user.subscription_status == "active"
    assert user.tier == "pro"


def test_subscription_updated_active_new_tier(processor):
    user = make_user(tier="pro")
    processor.db.users_by_subscription[user.stripe_subscription_id] = user
    processor._apply_tier_upgrade = Mock()

    processor._handle_subscription_updated(subscription_event(status="active", tier="agency"))

    processor._apply_tier_upgrade.assert_called_once_with(user, "agency")


def test_subscription_updated_canceled(processor):
    user = make_user(tier="pro")
    processor.db.users_by_subscription[user.stripe_subscription_id] = user
    processor._apply_tier_downgrade = Mock(wraps=processor._apply_tier_downgrade)

    processor._handle_subscription_updated(subscription_event(status="canceled"))

    processor._apply_tier_downgrade.assert_called_once_with(user)
    assert user.tier == "free"


def test_subscription_updated_user_not_found(processor):
    result = processor.process(subscription_event(status="active", tier="pro"))

    assert result == "processed"
    assert not any(getattr(item, "action", None) == "tier_upgraded" for item in processor.db.added)


def test_subscription_deleted_downgrades_user(processor):
    user = make_user(tier="pro")
    processor.db.users_by_subscription[user.stripe_subscription_id] = user

    processor._handle_subscription_deleted(
        {
            "id": "evt_deleted",
            "type": "customer.subscription.deleted",
            "data": {"object": {"id": user.stripe_subscription_id}},
        }
    )

    assert user.tier == "free"
    assert user.subscription_status == "canceled"
    assert user.stripe_subscription_id is None


def test_payment_failed_sets_past_due(processor):
    user = make_user(tier="pro", subscription_status="active")
    processor.db.users_by_customer[user.stripe_customer_id] = user

    processor._handle_payment_failed(
        {
            "id": "evt_failed",
            "type": "invoice.payment_failed",
            "data": {"object": {"customer": user.stripe_customer_id}},
        }
    )

    assert user.subscription_status == "past_due"
    assert user.tier == "pro"


def test_payment_failed_publishes_redis_event(processor, redis_mock):
    user = make_user()
    processor.db.users_by_customer[user.stripe_customer_id] = user

    processor._handle_payment_failed(
        {
            "id": "evt_failed",
            "type": "invoice.payment_failed",
            "data": {"object": {"customer": user.stripe_customer_id}},
        }
    )

    redis_mock.publish.assert_called_once()
    assert redis_mock.publish.call_args.args[0] == "payment_events"


def test_payment_succeeded_renews_credits(processor):
    user = make_user(tier="pro", credits_remaining=0, subscription_status="past_due")
    processor.db.users_by_customer[user.stripe_customer_id] = user

    processor._handle_payment_succeeded(
        {
            "id": "evt_paid",
            "type": "invoice.payment_succeeded",
            "data": {
                "object": {
                    "customer": user.stripe_customer_id,
                    "billing_reason": "subscription_cycle",
                }
            },
        }
    )

    assert user.credits_remaining == 20
    assert user.subscription_status == "active"


def test_payment_succeeded_ignores_non_cycle(processor):
    user = make_user(tier="pro", credits_remaining=4)
    processor.db.users_by_customer[user.stripe_customer_id] = user

    processor._handle_payment_succeeded(
        {
            "id": "evt_paid",
            "type": "invoice.payment_succeeded",
            "data": {
                "object": {
                    "customer": user.stripe_customer_id,
                    "billing_reason": "manual",
                }
            },
        }
    )

    assert user.credits_remaining == 4


def test_payment_succeeded_agency_gets_9999_credits(processor):
    user = make_user(tier="agency", credits_remaining=0)
    processor.db.users_by_customer[user.stripe_customer_id] = user

    processor._handle_payment_succeeded(
        {
            "id": "evt_paid",
            "type": "invoice.payment_succeeded",
            "data": {
                "object": {
                    "customer": user.stripe_customer_id,
                    "billing_reason": "subscription_cycle",
                }
            },
        }
    )

    assert user.credits_remaining == 9999


def test_subscription_paused_sets_free_tier(processor):
    user = make_user(tier="pro")
    processor.db.users_by_subscription[user.stripe_subscription_id] = user

    processor._handle_subscription_paused(
        {
            "id": "evt_paused",
            "type": "customer.subscription.paused",
            "data": {"object": {"id": user.stripe_subscription_id}},
        }
    )

    assert user.tier == "free"
    assert user.subscription_status == "paused"


def test_publish_tier_change_on_upgrade(processor, redis_mock):
    user = make_user(tier="free")
    processor.db.users_by_id[user.id] = user

    processor._handle_checkout_completed(checkout_event(user.id, tier="pro"))

    assert redis_mock.publish.call_args.args[0] == "tier_changes"
    payload = json.loads(redis_mock.publish.call_args.args[1])
    assert payload["user_id"] == str(user.id)
    assert payload["tier"] == "pro"


def test_publish_does_not_raise_on_redis_error(processor, redis_mock):
    user = make_user(tier="free")
    processor.db.users_by_id[user.id] = user
    redis_mock.publish.side_effect = ConnectionError("redis down")

    result = processor.process(checkout_event(user.id, tier="pro"))

    assert result == "processed"
