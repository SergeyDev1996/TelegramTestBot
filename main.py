"""
This is a echo bot.
It echoes any incoming text messages.
"""
import logging

from aiogram import Bot, Dispatcher, executor, types

from config import TOKEN

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await bot.send_message(message.from_user.id, f"Welcome, {message.from_user.first_name}.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)