import aiohttp
from asyncio import run


HOST = 'http://127.0.0.1:8080'


async def main():

    async with aiohttp.ClientSession() as session:
        """POST"""
        # response = await session.post(f'{HOST}/users/',
        #                               json={'username': 'skfniecegc',
        #                                     'password': 'qwecrwer'})
        # print(await response.json())

        # response = await session.post(f'{HOST}/advertisements/',
        #                               json={'header': 'header x',
        #                                     'description': 'description 2',
        #                                     'owner_id': 8})
        # print(await response.json())

        """GET"""
        # response = await session.get(f'{HOST}/users/8')
        # print(await response.json())
        # #
        response = await session.get(f'{HOST}/advertisements/3')
        print(await response.json())

        """PATCH"""
        # response = await session.patch(f'{HOST}/users/8',
        #                               json={'username': 'newusername'})
        # print(await response.json())
        #
        # response = await session.patch(f'{HOST}/advertisements/3',
        #                                json={'header': 'new_header'})
        # print(await response.json())

        """DELETE"""
        # response = await session.delete(f'{HOST}/users/3')
        # print(await response.json())

        # response = await session.delete(f'{HOST}/advertisements/2')
        # print(await response.json())


run(main())