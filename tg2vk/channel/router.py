import logging
import typing

from aiogram import Router, types, Bot, F
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER
from aiogram.utils.markdown import hlink, hbold
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tg2vk.database import model
from tg2vk.database.ops import get_or_add_user, delete_channel, get_or_add_channel, \
    add_repost_info, get_channel

router = Router(name="channel")

logger = logging.getLogger(__name__)


def chat_link(chat: typing.Union[types.Chat, model.Channel]) -> str:
    if chat.invite_link:
        return hlink(title=chat.title, url=chat.invite_link)
    else:
        return hbold(chat.title)


@router.my_chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_join(my_chat_member: types.ChatMemberUpdated, event_from_user: types.User,
                  event_chat: types.Chat, session: AsyncSession, bot: Bot):
    model_user = await get_or_add_user(session, event_from_user)
    event_chat = await bot.get_chat(event_chat.id)
    model_channel = await get_or_add_channel(session, event_chat)
    await add_repost_info(session, model_user, model_channel)
    try:
        await bot.send_message(
            chat_id=model_user.tg_id,
            text=f"I've been added to channel \"{chat_link(model_channel)}\""
        )
    except TelegramForbiddenError:
        pass


@router.my_chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
async def on_leave(my_chat_member: types.ChatMemberUpdated, event_chat: types.Chat,
                   session: AsyncSession, bot: Bot):
    model_channel = await get_channel(session, event_chat.id)
    if model_channel is None:
        return
    users = (await session.scalars(
        select(model.User).join(model.RepostInfo).where(
            model.RepostInfo.channel == model_channel))).all()
    for user in users:
        await bot.send_message(
            chat_id=user.tg_id,
            text=f"I've been removed from channel \"{chat_link(model_channel)}\""
        )
    await delete_channel(session, event_chat.id)


@router.channel_post()
async def channel_post_handler(channel_post: types.Message):
    pass


for update_type in router.resolve_used_update_types():
    router.observers[update_type].filter(F.chat.type == "channel")
