import aiogram.enums
from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramNotFound, TelegramForbiddenError, TelegramBadRequest
from aiogram.filters import Command, CommandStart, StateFilter, and_f, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove, Chat
from aiogram.utils.markdown import hbold, text, hlink
from aiogram.utils.formatting import BotCommand, as_list, Text, as_section, as_numbered_section

import tg2vk.vk
from tg2vk import vk
from tg2vk.database import model, ops
from tg2vk.middlewares import UserMiddleware

router = Router(name="private")

help_message = f"""
To start using me, just invite me to channel.
/list - list of channels, bot invited to
""".strip()

stateless_router = Router(name="private.stateless")


@stateless_router.message(CommandStart())
async def command_start(message: Message) -> None:
    await message.answer(f"Hello, {hbold(message.from_user.full_name)}!\n" + help_message,
                         reply_markup=ReplyKeyboardRemove())
    return None


@stateless_router.message(Command("help"))
async def command_help(message: Message) -> None:
    await message.answer(help_message, reply_markup=ReplyKeyboardRemove())


@stateless_router.message(Command("list"))
async def command_list(message: Message, event_from_user: model.User,
                       session: ops.AsyncSessionOps) -> None:
    from_user = await session.get_or_add_user(event_from_user)
    channels = await session.get_user_channels(from_user)
    if channels:
        txt_channels = as_numbered_section(
            Text("You have invited bot to next channels:"),
            *[channel.channel_link for channel in channels])
    else:
        txt_channels = as_list(
            "You have not invited bot to any channels.",
            "But there could be channels in common that other users invited bot."
        )
    await message.answer(**txt_channels.as_kwargs())


class RepostState(StatesGroup):
    original_message = State()
    community_id = State()
    community_token = State()


@stateless_router.message(Command("repost"))
async def command_repost(message: Message, state: FSMContext):
    await state.set_state(RepostState.original_message)
    await message.answer("Forward message from channel, you want to repost")


@router.message(and_f(StateFilter(RepostState),
                      or_f(Command("cancel"), F.text.casefold == "cancel")))
async def cancel_repost(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Canceled...")


@router.message(RepostState.original_message,
                F.forward_origin.type == aiogram.enums.MessageOriginType.CHANNEL)
async def forwarded_message(message: Message, state: FSMContext,
                            event_from_user: aiogram.types.User,
                            session: ops.AsyncSessionOps, bot: Bot) -> None:
    channel = None
    try:
        member = await message.forward_origin.chat.get_member(event_from_user.id)
        if member.status not in (aiogram.enums.ChatMemberStatus.ADMINISTRATOR,
                                 aiogram.enums.ChatMemberStatus.CREATOR):
            await message.answer("Only channel administrator can setup reposts")
            return
        channel = await session.get_channel(message.forward_origin.chat)
    except (TelegramNotFound, TelegramForbiddenError, TelegramBadRequest):
        pass
    if not channel:
        await message.answer("I was not invited to this channel!")
        return

    await state.update_data(channel_id=channel.id)
    await state.set_state(RepostState.community_id)
    await message.answer("Specify community ID")


@router.message(RepostState.original_message)
async def original_message_invalid_update(message: Message):
    await message.answer("Message was not forwarded from channel")


@router.message(RepostState.community_id)
async def message_community_id(message: Message, state: FSMContext):
    community_id = message.text
    await message.answer("Specify community token")
    await state.update_data(community_id=community_id)
    await state.set_state(RepostState.community_token)


@router.message(RepostState.community_token)
async def message_community_token(message: Message, state: FSMContext,
                                  session: ops.AsyncSessionOps,
                                  event_from_user: aiogram.types.User):
    from_user = await session.get_or_add_user(event_from_user)
    community_token = message.text
    await state.update_data(community_token=community_token)
    data = await state.get_data()
    group_info = await vk.get_group_info(group_id=data['community_id'],
                                         group_token=community_token)
    if not group_info:
        await message.answer("Invalid community ID/Token pair. "
                             "Please specify community ID or /cancel to break.")
        await state.set_state(RepostState.community_id)
        return
    community_name = group_info["name"]
    community_photo = group_info["photo_200"]
    channel = await session.get_channel(data['channel_id'])
    repost_info = await session.add_repost_info(user=from_user, channel=channel,
                                                community_id=data['community_id'],
                                                community_token=community_token,
                                                community_name=community_name)
    response = as_list(
        Text("Repost from channel ", channel.channel_link,
             " to community ", repost_info.community_link, " has been established."),
        Text("You can forward message from channel")
    )
    await message.answer(**response.as_kwargs())

    await state.clear()


for update_type in stateless_router.resolve_used_update_types():
    stateless_router.observers[update_type].middleware(UserMiddleware())
    stateless_router.observers[update_type].filter(StateFilter(None), F.chat.type == "private")

router.include_router(stateless_router)
