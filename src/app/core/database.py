from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)

from sqlalchemy import select

from app.models.base import Base
from app.models.package import PackageType
from app.config.settings import get_settings
from app.core.logging import get_logger

import asyncio

logger = get_logger(__name__)
settings = get_settings()

DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=300
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session

async def create_all_tables():
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(sync_conn, checkfirst=True)
        )
    logger.info("All tables created successfully")

async def seed_package_types():
    async with SessionLocal() as session:
        result = await session.execute(select(PackageType.name))
        existing_names = {row for row in result.scalars().all()}
        types_to_add = []
        for name, description in [
            ("clothes", "Одежда"),
            ("electronics", "Электроника"),
            ("other", "Разное"),
        ]:
            if name not in existing_names:
                types_to_add.append(PackageType(name=name, description=description))
        if types_to_add:
            session.add_all(types_to_add)
            await session.commit()
            logger.info("Package types seeded successfully")
        else:
            logger.debug("Package types already exist, skipping seed")

async def init_db():
    await create_all_tables()
    await seed_package_types()

if __name__ == "__main__":
    asyncio.run(init_db())