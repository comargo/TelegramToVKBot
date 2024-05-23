import logging
import typing

import aiogram.enums
from aiogram import Router, types, Bot, F
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER, IS_ADMIN, \
    PROMOTED_TRANSITION
from aiogram.utils.formatting import Text
from aiogram.utils.markdown import hlink, hbold, text

from tg2vk.database import model, ops

router = Router(name="channel")

logger = logging.getLogger(__name__)


@router.my_chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER),
                       F.chat.type == aiogram.enums.ChatType.CHANNEL)
async def on_join(my_chat_member: types.ChatMemberUpdated, event_from_user: types.User,
                  event_chat: types.Chat, session: ops.AsyncSessionOps, bot: Bot):
    model_user = await session.get_or_add_user(event_from_user)
    model_channel = await session.get_or_add_channel(event_chat)
    await session.add_repost_info(model_user, model_channel)
    try:
        await bot.send_message(
            chat_id=model_user.tg_id,
            **Text("I've been added to channel ", model_channel.channel_link).as_kwargs()
        )
    except TelegramForbiddenError:
        pass


@router.my_chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
async def on_leave(my_chat_member: types.ChatMemberUpdated,
                   event_chat: types.Chat,
                   session: ops.AsyncSessionOps, bot: Bot):
    model_channel = await session.get_channel(event_chat)
    if model_channel is None:
        return
    users = await session.get_channel_users(model_channel)
    for user in users:
        await bot.send_message(
            chat_id=user.tg_id,
            **Text("I've been removed from channel", model_channel.channel_link).as_kwargs()
        )
    await session.delete_channel(model_channel)


@router.chat_member(ChatMemberUpdatedFilter(~PROMOTED_TRANSITION))
async def on_user_leave(chat_member: types.ChatMemberUpdated,
                        event_chat: types.Chat,
                        event_user_from: types.User,
                        session: ops.AsyncSessionOps,
                        bot: Bot):
    user = await session.get_user(event_user_from)
    channel = await session.get_channel(event_chat)
    if user is None or channel is None:
        return

    deleted_reposts = await session.delete_reposts(user, channel)
    if deleted_reposts:
        message = Text("You are not admin of channel ", channel.channel_link,
                       " anymore. Reposts deleted")
        await bot.send_message(
            chat_id=user.tg_id,
            **message.as_kwargs()
        )

    if len(list(await session.get_channel_users(channel))) == 0:
        await session.delete_channel(channel)
        await bot.leave_chat(event_chat.id)


@router.channel_post()
async def channel_post_handler(channel_post: types.Message):
    pass


for update_type in router.resolve_used_update_types():
    router.observers[update_type].filter(F.chat.type == aiogram.enums.ChatType.CHANNEL)
