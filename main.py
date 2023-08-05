import requests

import logging

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ParseMode


from config import TOKEN, WEATHER_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    first_name = message.from_user.first_name
    await bot.send_message(message.from_user.id, f"Welcome, {first_name}.")


# States
class WeatherForm(StatesGroup):
    city = State()  # Will be represented in storage as 'Form:gender'


@dp.message_handler(commands='weather')
async def cmd_start(message: types.Message):
    """
    Conversation's entry point
    """
    # Set state
    await WeatherForm.city.set()

    await message.reply("Hello! To get the weather, please enter your city name.")


# You can use state '*' if you need to handle all states
@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await message.reply('Cancelled.', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=WeatherForm.city)
async def process_weather(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        city = message.text
        url = 'http://api.openweathermap.org/data/2.5/weather'
        params = {
            'q': city,
            'appid': WEATHER_API_KEY,
            'units': 'metric',  # Use 'imperial' for Fahrenheit
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            weather_description = data['weather'][0]['description']
            temp = data['main']['temp']
            country = data['sys']['country']
            response_text = f"Weather in {city}, {country}: {weather_description}, Temperature: {temp}°C"
        else:
            response_text = "Sorry, we were unable to process the weather for your city."
        markup = types.ReplyKeyboardRemove()
        # And send message
        await bot.send_message(
            message.chat.id,
            md.text(
                response_text
            ),
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN,
        )
    # Finish conversation
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
