import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, User, Chat, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import pytz
import random
import string


with patch('Bot.handlers.config') as mock_config, \
     patch('Bot.handlers.sb') as mock_sb:
    mock_config.url.get_secret_value.return_value = "mock_url"
    mock_config.key.get_secret_value.return_value = "mock_key"
    mock_client = AsyncMock()
    mock_sb.create_client.return_value = mock_client
    from Bot.handlers import (
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
        Registration,
        HomeWork,
        AddDeadline
    )

@pytest.fixture(autouse=True)
def auto_mock_config_and_db():
    with patch('Bot.handlers.config') as mock_config, \
         patch('Bot.handlers.sb') as mock_sb:
        mock_config.url.get_secret_value.return_value = "mock_url"
        mock_config.key.get_secret_value.return_value = "mock_key"
        mock_client = AsyncMock()
        mock_sb.create_client.return_value = mock_client
        yield mock_config, mock_client

@pytest.fixture
async def fsm_context(bot):
    """Фикстура с синхронным доступом к состоянию"""
    storage = MemoryStorage()
    context = FSMContext(storage=storage, bot=bot, user_id=123, chat_id=123)
    
    # Добавляем синхронные методы для тестирования
    async def get_current_state():
        return await storage.get_state(key=context.key)
    
    async def get_current_data():
        return await storage.get_data(key=context.key)
    
    context.get_current_state = get_current_state
    context.get_current_data = get_current_data
    
    return context

@pytest.fixture
def storage():
    return MemoryStorage()

@pytest.fixture
def bot():
    mock = AsyncMock()
    mock.send_message = AsyncMock()
    mock.edit_message_text = AsyncMock()
    return mock

def message(id=1, user_name='123456789', text='Somebody', msg='Some text'):
    msg = MagicMock(spec=Message)
    msg.from_user = MagicMock(spec=User)
    msg.from_user.id = id
    msg.from_user.username=user_name
    msg.answer = AsyncMock()
    msg.text = text
    msg.message = msg
    return msg


def callback(id="123abc", data="button_1", user_id=111, user_name='Somebody'):
    """Мок CallbackQuery с базовой функциональностью"""
    mock_callback = MagicMock(spec=CallbackQuery)
    mock_callback.id = id  # ID callback-запроса
    mock_callback.data = data # Данные кнопки
    mock_callback.from_user = MagicMock()  # Мокаем пользователя
    mock_callback.from_user.id = user_id  # Telegram ID пользователя
    mock_callback.from_user.username = user_name
    mock_callback.message = MagicMock()
    mock_callback.message.answer = AsyncMock()
    
    return mock_callback



@pytest.mark.asyncio
async def test_start_command():

    msg = message()
    mock_state = AsyncMock(spec=FSMContext)

    await command_start_handler(msg, mock_state)

    msg.answer.assert_called_once()
    args, kwargs = msg.answer.call_args
    assert 'Привет! Я бот 321 группы' in args[0]
    assert "Регистрация" in str(kwargs['reply_markup'])


@pytest.mark.asyncio
async def test_registration_1():
    """Имитируем работу функции registration с дефолтными параметрами пользователя, которые есть в БД
    Ожидаемый результат - пользователю выводится сообщение о том, что он уже зарегистрирован"""

    mock_callback = callback()
    mock_state = AsyncMock(spec=FSMContext)
    await registration(mock_callback, mock_state)
    args, kwargs = mock_callback.message.answer.call_args
    assert 'Вы уже зарегестрированы со следующими данными.' in args[0]


@pytest.mark.asyncio
async def test_registration_2():
    """Имитируем работу функции registration с нестандартными параметрами пользователя, которых нет в БД
    Ожидаемый результат - пользователю выводится сообщение с просьбой пройти регистрацию"""

    mock_callback = callback(user_name=''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase) for _ in range(10)))
    mock_state = AsyncMock(spec=FSMContext)
    await registration(mock_callback, mock_state)
    args, kwargs = mock_callback.message.answer.call_args
    assert 'Введите ваше ФИО:' in args[0]
    mock_state.set_state.assert_called_once_with(Registration.name)


@pytest.mark.asyncio
async def test_fix_registration_command():
    """Пользователь с обычными параметрами удаляется из БД и бот просит ввести фио"""

    mock_callback = callback()
    mock_state = AsyncMock(spec=FSMContext)
    await fix_registration(mock_callback, mock_state)
    mock_callback.message.answer.assert_called_once_with('Введите ваше ФИО:')



@pytest.mark.asyncio
async def test_process_name_command():
    
    msg = message()
    mock_state = AsyncMock(spec=FSMContext)

    await process_name(msg, mock_state)
    msg.answer.assert_called_once()
    args, kwargs = msg.answer.call_args
    assert 'Отлично!' == args[0]


@pytest.mark.asyncio
async def test_homework_menu_command():
    
    msg = message()
    mock_state = AsyncMock(spec=FSMContext)

    await homework_menu(
        msg, 
        mock_state
    )
    msg.answer.assert_called_once()
    args, kwargs = msg.answer.call_args
    assert 'Выберите' in args[0]


@pytest.mark.asyncio
async def test_task_entered_command():
    
    msg = message()
    mock_state = AsyncMock(spec=FSMContext)
    
    await task_entered(msg, mock_state)
    msg.answer.assert_called_once()
    args, kwargs = msg.answer.call_args
    assert 'Введите дедлайн в формате' in args[0]


@pytest.mark.asyncio
async def test_deadline_entered_command():

    msg = message()
    mock_state = AsyncMock(spec=FSMContext)

    await deadline_entered(msg, mock_state)
    msg.answer.assert_called_once()
    args, kwargs = msg.answer.call_args
    assert 'ДЗ успешно добавлено!' in args[0] or 'Неверный формат даты! Введите в формате ДД.ММ.ГГГГ:' in args[0]



'''



@pytest.mark.asyncio
async def test_homework_flow(callback_query, message, auto_mock_config_and_db):
    _, mock_client = auto_mock_config_and_db
    
    # 1. Пользователь вводит /hw
    message.text = "/hw"
    state = FSMContext(storage=MemoryStorage(), key='')
    await state.set_state(Registration.passed)
    
    mock_client.table.return_value.select.return_value.execute.return_value.data = [
        {"id": 1, "name": "Математика"}
    ]
    
    await homework_menu(message, state)
    message.answer.assert_called_once()
    assert "Выберите действие:" in message.answer.call_args[0][0]
    
    # 2. Пользователь выбирает "Добавить ДЗ"
    callback_query.data = "add_hw"
    await action_selected(callback_query, state)
    callback_query.message.answer.assert_called_once_with("Выберите предмет:")
    
    # 3. Пользователь выбирает предмет
    callback_query.data = "subject_1"
    await subject_selected(callback_query, state)
    assert "Выбран предмет:" in callback_query.message.answer.call_args[0][0]
    assert "Введите задание:" in callback_query.message.answer.call_args[1]['text']
    
    # 4. Пользователь вводит задание
    message.text = "Решить задачи 1-5"
    await task_entered(message, state)
    message.answer.assert_called_once_with("Введите дедлайн в формате ДД.ММ.ГГГГ")
    
    # 5. Пользователь вводит дедлайн
    message.text = "31.12.2023"
    await deadline_entered(message, state)
    message.answer.assert_called_once_with("ДЗ успешно добавлено!")





@pytest.mark.asyncio
async def test_registration_flow(callback_query, auto_mock_config_and_db, fsm_context):
    _, mock_client = auto_mock_config_and_db
    
    # 1. Пользователь нажимает кнопку "Регистрация"
    callback_query.data = "registration"
    mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    
    a = FSMContext(storage=MemoryStorage(), key='state')
    registration(callback_query, a)

    print(f'AAAAAAAAAAAAA = {await a.storage.get_state(key='state')}')

    #storage.get_state(key=fsm_context.key)
    assert a.get_state == Registration.name.state

    
    # Проверяем запрос ввода ФИО
    #callback_query.message.answer.assert_called_once_with("Введите ваше ФИО:")
    
    # 2. Пользователь вводит ФИО
    message = callback_query.message
    message.text = "Иванов Иван Иванович"
    await process_name(message, fsm_context)
    
    # Проверяем успешную регистрацию
    #print('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
    #message.answer.assert_called_once_with("Отлично!")
    #mock_client.table.return_value.insert.assert_called_once_with({
    #    "tg_id": "123",
    #    "name": "Иванов Иван Иванович",
    #    "tg_username": "test_user"
    #})
    '''