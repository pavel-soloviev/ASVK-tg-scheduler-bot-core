"""Handlers for our bot."""
import supabase as sb

from config_reader import config

from aiogram import F, Router
from aiogram.filters import CommandStart, Command
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
    print(str(callback.from_user.username))
    same_user = CLIENT.table("users").select("*").eq("tg_username", str(callback.from_user.username)).execute().data
    if same_user:
        check = InlineKeyboardBuilder()
        check.add(InlineKeyboardButton(
            text="Всё верно",
            callback_data='right'
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
    CLIENT.table("users").delete().eq("tg_username", str(callback.from_user.username)).execute()
    await callback.message.answer('Введите ваше ФИО:')
    await state.set_state(Registration.name)


@router.message(F.text, Registration.name)
async def process_name(message: Message, state: FSMContext):
    """Add user."""
    CLIENT.table("users").insert({"tg_id": str(message.from_user.id),
                                  "name": message.text,
                                  "tg_username": message.from_user.username}).execute()
    await message.answer("Отлично!")


@router.callback_query(F.data == 'right')
async def wait(callback: CallbackQuery, state: FSMContext):
    """Standart response."""
    tg_id, tg_username = str(callback.from_user.id), str(callback.from_user.username)
    CLIENT.table("users").update({"tg_id": tg_id}).eq("tg_username", tg_username).execute()
    await callback.message.answer('Отлично!')


@router.message(F.text, Command("schedule"))
async def set_day(message: Message, state: FSMContext):
    """Select day to get schedule."""
    day = InlineKeyboardBuilder()
    day.add(InlineKeyboardButton(
        text="Понедельник",
        callback_data="monday")
    )
    day.add(InlineKeyboardButton(
        text="Вторник",
        callback_data="tuesday")
    )
    day.add(InlineKeyboardButton(
        text="Среда",
        callback_data="wednesday")
    )
    day.add(InlineKeyboardButton(
        text="Четверг",
        callback_data="thursday")
    )
    day.add(InlineKeyboardButton(
        text="Пятница",
        callback_data="friday")
    )
    day.adjust(1)
    await message.answer("Выбери день недели",
                         reply_markup=day.as_markup())


def get_schedule(day, day_to_print):
    """Get all information to print schedule."""
    schedule = CLIENT.table("schedule").select("*").eq("day_of_week", day).execute().data
    if not schedule:
        return 'В этот день нет пар.'
    mes = 'Расписание на {}'.format(day_to_print)
    schedule = sorted(schedule, key=lambda x: x['pair_number'])
    for i in schedule:
        classroom = CLIENT.table('classrooms').select('number').eq("id", i["classroom_id"]).execute().data
        time = CLIENT.table('time_slots').select('*').eq("pair_number", i["pair_number"]).execute().data
        if i["teacher_id"]:
            teacher = CLIENT.table('teachers').select('*').eq("id", i["teacher_id"]).execute().data
        else:
            teacher = ''
        match i['week_type']:
            case 'even':
                week_type = ' чётные недели'
            case 'odd':
                week_type = ' нечётные недели'
            case _:
                week_type = ''
        mes += f"\n\n{time[0]['start_time'][:-3]} - {time[0]['end_time'][:-3]}" + week_type
        mes += "\nПредмет: {}".format(i['subject'])
        mes += "\nКабинет: {}".format(classroom[0]['number'])
        if teacher:
            mes += "\nПреподаватель: {}".format(teacher[0]['name'])
    return mes


@router.callback_query(F.data == 'monday')
async def monday(callback: CallbackQuery, state: FSMContext):
    """Schedule for monday."""
    schedule = get_schedule(1, 'понедельник')
    await callback.message.answer(schedule)


@router.callback_query(F.data == 'tuesday')
async def tuesday(callback: CallbackQuery, state: FSMContext):
    """Schedule for tuesday."""
    schedule = get_schedule(2, 'вторник')
    await callback.message.answer(schedule)


@router.callback_query(F.data == 'wednesday')
async def wednesday(callback: CallbackQuery, state: FSMContext):
    """Schedule for wednesday."""
    schedule = get_schedule(3, 'среда')
    await callback.message.answer(schedule)


@router.callback_query(F.data == 'thursday')
async def thursday(callback: CallbackQuery, state: FSMContext):
    """Schedule for thursday."""
    schedule = get_schedule(4, 'четверг')
    await callback.message.answer(schedule)


@router.callback_query(F.data == 'friday')
async def friday(callback: CallbackQuery, state: FSMContext):
    """Schedule for friday."""
    schedule = get_schedule(5, 'пятница')
    await callback.message.answer(schedule)

@router.message(F.text, Command("help"))
async def get_help(message: Message, state: FSMContext):
    """Print all commands with instruction"""
    await message.answer("""
                         /schedule - просмотр расписания,
                         /smth else
                         """)
