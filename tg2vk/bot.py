from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from tg2vk import config, channel, private
from tg2vk.database.engine import session_maker, create_db
from tg2vk.middlewares import DataBaseSession


async def on_startup(bot: Bot):
    await create_db()


dp = Dispatcher()
dp.include_routers(channel.router, private.router)
dp.update.middleware(DataBaseSession(session_pool=session_maker))
dp.startup.register(on_startup)


async def start_polling() -> None:
    bot = Bot(token=config.TG_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
