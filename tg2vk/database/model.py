from typing import List, Callable, Protocol

import aiogram
from aiogram.utils.formatting import TextLink
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship



class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    def __repr__(self) -> str:
        columns = ",".join(
            (f"{c.name}={getattr(self, c.name)!r}" for c in self.__table__.columns))
        return f"{type(self).__name__}({columns})"

    def __lt__(self, other):
        return  self.id < other.id


class User(Base):
    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(unique=True)
    lang: Mapped[str] = mapped_column(nullable=True)
    reposts: Mapped[List["RepostInfo"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Channel(Base):
    __tablename__ = "channels"

    channel_id: Mapped[int] = mapped_column(unique=True)
    title: Mapped[str] = mapped_column(String(256))

    reposts: Mapped[List["RepostInfo"]] = relationship(
        back_populates="channel", cascade="all, delete-orphan"
    )

    @property
    def channel_link(self):
        chat = aiogram.types.Chat(id=self.channel_id, type=aiogram.enums.ChatType.CHANNEL)
        return TextLink(self.title, url=f"https://t.me/c/{chat.shifted_id}")


class RepostInfo(Base):
    __tablename__ = "reposts"

    community_id: Mapped[int] = mapped_column(nullable=True)
    community_token: Mapped[str] = mapped_column(String(256), nullable=True)
    community_name: Mapped[str] = mapped_column(String(256), nullable=True)

    channel_id: Mapped[int] = mapped_column(ForeignKey(Channel.id))
    channel: Mapped["Channel"] = relationship(back_populates="reposts")
    user_id: Mapped[int] = mapped_column(ForeignKey(User.id))
    user: Mapped["User"] = relationship(back_populates="reposts")

    @property
    def community_link(self):
        return TextLink(self.community_name, url=f"https://vk.com/club{self.community_id}")
