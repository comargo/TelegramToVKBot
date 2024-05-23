from functools import partial
from typing import Callable

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.client.session.middlewares.request_logging import RequestLogging
from aiogram.methods import GetUpdates
from sqlalchemy.ext.asyncio import AsyncSession

from tg2vk import channel, private
from tg2vk.config import Config
from tg2vk.database import engine, ops
from tg2vk.middlewares import DataBaseSession


async def on_startup(session_pool: Callable[[], AsyncSession]):
    async with session_pool() as session:
        if isinstance(session, AsyncSession):
            await engine.create_db(session)


def init_dispatcher(config: Config):
    dp = Dispatcher()
    dp.include_routers(channel.router, private.router)
    dp.session_maker = engine.get_session_maker(config)
    dp.update.middleware(DataBaseSession(session_pool=dp.session_maker))
    dp.startup.register(partial(on_startup, session_pool=dp.session_maker))
    return dp


async def start_polling(config: Config) -> None:
    bot = Bot(token=config.TG_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    bot.session.middleware(RequestLogging(ignore_methods=[GetUpdates]))
    await bot.delete_webhook(drop_pending_updates=True)
    dp = init_dispatcher(config)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
