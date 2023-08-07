import requests
import logging

import asyncio

from aiogram.client.session.middlewares.request_logging import RequestLogging
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import Command
from aiogram.methods import GetUpdates
from aiogram.types import Message, ReplyKeyboardRemove

from config import TOKEN, WEATHER_API_KEY, redis_db
from helper_functions import is_user_admin
from middlewares.incoming_messages_middleware import LoggingMiddleware
from middlewares.outcoming_messages_middleware import OutgoingRequestMiddleware

logging.basicConfig(level=logging.DEBUG)

router = Router()
form_router = Router()
all_router = Router()

#
# @all_router.message()
# async def return_message(message: types.Message): pass


@router.message(Command(commands=["start"]))
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    first_name = message.from_user.first_name
    await message.answer(f"Welcome, {first_name}.")


# States
class WeatherForm(StatesGroup):
    city = State()  # Will be represented in storage as 'Form:gender'


@router.message(Command(commands=["weather"]))
async def command_start(message: Message, state: FSMContext) -> None:
    await state.set_state(WeatherForm.city)
    await message.answer(
        "Hello! To get the weather, please enter your city name.",
        reply_markup=ReplyKeyboardRemove(),
    )


@form_router.message(Command("cancel"))
@form_router.message(F.text.casefold() == "cancel")
async def cancel_handler(message: Message, state: FSMContext) -> None:
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info("Cancelling state %r", current_state)
    await state.clear()
    await message.answer(
        "Cancelled.",
        reply_markup=ReplyKeyboardRemove(),
    )


@form_router.message(WeatherForm.city)
async def process_weather(message: types.Message, state: FSMContext):
    await state.set_state(WeatherForm.city)
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
        # And send message
    await state.clear()
    await message.answer(
        response_text,
        resize_keyboard=True,
    )


@router.message(Command("promote"))
async def promote_admin(message: types.Message):
    if is_user_admin(message.from_user.id):
        # Check if a user is mentioned in the command
        new_admin_id = message.text.split()[1]
        if not new_admin_id.isdigit():
            await message.answer(f'The user id can contain digits only. You are doing something wrong, sorry.')
        # Grant admin privileges to the specified user
        else:
            redis_db.sadd('admin_users', new_admin_id)
            await message.answer(f'The user with id {new_admin_id} is now an admin!')
    else:
        await message.answer('You do not have permission to use this command.')


@router.message(Command("newbot"))
async def new_bot(message: types.Message):
    if is_user_admin(message.from_user.id):
        api_key = message.text.split()[1]
        is_active = redis_db.sismember('active_tokens', api_key)
        if is_active:
            await message.answer('The token is already active!')
        else:
            redis_db.sadd("active_tokens", api_key)
            await message.answer('The token was added, the new bout is now running.')
            await main()
    else:
        await message.answer("You do no have access to this function.")


async def main() -> None:
    # Dispatcher is a root router

    # Initialize Bot instance with a default parse mode which will be passed to all API calls

    bot_tokens = [token for token in redis_db.smembers("active_tokens")]
    bots = []
    for token in bot_tokens:
        current_bot = Bot(token=token, parse_mode="HTML")
        current_bot.session.middleware(OutgoingRequestMiddleware(ignore_methods=[GetUpdates]))
        bots.append(current_bot)
    dp = Dispatcher()
    router.message.outer_middleware(LoggingMiddleware())
    dp.include_router(router)
    dp.include_router(form_router)
    # And the run events dispatching
    await dp.start_polling(*bots)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
