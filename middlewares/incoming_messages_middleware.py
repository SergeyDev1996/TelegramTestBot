from typing import Callable, Dict, Awaitable, Any
import random

from aiogram import BaseMiddleware
from aiogram.types import Message

from config import redis_db


def generate_random_8digit():
    return random.randint(10000000, 99999999)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        # Log the message text to Redis
        redis_db.hset(f"income_message{generate_random_8digit()}", mapping={
            'text': event.text,
            'user_id': event.from_user.id
        })
        # Call the handler and pass the event and data to it
        return await handler(event, data)


