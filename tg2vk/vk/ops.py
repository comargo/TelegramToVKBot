from typing import Final

from aiohttp import ClientResponseError
from aiohttp.client import ClientSession

VK_API: Final[str] = "https://api.vk.ru/"


async def get_group_info(group_id, group_token: str):
    try:
        async with ClientSession(VK_API) as client:
            response = await client.post("method/groups.getById",
                                         data={"access_token": group_token, "group_id": group_id})
            response.raise_for_status()
            group_info = response.json()["response"]["groups"][0]
            return response.json()
    except (KeyError, ClientResponseError):
        return None
