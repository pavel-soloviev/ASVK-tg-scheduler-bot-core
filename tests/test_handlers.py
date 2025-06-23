import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, User, Chat, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import pytz

# Мокируем ДО импорта хендлеров
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
    cbq.from_user = message.from_user
    cbq.message = message
    cbq.answer = AsyncMock()
    cbq.data = ""
    return cbq



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
async def test_registration_flow(callback_query, auto_mock_config_and_db, fsm_context):
    _, mock_client = auto_mock_config_and_db
    
    # 1. Пользователь нажимает кнопку "Регистрация"
    callback_query.data = "registration"
    mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    
    await registration(callback_query, fsm_context)

    print(fsm_context.get_current_state())
    assert fsm_context.get_current_state() == Registration.name.state

    
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
