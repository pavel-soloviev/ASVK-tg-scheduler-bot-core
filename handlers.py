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
import asyncio


router = Router()

URL = config.url.get_secret_value()
KEY = config.key.get_secret_value()

CLIENT = sb.create_client(URL, KEY)
moscow_tz = pytz.timezone("Europe/Moscow")


class Registration(StatesGroup):
    """Fields to be complited during registartion."""

    name = State()


class AddDeadline(StatesGroup):
    """States for cgreating new deadlines."""

    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_title = State()


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


@router.message(Command("deadlines"))
async def cmd_deadline(message: Message, command: CommandObject):
    """Options to work with deadlines."""
    kb = InlineKeyboardBuilder()

    kb.row(
        InlineKeyboardButton(text="Создать", callback_data="create"),
        InlineKeyboardButton(text="Посмотреть список", callback_data="check_list"),
    )

    await message.answer(
        "Здесь можно настроить или узнать текущие дедлайны. Выберите действие:",
        reply_markup=kb.as_markup()
    )


@router.callback_query(F.data == "create")
async def start_add_deadline(callback: CallbackQuery, state: FSMContext):
    """Create new deadline."""
    await callback.message.edit_text("Введите дату дедлайна в формате YYYY-MM-DD")
    await state.set_state(AddDeadline.waiting_for_date)


@router.message(AddDeadline.waiting_for_date)
async def input_date(message: Message, state: FSMContext):
    """Input deadline date."""
    try:
        date = datetime.strptime(message.text, "%Y-%m-%d").date()
        await state.update_data(date=date)
        await message.answer("Теперь введите время дедлайна в формате HH:MM")
        await state.set_state(AddDeadline.waiting_for_time)
    except ValueError:
        await message.answer("⚠ Неверный формат. Введите дату как YYYY-MM-DD")


@router.message(AddDeadline.waiting_for_time)
async def input_time(message: Message, state: FSMContext):
    """Input deadline time."""
    try:
        time = datetime.strptime(message.text, "%H:%M").time()
        await state.update_data(time=time)
        await message.answer("Теперь введите название дедлайна")
        await state.set_state(AddDeadline.waiting_for_title)
    except ValueError:
        await message.answer("⚠ Неверный формат. Введите время как HH:MM")


@router.message(AddDeadline.waiting_for_title)
async def input_title(message: Message, state: FSMContext):
    """Input deadline title."""
    user_data = await state.get_data()
    title = message.text

    naive_dt = datetime.combine(user_data["date"], user_data["time"])
    moscow_dt = moscow_tz.localize(naive_dt)

    CLIENT.table("deadlines").insert({
        "telegram_id": message.from_user.id,
        "title": title,
        "deadline_at": moscow_dt.isoformat(),
        "notified": False
    }).execute()

    await message.answer(f"✅ Дедлайн «{title}» добавлен на {moscow_dt.strftime('%d.%m.%Y %H:%M')} (МСК)")
    await state.clear()


@router.callback_query(F.data == "check_list")
async def check_deadlines_list(callback: CallbackQuery, state: FSMContext):
    """Check all deadlines."""
    user_id = callback.from_user.id
    now = datetime.now(pytz.UTC)
    future_deadlines = CLIENT.table("deadlines").select(
        "*").eq("telegram_id", user_id).gt("deadline_at", now.isoformat()).execute()
    if not future_deadlines:
        await callback.message.answer("🎉 У вас пока нет активных дедлайнов!")
        return

    sorted_deadlines = sorted(
        future_deadlines.data,
        key=lambda x: datetime.fromisoformat(x['deadline_at'])
    )

    text = "📅 <b>Ваши дедлайны:</b>\n\n"
    for i, deadline in enumerate(sorted_deadlines, 1):
        print(deadline)
        deadline_time = datetime.fromisoformat(deadline["deadline_at"]).strftime('%d.%m.%Y в %H:%M')
        text += (
            f"{i}. <b>{deadline['title']}</b>\n"
            f"   └ 🕒 {deadline_time}\n\n"
        )

    await callback.message.answer(text, parse_mode="HTML")
