import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, User, Chat, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import pytz


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
def fsm_context():
    """Улучшенный мок FSMContext с сохранением состояния"""
    class MockFSMContext:
        def __init__(self):
            self._storage = {}  # Хранилище состояний
            self._current_state = None
            self._current_data = {}
        
        async def get_state(self):
            return self._current_state
        
        async def set_state(self, state):
            self._current_state = state
        
        async def get_data(self):
            return self._current_data.copy()
        
        async def set_data(self, data: dict):
            self._current_data = data.copy()
        
        async def update_data(self, data: dict):
            self._current_data.update(data)
            return self._current_data.copy()
        
        async def update_data(self, task):
            self._current_data.update(task)
            return self._current_data.copy()
        
        async def clear(self):
            self._current_state = None
            self._current_data = {}
        
        # Синхронные методы для тестирования
        def get_current_state(self):
            return self._current_state
        
        def get_current_data(self):
            return self._current_data.copy()
        
        def print_state(self):  # Для отладки
            print(f"State: {self._current_state}, Data: {self._current_data}")

    return MockFSMContext()

@pytest.fixture
def storage():
    return MemoryStorage()

@pytest.fixture
def bot():
    mock = AsyncMock()
    mock.send_message = AsyncMock()
    mock.edit_message_text = AsyncMock()
    return mock

@pytest.fixture
def message():
    msg = MagicMock(spec=Message)
    msg.from_user = MagicMock(spec=User)
    msg.from_user.id = 123
    msg.from_user.username = "test_user"
    msg.chat = MagicMock(spec=Chat)
    msg.chat.id = 123
    msg.answer = AsyncMock()
    msg.text = ""
    return msg


@pytest.fixture
def callback_query(message):
    cbq = MagicMock(spec=CallbackQuery)
    #cbq.from_user.username = message.from_user
    #cbq.message = message
    #cbq.answer = AsyncMock()
    #cbq.data = ""
    return CallbackQuery



@pytest.mark.asyncio
async def test_start_command(message, bot, auto_mock_config_and_db):
    await command_start_handler(
        message, 
        None
    )
    message.answer.assert_called_once()
    args, kwargs = message.answer.call_args
    #print(f'args = {args}')
    #print(kwargs)
    assert 'Привет! Я бот 321 группы' in args[0]
    assert "Регистрация" in str(kwargs['reply_markup'])


@pytest.mark.asyncio
async def test_process_name_command(message, fsm_context):
    await process_name(
        message, 
        fsm_context
    )
    message.answer.assert_called_once()
    args, kwargs = message.answer.call_args
    assert 'Отлично' in args[0]


@pytest.mark.asyncio
async def test_homework_menu_command(message, fsm_context):
    await homework_menu(
        message, 
        fsm_context
    )
    message.answer.assert_called_once()
    args, kwargs = message.answer.call_args
    assert 'Выберите' in args[0]


@pytest.mark.asyncio
async def test_task_entered_command(message, fsm_context):
    await task_entered(
        message, 
        fsm_context
    )
    message.answer.assert_called_once()
    args, kwargs = message.answer.call_args
    assert 'Введите дедлайн в формате' in args[0]


@pytest.mark.asyncio
async def test_deadline_entered_command(message, fsm_context):
    await deadline_entered(
        message, 
        fsm_context
    )
    message.answer.assert_called_once()
    args, kwargs = message.answer.call_args
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
'''


'''

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