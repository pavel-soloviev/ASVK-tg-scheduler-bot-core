import supabase as sb
import aiogram
import logging
import sys
import asyncio

from config_reader import config

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.client.default import DefaultBotProperties
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

TOKEN = config.bot_token.get_secret_value()
URL = config.url.get_secret_value()
KEY = config.key.get_secret_value()

STORAGE = MemoryStorage()
dp = Dispatcher(storage=STORAGE)
BOT = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

CLIENT = sb.create_client(URL, KEY)

class Registration(StatesGroup):
    name = State()

@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    registration = InlineKeyboardBuilder()
    registration.add(InlineKeyboardButton(
        text="Регистрация",
        callback_data="registration")
    )
    await message.answer("Привет! Я бот 321 группы. Для начала необходимо зарегестрироваться.",
                         reply_markup=registration.as_markup())

@dp.callback_query(F.data == 'registration')
async def registration(callback: CallbackQuery, state: FSMContext):
    same_user = CLIENT.table("users").select("*").eq("tg_id", str(callback.from_user.id)).execute().data 
    if same_user:
        check = InlineKeyboardBuilder()
        check.add(InlineKeyboardButton(
             text="Всё верно",
             callback_data='wait'
        ))
        check.add(InlineKeyboardButton(
             text = 'Редактировать',
             callback_data='fix'
        ))
        await callback.message.answer(f"Вы уже зарегестрированы со следующими данными.\n\nФИО: {same_user[0]['name']}",
                                      reply_markup = check.as_markup())
        return
    await callback.message.answer('Введите ваше ФИО:')
    await state.set_state(Registration.name)

@dp.message(F.text, Registration.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    response = CLIENT.table("users").insert({"tg_id": str(message.from_user.id), "name": message.text}).execute()
    await message.answer("Отлично, дождись решения админимтратора.")

async def main() -> None:
    await dp.start_polling(BOT)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
