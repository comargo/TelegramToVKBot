from dataclasses import dataclass
from os import getenv


@dataclass(frozen=True)
class Config:
    TG_BOT_TOKEN: str = getenv('TG_BOT_TOKEN')
    DB_URL: str = getenv('DB_URL')
    DEBUG: bool = getenv('DEBUG', 'False').casefold() in ('true', 't', 'y', '1')
