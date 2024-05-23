import asyncio
import logging
import sys
from dotenv import load_dotenv

load_dotenv()

from tg2vk.config import Config  # NoPEP8
import tg2vk.bot  # NoPEP8

if __name__ == "__main__":
    loglevel = logging.INFO
    config = Config()
    if config.DEBUG:
        loglevel = logging.DEBUG

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(tg2vk.bot.start_polling(config))
