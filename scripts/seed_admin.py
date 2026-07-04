import argparse
import asyncio
import hashlib
import logging
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from securesight.api.core.config import get_settings
from securesight.api.models.user import User

logger = logging.getLogger(__name__)


async def seed_admin(
    email: str = "admin@securesight.local",
    username: str = "admin",
    password: str | None = None,
    is_superuser: bool = True,
) -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    if password is None:
        password = secrets.token_urlsafe(16)
        logger.info("Generated admin password: %s", password)

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.email == email))
        existing = result.scalar_one_or_none()

        if existing:
            logger.info("Admin user already exists (email=%s, id=%s)", email, existing.id)
            return

        user = User(
            email=email,
            username=username,
            hashed_password=hashlib.sha256(password.encode()).hexdigest(),
            is_active=True,
            is_superuser=is_superuser,
        )
        session.add(user)
        await session.commit()
        logger.info("Created admin user (id=%s, email=%s)", user.id, user.email)

    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed admin user")
    parser.add_argument("--email", default="admin@securesight.local")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default=None)
    parser.add_argument("--no-superuser", action="store_false", dest="is_superuser")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    asyncio.run(seed_admin(**vars(args)))
