from typing import Callable, Dict, Awaitable, Any
import random

from aiogram import BaseMiddleware
from aiogram.types import Message

from config import redis_db


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        # Log the message text to Redis
        redis_db.lpush(f"user_{event.from_user.id}_messages", event.text)
        return await handler(event, data)
