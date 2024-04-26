from typing import Optional

from aiogram import types
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from tg2vk.database import model


async def get_user(session: AsyncSession, user_id: int):
    model_user: Optional[model.User] = await session.scalar(
        select(model.User).where(model.User.tg_id == user_id)
    )
    return model_user


async def get_or_add_user(session: AsyncSession, user: types.User) -> model.User:
    model_user = await get_user(session, user.id)
    if model_user is None:
        model_user = model.User(tg_id=user.id, lang=user.language_code)
        session.add(model_user)
        await session.commit()
    return model_user


async def get_channel(session: AsyncSession, channel_id: int):
    model_channel: Optional[model.Channel] = await session.scalar(
        select(model.Channel).where(model.Channel.channel_id == channel_id)
    )
    return model_channel


async def get_or_add_channel(session: AsyncSession, channel: types.Chat):
    model_channel = await get_channel(session, channel.id)
    if model_channel is None:
        model_channel = model.Channel(channel_id=channel.id,
                                      title=channel.title,
                                      invite_link=channel.invite_link)
        session.add(model_channel)
        await session.commit()
    return model_channel


async def add_repost_info(session: AsyncSession, user: model.User, channel: model.Channel):
    repost_info = model.RepostInfo(user=user, channel=channel)
    session.add(repost_info)
    await session.commit()
    return repost_info


async def delete_channel(session: AsyncSession, channel_id: int):
    delete_channel_reposts = delete(model.Channel).where(model.Channel.channel_id == channel_id)
    await session.execute(delete_channel_reposts)
    await session.commit()
