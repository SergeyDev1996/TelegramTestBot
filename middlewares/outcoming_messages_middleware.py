from typing import Optional, List, Type, Any

from aiogram import loggers
from aiogram.client.session.middlewares.base import BaseRequestMiddleware, NextRequestMiddlewareType
from aiogram.methods import TelegramMethod
from aiogram.methods.base import TelegramType, Response

from config import redis_db
from helper_functions import generate_random_8digit


class OutgoingRequestMiddleware(BaseRequestMiddleware):
    def __init__(self, ignore_methods: Optional[List[Type[TelegramMethod[Any]]]] = None):
        """
        Middleware for logging outgoing requests
        """
    async def __call__(
        self,
        make_request: NextRequestMiddlewareType[TelegramType],
        bot: "Bot",
        method: TelegramMethod[TelegramType],
    ) -> Response[TelegramType]:

        if type(method).__name__ == "SendMessage":
            redis_db.hset(f"outgoing_request_{generate_random_8digit()}", mapping={
                "method_name": type(method).__name__,
                "bot_id": bot.id,
                "text": method.text
            })
            redis_db.incr("outgoing_messages_count")
        return await make_request(bot, method)
