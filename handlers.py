"""Handlers for our bot."""
import supabase as sb

from config_reader import config

from aiogram import F, Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.filters.command import Command
from aiogram.types import Message, CallbackQuery
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State


router = Router()

URL = config.url.get_secret_value()
KEY = config.key.get_secret_value()

CLIENT = sb.create_client(URL, KEY)


class Registration(StatesGroup):
    """Fields to be complited during registartion."""

    name = State()
    passed = State()

class HomeWork(StatesGroup):
    """Field to be complited during homework creation"""

    choosing_action = State() # Пользователь выбирает, что он хочет сделать: посмотреть текущие ДЗ или добавить новые
    sub_name = State() # Пользователь решил добавить новое ДЗ, тогда ему надо выбрать предмет из имеющихся
    descr = State() # Нужно добавить описание нового ДЗ
    deadline = State() # Нужно ввести дату дедлайна
    view_hw = State() # Пользов атель хочет посмотреть текущие ДЗ




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
    await state.set_state(Registration.passed)


@router.message(StateFilter(Registration.passed), Command("hw"))
async def cmd_random(message: Message):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="Посмотреть текущие ДЗ",
        callback_data="check_current_hw")
    )

    builder.add(InlineKeyboardButton(
        text="Добавить ДЗ",
        callback_data="add_hw")
    )

    builder.adjust(1)

    await message.answer(
        "Выберите действие, которое хотите выполнить",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == 'add_hw')
async def add_hw(callback: CallbackQuery, state: FSMContext, message: Message):
    """Start registration from the beginning."""

    # Выбор всех записей из таблицы subjects
    response = CLIENT.table('subjects').select('*').execute()

    # Получение данных
    subjects = response.data  # Список словарей с предметами

    # Вывод результатов
    for subject in subjects:
        print(subject)


    builder = InlineKeyboardBuilder()


    builder.add(InlineKeyboardButton(
        text="Посмотреть текущие ДЗ",
        callback_data="check_current_hw")
    )

    builder.add(InlineKeyboardButton(
        text="Добавить ДЗ",
        callback_data="add_hw")
    )

    builder.adjust(1)

    await message.answer(
        "Выберите предмет",
        reply_markup=builder.as_markup()
    )



