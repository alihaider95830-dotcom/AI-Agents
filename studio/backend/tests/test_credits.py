import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.core.credits import TIER_LIMITS, check_and_deduct, get_usage_summary, refund, refund_sync
from backend.core.exceptions import InsufficientCreditsError


class ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one(self):
        return self._value


def make_async_session(report_count: int) -> AsyncMock:
    db = AsyncMock(spec=AsyncSession)
    db.execute = AsyncMock(side_effect=[ScalarResult(make_user()), ScalarResult(report_count)])
    db.add = Mock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.rollback = AsyncMock()
    return db


def make_user(*, tier: str = "free", credits_remaining: int = 2):
    return SimpleNamespace(
        id=uuid.uuid4(),
        tier=tier,
        credits_remaining=credits_remaining,
    )


@pytest.mark.asyncio
async def test_check_deduct_success() -> None:
    user = make_user()
    db = make_async_session(report_count=0)
    db.execute = AsyncMock(side_effect=[ScalarResult(user), ScalarResult(0)])

    await check_and_deduct(user, db)

    assert user.credits_remaining == 1
    assert db.add.call_count == 2
    db.flush.assert_awaited_once()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_check_deduct_at_limit() -> None:
    user = make_user()
    db = make_async_session(report_count=TIER_LIMITS["free"]["monthly_reports"])
    db.execute = AsyncMock(
        side_effect=[ScalarResult(user), ScalarResult(TIER_LIMITS["free"]["monthly_reports"])]
    )

    with pytest.raises(
        InsufficientCreditsError,
        match="Monthly limit of 2 reports reached. Upgrade to generate more.",
    ):
        await check_and_deduct(user, db)

    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_check_deduct_agency_unlimited() -> None:
    user = make_user(tier="agency", credits_remaining=4)
    db = make_async_session(report_count=999)
    db.execute = AsyncMock(side_effect=[ScalarResult(user), ScalarResult(999)])

    await check_and_deduct(user, db)

    assert user.credits_remaining == 3
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_check_deduct_no_negative_credits() -> None:
    user = make_user(credits_remaining=0)
    db = make_async_session(report_count=0)
    db.execute = AsyncMock(side_effect=[ScalarResult(user), ScalarResult(0)])

    await check_and_deduct(user, db)

    assert user.credits_remaining == 0


@pytest.mark.asyncio
async def test_refund_async() -> None:
    user = make_user(credits_remaining=1)
    report_id = str(uuid.uuid4())
    db = make_async_session(report_count=0)

    await refund(user, db, report_id)

    usage_log = db.add.call_args_list[1].args[0]
    assert user.credits_remaining == 2
    assert usage_log.delta == 1
    assert str(usage_log.report_id) == report_id


def test_refund_sync() -> None:
    user = make_user(credits_remaining=1)
    report_id = str(uuid.uuid4())
    session = Mock(spec=Session)
    session.get.return_value = user
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()

    refund_sync(str(user.id), report_id, session)

    usage_log = session.add.call_args_list[1].args[0]
    assert user.credits_remaining == 2
    assert usage_log.delta == 1
    assert str(usage_log.report_id) == report_id
    session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_usage_summary_free_tier() -> None:
    user = make_user()
    db = make_async_session(report_count=1)
    now = datetime.now(timezone.utc)
    if now.month == 12:
        expected_reset = now.replace(year=now.year + 1, month=1, day=1)
    else:
        expected_reset = now.replace(month=now.month + 1, day=1)

    summary = await get_usage_summary(user, db)

    assert summary["monthly_limit"] == TIER_LIMITS["free"]["monthly_reports"]
    assert summary["resets_on"] == expected_reset.strftime("%Y-%m-%d")


@pytest.mark.asyncio
async def test_usage_summary_agency_unlimited() -> None:
    user = make_user(tier="agency")
    db = make_async_session(report_count=999)

    summary = await get_usage_summary(user, db)

    assert summary["monthly_limit"] is None
