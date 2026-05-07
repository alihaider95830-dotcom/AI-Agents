import asyncio

from sqlalchemy import select

from backend.db.base import Base, engine
from backend.db.models import User, UserTier, Report, ReportStatus, UsageLog, UserSettings
from backend.db.session import AsyncSessionLocal


async def seed() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Check if seed data already exists
        result = await session.execute(
            select(User).where(User.email == "admin@studio.local")
        )
        if result.scalar_one_or_none() is not None:
            print("Seed data already exists, skipping...")
            return

        # Create admin user
        admin_user = User(
            email="admin@studio.local",
            supabase_id="seed-admin-user",
            tier=UserTier.AGENCY,
            credits_remaining=100,
        )
        session.add(admin_user)
        await session.flush()

        # Create admin settings
        admin_settings = UserSettings(user_id=admin_user.id)
        session.add(admin_settings)

        # Create test PRO user
        pro_user = User(
            email="pro@studio.local",
            supabase_id="seed-pro-user",
            tier=UserTier.PRO,
            credits_remaining=20,
        )
        session.add(pro_user)
        await session.flush()

        pro_settings = UserSettings(user_id=pro_user.id)
        session.add(pro_settings)

        # Create test FREE user
        free_user = User(
            email="test@studio.local",
            supabase_id="seed-test-user",
            tier=UserTier.FREE,
            credits_remaining=2,
        )
        session.add(free_user)
        await session.flush()

        free_settings = UserSettings(user_id=free_user.id)
        session.add(free_settings)

        # Create sample reports in different statuses
        completed_report = Report(
            user_id=pro_user.id,
            title="AI Market Analysis 2024",
            topic="Artificial Intelligence market trends",
            report_type="market_research",
            status=ReportStatus.DONE,
            content_md="# AI Market Analysis\n\n## Executive Summary\nThis is a sample completed report.",
            word_count=1250,
        )
        session.add(completed_report)
        await session.flush()

        # Add usage log for completed report
        usage_log = UsageLog(
            user_id=pro_user.id,
            report_id=completed_report.id,
            action="report_created",
            delta=-1,
        )
        session.add(usage_log)

        # Create a pending report
        pending_report = Report(
            user_id=free_user.id,
            title="SaaS Industry Report",
            topic="SaaS business models and trends",
            report_type="industry_analysis",
            status=ReportStatus.PENDING,
        )
        session.add(pending_report)
        await session.flush()

        # Create a running report
        running_report = Report(
            user_id=admin_user.id,
            title="Blockchain Technology Deep Dive",
            topic="Blockchain applications and adoption",
            report_type="technology_analysis",
            status=ReportStatus.RUNNING,
        )
        session.add(running_report)
        await session.flush()

        # Create a failed report
        failed_report = Report(
            user_id=pro_user.id,
            title="Quantum Computing Report",
            topic="Quantum computing advancements",
            report_type="technology_analysis",
            status=ReportStatus.FAILED,
        )
        session.add(failed_report)

        await session.commit()

    print("Seed complete - created 3 users, 4 sample reports, and settings")


if __name__ == "__main__":
    asyncio.run(seed())
