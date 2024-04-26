from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.utils.markdown import hbold, text
from sqlalchemy.ext.asyncio import AsyncSession

from tg2vk.database import model
from tg2vk.database.ops import get_or_add_user
from tg2vk.middlewares import UserMiddleware

router = Router(name="private")

help_message = f"""
To start using me, just invite me to channel.
/list - list of channels, bot invited to
""".strip()


@router.message(CommandStart())
async def command_start(message: Message) -> None:
    await message.answer(f"Hello, {hbold(message.from_user.full_name)}!\n" + help_message,
                         reply_markup=ReplyKeyboardRemove())
    return None


@router.message(Command("help"))
async def command_help(message: Message) -> None:
    await message.answer(help_message, reply_markup=ReplyKeyboardRemove())


@router.message(Command("list"))
async def command_list(message: Message, state: FSMContext,
                       from_user: model.User, session: AsyncSession) -> None:
    from sqlalchemy import select

    q = select(model.Channel).join(model.Channel.reposts).group_by(model.Channel.id).where(model.RepostInfo.user == from_user)
    channels = await session.scalars(q)
    txt_channels = text(*[channel.title for channel in channels], sep="\n")
    await message.answer(txt_channels)

for update_type in router.resolve_used_update_types():
    router.observers[update_type].middleware(UserMiddleware())
    router.observers[update_type].filter(F.chat.type == "private")
