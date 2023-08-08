import pytest

from main import send_welcome

from aiogram_tests import MockedBot
from aiogram_tests.handler import MessageHandler
from aiogram_tests.types.dataset import MESSAGE


@pytest.mark.asyncio
async def test_echo():
    request = MockedBot(MessageHandler(send_welcome))
    calls = await request.query(message=MESSAGE.as_object(text="Hello, Bot!"))
    answer_message = calls.send_messsage.fetchone()
    assert answer_message.text == "Hello, Bot!"