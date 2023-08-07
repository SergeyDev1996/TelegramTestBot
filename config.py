import os

# from aiogram import Bot, Dispatcher, executor, types
# from aiogram.contrib.fsm_storage.memory import MemoryStorage
import redis

TOKEN = os.environ.get("TELEGRAM_TOKEN", None)
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", None)
# bot = Bot(token=TOKEN)
# storage = MemoryStorage()
# dp = Dispatcher(bot, storage=storage)
redis_db = redis.Redis(host='redis', port=6379, decode_responses=True)