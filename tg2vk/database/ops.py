from typing import Optional, Union, Iterable, TypedDict

from aiogram import types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tg2vk.database import model


class Link(TypedDict):
    title: str
    url: str


class AsyncSessionOps(AsyncSession):
    async def get_user(self, user: Union[int, types.User]) -> Optional[model.User]:
        if not isinstance(user, int):
            user = user.id
        model_user: Optional[model.User] = await self.scalar(
            select(model.User).where(model.User.tg_id == user)
        )
        return model_user

    async def get_or_add_user(self, user: types.User) -> model.User:
        model_user = await self.get_user(user)
        if model_user is None:
            model_user = model.User(tg_id=user.id, lang=user.language_code)
            self.add(model_user)
            await self.commit()
        return model_user

    async def get_channel(self, channel: Union[int, types.Chat]) -> Optional[model.Channel]:
        if not isinstance(channel, int):
            channel = channel.id
        model_channel = await self.scalar(
            select(model.Channel).where(model.Channel.channel_id == channel)
        )
        return model_channel

    async def get_or_add_channel(self, channel: types.Chat) -> model.Channel:
        model_channel = await self.get_channel(channel.id)
        if model_channel is None:
            model_channel = model.Channel(channel_id=channel.id,
                                          title=channel.title)
            self.add(model_channel)
            await self.commit()
        return model_channel

    async def get_channel_users(self, channel: model.Channel) -> Iterable[model.User]:
        users = (await self.scalars(
            select(model.User).join(model.RepostInfo).where(
                model.RepostInfo.channel == channel).distinct().order_by(model.User.tg_id))).all()
        return users

    async def get_user_channels(self, user: model.User) -> Iterable[model.Channel]:
        channels = (await self.scalars(
            select(model.Channel).
                join(model.RepostInfo).where(model.RepostInfo.user == user).
                distinct().order_by(model.Channel.channel_id)
        )).all()
        return channels

    async def delete_channel(self, channel: model.Channel) -> None:
        await self.delete(channel)
        await self.commit()

    async def add_repost_info(self,
                              user: model.User,
                              channel: model.Channel,
                              community_id: Optional[int] = None,
                              community_token: Optional[str] = None,
                              community_name: Optional[str] = None
                              ) -> model.RepostInfo:
        selector = select(model.RepostInfo).where(
            model.RepostInfo.user == user,
            model.RepostInfo.channel == channel,
            model.RepostInfo.community_id is None,
            model.RepostInfo.community_token is None)
        repost_info:model.RepostInfo = await self.scalar(selector)
        if not repost_info:
            repost_info = model.RepostInfo(user=user, channel=channel,
                                           community_id=community_id,
                                           community_token=community_token,
                                           community_name=community_name)
            self.add(repost_info)
        else:
            repost_info.community_id = community_id
            repost_info.community_token = community_token
            repost_info.community_name = community_name

        await self.commit()
        return repost_info

    async def get_reposts(self, user: Optional[model.User] = None,
                          channel: Optional[model.Channel] = None) -> Iterable[model.RepostInfo]:
        selector = select(model.RepostInfo)
        if user:
            selector = selector.where(model.RepostInfo.user == user)
        if channel:
            selector = selector.where(model.RepostInfo.channel == channel)
        return (await self.scalars(selector)).all()

    async def delete_repost(self, repost: model.RepostInfo) -> None:
        await self.delete(repost)
        await self.commit()

    async def delete_reposts(self, user: Optional[model.User] = None,
                             channel: Optional[model.Channel] = None) -> Optional[list[Link]]:

        reposts = await self.get_reposts(user, channel)
        deleted_reposts: list[Link] = []
        for repost in reposts:
            deleted_reposts.append(repost.community_link)
            await self.delete_repost(repost)
        return deleted_reposts
