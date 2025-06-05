"""Handlers for our bot."""
import supabase as sb

from config_reader import config

from aiogram import F, Router
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import pytz


router = Router()

URL = config.url.get_secret_value()
KEY = config.key.get_secret_value()

CLIENT = sb.create_client(URL, KEY)
moscow_tz = pytz.timezone("Europe/Moscow")


class Registration(StatesGroup):
    """Fields to be complited during registartion."""

    name = State()


@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    """Greeting of the bot."""
    registration = InlineKeyboardBuilder()
    registration.add(InlineKeyboardButton(
        text="Регистрация",
        callback_data="registration")
    )
    await message.answer("Привет! Я бот 321 группы. Для начала необходимо зарегестрироваться.",
                         reply_markup=registration.as_markup())


@router.callback_query(F.data == 'registration')
async def registration(callback: CallbackQuery, state: FSMContext):
    """Start of registartion."""
    same_user = CLIENT.table("users").select("*").eq("tg_id", str(callback.from_user.id)).execute().data
    if same_user:
        check = InlineKeyboardBuilder()
        check.add(InlineKeyboardButton(
            text="Всё верно",
            callback_data='wait'
        ))
        check.add(InlineKeyboardButton(
            text='Редактировать',
            callback_data='fix'
        ))
        await callback.message.answer(f"Вы уже зарегестрированы со следующими данными.\n\nФИО: {same_user[0]['name']}",
                                      reply_markup=check.as_markup())
        return
    await callback.message.answer('Введите ваше ФИО:')
    await state.set_state(Registration.name)


@router.callback_query(F.data == 'fix')
async def fix_registration(callback: CallbackQuery, state: FSMContext):
    """Start registration from the beginning."""
    CLIENT.table("users").delete().eq("tg_id", str(callback.from_user.id)).execute()
    await callback.message.answer('Введите ваше ФИО:')
    await state.set_state(Registration.name)


@router.message(F.text, Registration.name)
async def process_name(message: Message, state: FSMContext):
    """Add user."""
    CLIENT.table("users").insert({"tg_id": str(message.from_user.id), "name": message.text}).execute()
    await message.answer("Отлично, дождитесь решения админимтратора.")


@router.callback_query(F.data == 'wait')
async def wait(callback: CallbackQuery, state: FSMContext):
    """Standart response."""
    await callback.message.answer('Отлично!')


@router.message(Command("add_deadline"))
async def cmd_add_deadline(message: Message, command: CommandObject):
    """Add deadline."""
    try:
        parts = message.text.split(maxsplit=3)
        if len(parts) < 4:
            raise ValueError("Недостаточно аргументов")
        date_str, time_str, *title_parts = parts[1:]
        title = " ".join(title_parts)

        naive_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        deadline = moscow_tz.localize(naive_dt)

        CLIENT.table("deadlines").insert({
            "telegram_id": message.from_user.id,
            "title": title,
            "deadline_at": deadline.isoformat(),
            "notified": False
        }).execute()

        await message.answer(f"✅ Дедлайн «{title}» добавлен на {deadline.strftime('%d.%m.%Y %H:%M')} (МСК)")
    except Exception as e:
        await message.answer(f"Ошибка: {e}\nПример команды:\n/add_deadline 2025-06-10 18:30 Сдать проект")
