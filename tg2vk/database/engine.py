from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from tg2vk import config
from tg2vk.database.model import Base

engine = create_async_engine(config.DB_URL, echo=config.DEBUG)

session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
