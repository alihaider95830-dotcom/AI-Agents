import asyncio

from sqlalchemy import select

from backend.db.base import Base, engine
from backend.db.models import User, UserTier
from backend.db.session import AsyncSessionLocal


async def seed() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.email == "test@studio.local")
        )
        user = result.scalar_one_or_none()

        if user is None:
            session.add(
                User(
                    email="test@studio.local",
                    supabase_id="seed-test-user",
                    tier=UserTier.PRO,
                    credits_remaining=20,
                )
            )
            await session.commit()

    print("Seed complete")


if __name__ == "__main__":
    asyncio.run(seed())
