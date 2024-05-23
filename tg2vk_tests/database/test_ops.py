import unittest

import aiogram
from aiogram.types import User, Chat
from sqlalchemy import select, func

from tg2vk.database import model, engine
from tg2vk_tests.fixtures import config, DbData


class OpsTestCase(unittest.IsolatedAsyncioTestCase):
    def assertSortedListEqual(self, list1, list2, msg=None):
        return self.assertListEqual(sorted(list1), sorted(list2), msg)

    async def asyncSetUp(self) -> None:
        session_maker = engine.get_session_maker(config)
        self.session = session_maker()
        await engine.create_db(self.session)
        self.addAsyncCleanup(self.session.close)
        self.data = DbData()
        async with self.session.begin():
            self.session.add_all(self.data.all_data)

    async def test_get_user(self):
        self.assertEqual(await self.session.get_user(1), self.data.users[1])
        self.assertIsNone(await self.session.get_user(10))
        pass

    async def test_get_or_add_user(self):
        self.assertEqual(
            await self.session.get_or_add_user(User(id=0, is_bot=False, first_name="")),
            self.data.users[0]
        )
        user_count = await self.session.scalar(select(func.count("*")).select_from(model.User))
        self.assertIsNotNone(
            await self.session.get_or_add_user(User(id=4, is_bot=False, first_name=""))
        )
        self.assertEqual(
            await self.session.scalar(select(func.count("*")).select_from(model.User)),
            user_count + 1
        )

    async def test_get_channel(self):
        self.assertEqual(await self.session.get_channel(101), self.data.channels[1])
        self.assertIsNone(await self.session.get_channel(10))

    async def test_get_or_add_channel(self):
        self.assertEqual(
            await self.session.get_or_add_channel(Chat(id=100, type=aiogram.enums.ChatType.CHANNEL, title="")),
            self.data.channels[0]
        )
        channel_count = await self.session.scalar(select(func.count()).select_from(model.Channel))
        self.assertIsNotNone(
            await self.session.get_or_add_channel(
                Chat(id=104, type="channel", title="")
            )
        )
        self.assertEqual(
            await self.session.scalar(select(func.count()).select_from(model.Channel)),
            channel_count + 1
        )

    async def test_get_channel_users(self):
        users100 = await self.session.get_channel_users(self.data.channels[0])
        self.assertSortedListEqual([self.data.users[0]], users100)

        users101 = await self.session.get_channel_users(self.data.channels[1])
        self.assertSortedListEqual([self.data.users[0], self.data.users[1]], users101)

        users102 = await self.session.get_channel_users(self.data.channels[2])
        self.assertSortedListEqual([self.data.users[0], self.data.users[2]], users102)

    async def test_delete_channel(self):
        channel = await self.session.get_channel(101)
        self.assertIsNotNone(channel)
        await self.session.delete_channel(channel)
        self.assertIsNone(await self.session.get_channel(101))
        self.assertEqual(await self.session.scalar(
            select(func.count("*")).
                select_from(model.RepostInfo).
                where(model.RepostInfo.channel_id == channel.id)
        ), 0)

    async def test_add_repost_info(self):
        reposts_count = await self.session.scalar(
            select(func.count()).select_from(model.RepostInfo)
        )
        await self.session.add_repost_info(self.data.users[1], self.data.channels[0])
        self.assertEqual(await self.session.scalar(
            select(func.count()).select_from(model.RepostInfo)),
                         reposts_count + 1)

    async def test_get_reposts(self):
        # 1. Channel only
        reposts = await self.session.get_reposts(channel=self.data.channels[2])
        self.assertSortedListEqual(reposts, self.data.reposts[4:7])

        # 2. User/channel
        reposts = await self.session.get_reposts(channel=self.data.channels[2],
                                                 user=self.data.users[0])
        self.assertSortedListEqual(reposts, [self.data.reposts[i] for i in (4, 6)])

        # 3. User only
        reposts = await self.session.get_reposts(user=self.data.users[0])
        self.assertSortedListEqual(reposts,
                                   [self.data.reposts[i] for i in (0, 1, 3, 4, 6)])

    async def test_delete_reposts_channel(self):
        await self.session.delete_reposts(channel=self.data.channels[2])
        self.assertSortedListEqual(
            (await self.session.scalars(select(model.RepostInfo))).all(),
            self.data.reposts[:4]
        )

    async def test_delete_reposts_user_channel(self):
        await self.session.delete_reposts(channel=self.data.channels[2],
                                          user=self.data.users[0])
        self.assertSortedListEqual(
            (await self.session.scalars(select(model.RepostInfo))).all(),
            [self.data.reposts[i] for i in (0, 1, 2, 3, 5)]
        )

    async def test_delete_reposts_user(self):
        await self.session.delete_reposts(user=self.data.users[0])
        self.assertSortedListEqual(
            (await self.session.scalars(select(model.RepostInfo))).all(),
            [self.data.reposts[i] for i in (2, 5)]
        )
