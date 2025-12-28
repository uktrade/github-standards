import logging
import pytest_asyncio

from aiohttp import web
from aiohttp.pytest_plugin import AiohttpClient


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


@pytest_asyncio.fixture
async def aio_client_with_app(aiohttp_client: AiohttpClient):
    web_app = web.Application()
    client = await aiohttp_client(web_app)
    client.app.router._frozen = False  # Allows setting fake requests inside a unit test
    return client
