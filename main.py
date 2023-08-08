import requests
import logging

import asyncio

from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import Command
from aiogram.methods import GetUpdates
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.utils.token import validate_token, TokenValidationError

from config import WEATHER_API_KEY, redis_db
from helper_functions import is_user_admin
from middlewares.incoming_messages_middleware import LoggingMiddleware
from middlewares.outcoming_messages_middleware import OutgoingRequestMiddleware

logging.basicConfig(level=logging.DEBUG)

router = Router()
form_router = Router()
all_router = Router()


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
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric",  # Use 'imperial' for Fahrenheit
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        weather_description = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        country = data["sys"]["country"]
        response_text = (
            f"Weather in {city},"
            f" {country}:"
            f" {weather_description},"
            f" Temperature: {temp}°C"
        )
    else:
        response_text = "Sorry, we were unable to" " process the weather for your city."
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
            await message.answer(
                "The user id can contain digits only." "You are doing something wrong."
            )
        # Grant admin privileges to the specified user
        else:
            redis_db.sadd("admin_users", new_admin_id)
            await message.answer(
                f"The user with id {new_admin_id}" f" is now an admin!"
            )
    else:
        await message.answer("You do not have permission to use this command.")


@router.message(Command("newbot"))
async def new_bot(message: types.Message):
    if is_user_admin(message.from_user.id):
        api_key = message.text.split()[1]
        is_active = redis_db.sismember("active_tokens", api_key)
        try:
            validate_token(api_key)
            if is_active:
                await message.answer("The token is already active!")
            else:
                redis_db.sadd("active_tokens", api_key)
                redis_db.incr("bots_created")
                await message.answer(
                    "The token was added," " the new bot is now running."
                )
                await main(first_run=False)
        except TokenValidationError:
            await message.answer("The token is invalid, sorry.")
        await message.answer("The token is invalid, sorry.")
    else:
        await message.answer("You do not have access to this function.")


@router.message(Command("statistics"))
async def statistics(message: types.Message):
    if is_user_admin(message.from_user.id):
        incoming_messages, outgoing_messages, bots_created = (
            redis_db.get("incoming_messages_count") or 0,
            redis_db.get("outgoing_messages_count") or 0,
            redis_db.get("bots_created") or 0,
        )
        bots_plural_or_single = ""
        if bots_created == 0 and bots_created != 1:
            bots_plural_or_single = f"{bots_created} bots were created."
        else:
            bots_plural_or_single = "1 bot was created."
        await message.answer(
            f"We received {incoming_messages}"
            f" incoming messages,"
            f" {outgoing_messages} outgoing messages."
            f" {bots_plural_or_single}"
        )
    else:
        await message.answer("You do not have access to this function.")


async def main(first_run=True) -> None:
    # Dispatcher is a root router
    # Initialize Bot instance with a
    # default parse mode which will be passed to all API calls
    bot_tokens = [token for token in redis_db.smembers("active_tokens")]
    bots = []
    for token in bot_tokens:
        try:
            current_bot = Bot(token=token, parse_mode="HTML")
        except TokenValidationError:
            continue
        current_bot.session.middleware(
            OutgoingRequestMiddleware(ignore_methods=[GetUpdates])
        )
        bots.append(current_bot)
    dp = Dispatcher()
    router.message.outer_middleware(LoggingMiddleware())
    if first_run:
        dp.include_routers(router, form_router)
    await dp.start_polling(*bots)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
