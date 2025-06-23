import pytest

from aiogram import F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, User, Chat
from aiogram_tests.aiogram_tests.mocked_bot import MockedBot
from aiogram_tests.aiogram_tests.handler import MessageHandler, CallbackQueryHandler
#from aiogram_tests.aiogram_tests.types import MESSAGE, CALLBACK_QUERY


from handlers import (
    router,
    command_start_handler,
    registration,
    fix_registration,
    process_name,
    wait,
    homework_menu,
    action_selected,
    subject_selected,
    task_entered,
    deadline_entered,
    view_homeworks_start,
    show_homeworks,
    set_day,
    monday,
    get_help,
    cmd_deadline,
    start_add_deadline,
    input_date,
    input_time,
    input_title,
    check_deadlines_list,
    HomeWork,
    Registration
)

@pytest.fixture
def storage():
    return MemoryStorage()

@pytest.fixture
def bot(storage):
    return MockedBot(handlers=[MessageHandler(router), CallbackQueryHandler(router)], storage=storage)

@pytest.fixture
def message():
    user = User(id=123, is_bot=False, first_name="Test", username="test_user")
    chat = Chat(id=123, type="private")
    return Message(message_id=1, from_user=user, chat=chat, date=None, text="")

@pytest.fixture
def callback_query():
    user = User(id=123, is_bot=False, first_name="Test", username="test_user")
    message = Message(message_id=1, from_user=user, chat=Chat(id=123, type="private"), date=None, text="")
    return CallbackQuery(id="1", from_user=user, message=message, chat_instance="1", data="")

@pytest.mark.asyncio
async def test_start_command(bot, message):
    message.text = "/start"
    message.entities = [{"type": "bot_command", "offset": 0, "length": 6}]
    
    calls = await bot.feed(message)
    answer = calls.send_message.fetchone().text
    assert "Привет! Я бот 321 группы." in answer
    assert "Регистрация" in answer.text  # Проверяем наличие кнопки регистрации

@pytest.mark.asyncio
async def test_registration_callback(bot, callback_query):
    callback_query.data = "registration"
    
    calls = await bot.feed(callback_query)
    answer = calls.send_message.fetchone().text
    assert "Введите ваше ФИО:" in answer

@pytest.mark.asyncio
async def test_process_name(bot, message, storage):
    # Устанавливаем состояние для имитации процесса регистрации
    context = FSMContext(storage, bot, "123", "123")
    await context.set_state(Registration.name)
    
    message.text = "Иванов Иван Иванович"
    
    calls = await bot.feed(message)
    answer = calls.send_message.fetchone().text
    assert "Отлично!" in answer
    
    # Проверяем, что состояние очищено
    state = await context.get_state()
    assert state is None

@pytest.mark.asyncio
async def test_homework_menu(bot, message, storage):
    # Устанавливаем состояние, что пользователь зарегистрирован
    context = FSMContext(storage, bot, "123", "123")
    await context.set_state(Registration.passed)
    
    message.text = "/hw"
    message.entities = [{"type": "bot_command", "offset": 0, "length": 3}]
    
    calls = await bot.feed(message)
    answer = calls.send_message.fetchone().text
    assert "Выберите действие:" in answer
    assert "Добавить ДЗ" in answer.text
    assert "Посмотреть ДЗ" in answer.text

@pytest.mark.asyncio
async def test_homework_flow(bot, callback_query, storage):
    # Тестируем полный flow добавления ДЗ
    
    # 1. Выбираем действие "Добавить ДЗ"
    context = FSMContext(storage, bot, "123", "123")
    await context.set_state(HomeWork.choosing_action)
    callback_query.data = "add_hw"
    
    calls = await bot.feed(callback_query)
    answer = calls.send_message.fetchone().text
    assert "Выберите предмет:" in answer
    
    # 2. Выбираем предмет (имитируем callback с data="subject_1")
    callback_query.data = "subject_1"
    calls = await bot.feed(callback_query)
    answer = calls.send_message.fetchone().text
    assert "Выбран предмет:" in answer
    assert "Введите задание:" in answer
    
    # 3. Вводим задание (имитируем сообщение)
    message = callback_query.message
    message.text = "Тестовое задание"
    context = FSMContext(storage, bot, "123", "123")
    await context.set_state(HomeWork.entering_task)
    
    calls = await bot.feed(message)
    answer = calls.send_message.fetchone().text
    assert "Введите дедлайн в формате ДД.ММ.ГГГГ" in answer
    
    # 4. Вводим дедлайн
    message.text = "31.12.2023"
    await context.set_state(HomeWork.entering_deadline)
    
    calls = await bot.feed(message)
    answer = calls.send_message.fetchone().text
    assert "ДЗ успешно добавлено!" in answer

@pytest.mark.asyncio
async def test_schedule_command(bot, message):
    message.text = "/schedule"
    message.entities = [{"type": "bot_command", "offset": 0, "length": 9}]
    
    calls = await bot.feed(message)
    answer = calls.send_message.fetchone().text
    assert "Выбери день недели" in answer
    assert "Понедельник" in answer.text

@pytest.mark.asyncio
async def test_monday_schedule(bot, callback_query):
    callback_query.data = "monday"
    
    calls = await bot.feed(callback_query)
    answer = calls.send_message.fetchone().text
    assert "Расписание на понедельник" in answer or "В этот день нет пар." in answer

@pytest.mark.asyncio
async def test_help_command(bot, message):
    message.text = "/help"
    message.entities = [{"type": "bot_command", "offset": 0, "length": 5}]
    
    calls = await bot.feed(message)
    answer = calls.send_message.fetchone().text
    assert "/schedule" in answer
    assert "/hw" in answer

@pytest.mark.asyncio
async def test_deadlines_command(bot, message):
    message.text = "/deadlines"
    message.entities = [{"type": "bot_command", "offset": 0, "length": 10}]
    
    calls = await bot.feed(message)
    answer = calls.send_message.fetchone().text
    assert "Здесь можно настроить или узнать текущие дедлайны" in answer
    assert "Создать" in answer.text
    assert "Посмотреть список" in answer.text

@pytest.mark.asyncio
async def test_deadline_creation_flow(bot, message, callback_query, storage):
    # 1. Начинаем создание дедлайна
    callback_query.data = "create"
    calls = await bot.feed(callback_query)
    answer = calls.edit_message_text.fetchone().text
    assert "Введите дату дедлайна в формате YYYY-MM-DD" in answer
    
    # 2. Вводим дату
    message.text = "2023-12-31"
    context = FSMContext(storage, bot, "123", "123")
    await context.set_state(AddDeadline.waiting_for_date)
    
    calls = await bot.feed(message)
    answer = calls.send_message.fetchone().text
    assert "Теперь введите время дедлайна в формате HH:MM" in answer
    
    # 3. Вводим время
    message.text = "23:59"
    await context.set_state(AddDeadline.waiting_for_time)
    
    calls = await bot.feed(message)
    answer = calls.send_message.fetchone().text
    assert "Теперь введите название дедлайна" in answer
    
    # 4. Вводим название
    message.text = "Тестовый дедлайн"
    await context.set_state(AddDeadline.waiting_for_title)
    
    calls = await bot.feed(message)
    answer = calls.send_message.fetchone().text
    assert "Дедлайн «Тестовый дедлайн» добавлен" in answer