from typing import List

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    def __repr__(self) -> str:
        columns = ",".join(
            (f"{k}={v!r}" for k, v in self.__dict__.items() if not k.startswith("_")))
        return f"{type(self).__name__}({columns})"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(unique=True)
    lang: Mapped[str] = mapped_column(nullable=True)
    reposts: Mapped[List["RepostInfo"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(unique=True)
    title: Mapped[str] = mapped_column(String(256))
    invite_link: Mapped[str] = mapped_column(String(256))

    reposts: Mapped[List["RepostInfo"]] = relationship(
        back_populates="channel", cascade="all, delete-orphan"
    )


class RepostInfo(Base):
    __tablename__ = "reposts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    community_id: Mapped[int] = mapped_column(nullable=True)
    community_token: Mapped[str] = mapped_column(String(256), nullable=True)

    channel_id: Mapped[int] = mapped_column(ForeignKey(Channel.id))
    channel: Mapped["Channel"] = relationship(back_populates="reposts")
    user_id: Mapped[int] = mapped_column(ForeignKey(User.id))
    user: Mapped["User"] = relationship(back_populates="reposts")
