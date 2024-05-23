from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from tg2vk.config import Config
from tg2vk.database.model import Base
from tg2vk.database.ops import AsyncSessionOps


def get_session_maker(config: Config):
    engine = create_async_engine(config.DB_URL, echo=config.DEBUG)
    return async_sessionmaker(bind=engine, class_=AsyncSessionOps, expire_on_commit=False)


async def create_db(session: AsyncSession):
    async with session.begin():
        await (await session.connection()).run_sync(Base.metadata.create_all)


async def drop_db(session: AsyncSession):
    async with session.begin():
        await (await session.connection()).run_sync(Base.metadata.drop_all)
