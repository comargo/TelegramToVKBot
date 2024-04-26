import asyncio
import logging
import sys
from dotenv import load_dotenv

load_dotenv()

import tg2vk.bot  # NoPEP8
import tg2vk.config  # NoPEP8

if __name__ == "__main__":
    loglevel = logging.INFO
    if tg2vk.config.DEBUG:
        loglevel = logging.DEBUG

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(tg2vk.bot.start_polling())
