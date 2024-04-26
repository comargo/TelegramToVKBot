from os import getenv

TG_BOT_TOKEN = getenv('TG_BOT_TOKEN')
DB_URL = getenv('DB_URL')


DEBUG = getenv('DEBUG', 'False').casefold() in ('true', 't', 'y', '1')
