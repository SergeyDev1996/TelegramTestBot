import os

import redis

TOKEN = os.environ.get("TELEGRAM_TOKEN", None)
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", None)
redis_db = redis.Redis(host='redis', port=6379, decode_responses=True)