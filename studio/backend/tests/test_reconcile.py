from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import Mock

from backend.workers import reconcile


class ScalarResult:
    def __init__(self, items):
        self._items = items

    def all(self):
        return list(self._items)


class QueryResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return ScalarResult(self._items)


class FakeSession:
    def __init__(self, subscribed=None, inconsistent=None):
        self.subscribed = subscribed or []
        self.inconsistent = inconsistent or []
        self.execute_count = 0
        self.added = []
        self.commit_count = 0
        self.rollback_count = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, statement):
        self.execute_count += 1
        if self.execute_count == 1:
            return QueryResult(self.subscribed)
        return QueryResult(self.inconsistent)

    def add(self, instance):
        self.added.append(instance)

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1


def make_user(**overrides):
    data = {
        "id": uuid.uuid4(),
        "tier": "pro",
        "credits_remaining": 20,
        "stripe_subscription_id": "sub_123",
        "subscription_status": "active",
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def run_with_session(monkeypatch, session):
    monkeypatch.setattr(reconcile, "SyncSessionLocal", lambda: session)
    return reconcile.reconcile_subscriptions()


def test_reconcile_updates_stale_status(monkeypatch):
    user = make_user(subscription_status="active")
    session = FakeSession(subscribed=[user])
    monkeypatch.setattr(
        reconcile.stripe_client,
        "retrieve_subscription",
        Mock(return_value={"status": "past_due", "metadata": {"tier": "pro"}}),
    )

    result = run_with_session(monkeypatch, session)

    assert user.subscription_status == "past_due"
    assert session.commit_count == 1
    assert result["reconciled_status"] == 1


def test_reconcile_downgrades_cancelled_subscription(monkeypatch):
    user = make_user(tier="pro", subscription_status="active")
    session = FakeSession(subscribed=[user])
    monkeypatch.setattr(
        reconcile.stripe_client,
        "retrieve_subscription",
        Mock(return_value={"status": "canceled", "metadata": {"tier": "pro"}}),
    )

    result = run_with_session(monkeypatch, session)

    assert user.tier == "free"
    assert user.stripe_subscription_id is None
    assert result["reconciled_tier"] == 1


def test_reconcile_skips_already_consistent_user(monkeypatch):
    user = make_user(tier="pro", subscription_status="active")
    session = FakeSession(subscribed=[user])
    monkeypatch.setattr(
        reconcile.stripe_client,
        "retrieve_subscription",
        Mock(return_value={"status": "active", "metadata": {"tier": "pro"}}),
    )

    result = run_with_session(monkeypatch, session)

    assert user.tier == "pro"
    assert not session.added
    assert result["reconciled_status"] == 0
    assert result["reconciled_tier"] == 0


def test_reconcile_continues_after_stripe_error(monkeypatch):
    first_user = make_user(stripe_subscription_id="sub_bad")
    second_user = make_user(stripe_subscription_id="sub_good", subscription_status="past_due")
    session = FakeSession(subscribed=[first_user, second_user])
    retrieve = Mock(
        side_effect=[
            RuntimeError("stripe unavailable"),
            {"status": "active", "metadata": {"tier": "pro"}},
        ]
    )
    monkeypatch.setattr(reconcile.stripe_client, "retrieve_subscription", retrieve)

    result = run_with_session(monkeypatch, session)

    assert result["errors"] == 1
    assert second_user.subscription_status == "active"
    assert result["reconciled_status"] == 1


def test_reconcile_flags_missing_subscription_id(monkeypatch, caplog):
    user = make_user(stripe_subscription_id=None, tier="pro")
    session = FakeSession(subscribed=[], inconsistent=[user])
    monkeypatch.setattr(
        reconcile.stripe_client,
        "retrieve_subscription",
        Mock(return_value={"status": "active", "metadata": {"tier": "pro"}}),
    )

    result = run_with_session(monkeypatch, session)

    assert result["inconsistencies_flagged"] == 1
    assert user.tier == "pro"
    assert "no subscription ID" in caplog.text


def test_reconcile_returns_correct_counts(monkeypatch):
    status_user = make_user(subscription_status="past_due", tier="pro")
    tier_user = make_user(stripe_subscription_id="sub_tier", tier="pro")
    error_user = make_user(stripe_subscription_id="sub_error")
    session = FakeSession(subscribed=[status_user, tier_user, error_user])
    retrieve = Mock(
        side_effect=[
            {"status": "active", "metadata": {"tier": "pro"}},
            {"status": "active", "metadata": {"tier": "agency"}},
            RuntimeError("stripe down"),
        ]
    )
    monkeypatch.setattr(reconcile.stripe_client, "retrieve_subscription", retrieve)

    result = run_with_session(monkeypatch, session)

    assert result == {
        "users_checked": 3,
        "reconciled_status": 1,
        "reconciled_tier": 1,
        "inconsistencies_flagged": 0,
        "errors": 1,
    }
