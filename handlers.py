"""Handlers for our bot."""
import supabase as sb

from config_reader import config

from aiogram import F, Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.filters.command import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime


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
    selecting_subject = State() # Пользователь решил добавить новое ДЗ, тогда ему надо выбрать предмет из имеющихся
    entering_task = State() # Нужно добавить описание нового ДЗ
    entering_deadline = State() # Нужно ввести дату дедлайна
    viewing_homeworks = State() # Пользователь хочет посмотреть текущие ДЗ




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
async def homework_menu(message: Message, state: FSMContext):
    """Start of hw command. Chose between add and check homework"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Добавить ДЗ", callback_data="add_hw")],
        [InlineKeyboardButton(text="Посмотреть ДЗ", callback_data="view_hw")]
    ])
    await message.answer("Выберите действие:", reply_markup=keyboard)
    await state.set_state(HomeWork.choosing_action)


@router.callback_query(HomeWork.choosing_action, F.data == "add_hw")
async def action_selected(callback: CallbackQuery, state: FSMContext):
    """Adding hw selected. Choose subject to add hw"""


    await callback.answer()
    action = callback.data
    
    response = CLIENT.table('subjects').select('id, name').execute()
    subjects = response.data
        
    if not subjects:
        await callback.message.answer("В базе нет предметов.")
        return await state.clear()
            
    builder = InlineKeyboardBuilder()
    for subj in subjects:
        builder.button(text=subj['name'], callback_data=f"subject_{subj['id']}")

    builder.adjust(2)
    await callback.message.answer("Выберите предмет:", reply_markup=builder.as_markup())
        
    await state.set_state(HomeWork.selecting_subject)
    await callback.answer()


@router.callback_query(HomeWork.selecting_subject)
async def subject_selected(callback: CallbackQuery, state: FSMContext):
    """Inserting hw description of a chosen subject"""

    #print(f'DATA = {callback.data}')
    subject_id = int(callback.data.split("_")[-1])
    await state.update_data(subject_id=subject_id)
    
    try:
        response = CLIENT.table('subjects').select('name').eq('id', subject_id).execute()
        subject_name = response.data[0]['name'] if response.data else "неизвестный предмет"
        
        await callback.message.answer(f"Выбран предмет: {subject_name}\n")
        await callback.message.answer(f"Введите задание:")
        await state.set_state(HomeWork.entering_task)
        
    except Exception as e:
        await callback.message.answer("Ошибка при получении данных о предмете")
        print(f"Error getting subject name: {e}")
        await state.clear()
    
    await callback.answer()


@router.message(HomeWork.entering_task)
async def task_entered(message: Message, state: FSMContext):
    """Inserting deadline of the hw"""

    await state.update_data(task=message.text)
    await message.answer("Введите дедлайн в формате ДД.ММ.ГГГГ")
    await state.set_state(HomeWork.entering_deadline)


@router.message(HomeWork.entering_deadline)
async def deadline_entered(message: Message, state: FSMContext):
    """Inserting hw into BD"""


    try:
        deadline = datetime.strptime(message.text, "%d.%m.%Y").date()
        if deadline < datetime.now().date():
            await message.answer("Дедлайн не может быть в прошлом! Введите корректную дату:")
            return
            
        data = await state.get_data()

        #print(f'DATA_INSERT = subject_id: {int(data['subject_id'])},task: {str(data['task'])}, deadline: {deadline.isoformat()}, user_id: {str(message.from_user.id)}')
        
        CLIENT.table('homework').insert({'subject_id': int(data['subject_id']),'description': str(data['task']),
            'due_date': deadline.isoformat(),
            'is_completed': False,
            'tg_id': str(message.from_user.id)}).execute()
        
        await message.answer("ДЗ успешно добавлено!")
        await state.set_state(Registration.passed) # После добавления ДЗ возвращаемся в начальное состояние. Пользователь зареган и может давать команды
        
    except ValueError:
        await message.answer("Неверный формат даты! Введите в формате ДД.ММ.ГГГГ:")



@router.callback_query(HomeWork.choosing_action, F.data == "view_hw")
async def view_homeworks_start(callback: CallbackQuery, state: FSMContext):
    try:
        response = CLIENT.table('subjects').select('id, name').execute()
        subjects = response.data
        
        if not subjects:
            await callback.message.answer("В базе нет предметов.")
            return await state.clear()
            
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=subj['name'], callback_data=f"view_subject_{subj['id']}")] 
                for subj in subjects])
        
        await callback.message.answer("Выберите предмет для просмотра ДЗ:", reply_markup=keyboard)
        await state.set_state(HomeWork.viewing_homeworks)
        await callback.answer()
        
    except Exception as e:
        await callback.message.answer(f"Ошибка: {e}")
        await state.set_state(Registration.passed)

@router.callback_query(HomeWork.viewing_homeworks, F.data.startswith("view_subject_"))
async def show_homeworks(callback: CallbackQuery, state: FSMContext):
    subject_id = callback.data.split("_")[-1]
    
    try:
        subject_name = CLIENT.table('subjects').select('name').eq('id', subject_id).execute().data[0]['name']
            
        homeworks = CLIENT.table('homework').select('description, due_date').eq('subject_id', subject_id).order('due_date').execute().data
            
        if not homeworks:
            await callback.message.answer(f"По предмету {subject_name} нет домашних заданий.")
        else:
            hw_list = "\n\n".join(f"Описание задания: {hw['description']}\n"
                f"Дедлайн: {datetime.fromisoformat(hw['due_date']).strftime('%d.%m.%Y')}" for hw in homeworks)
            
            await callback.message.answer(f"Домашние задания по предмету {subject_name}:\n\n{hw_list}")
            
        await state.set_state(Registration.passed)
        await callback.answer()
    except Exception as e:
        await callback.message.answer(f"Ошибка: {e}")
        await state.set_state(Registration.passed)

