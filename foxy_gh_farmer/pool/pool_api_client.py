from aiohttp import ClientSession, ClientTimeout

timeout = ClientTimeout(total=30)

POOL_URL = "https://farmer.chia.foxypool.io"


class PoolApiClient:
    async def get_pool_info(self):
        async with ClientSession(timeout=timeout) as client:
            async with client.get(f"{POOL_URL}/pool_info") as res:
                return await res.json()
