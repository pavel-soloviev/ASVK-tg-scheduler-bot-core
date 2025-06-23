import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, User, Chat

# Мокируем ДО импорта хендлеров
with patch('Bot.handlers.config') as mock_config:
    mock_config.url.get_secret_value.return_value = "mock_url"
    mock_config.key.get_secret_value.return_value = "mock_key"
    from Bot.handlers import command_start_handler

@pytest.fixture(autouse=True)
def auto_mock_config():
    with patch('Bot.handlers.config') as mock_config:
        mock_config.url.get_secret_value.return_value = "mock_url"
        mock_config.key.get_secret_value.return_value = "mock_key"
        yield mock_config

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
    return msg

@pytest.mark.asyncio
async def test_start_command(message, bot, auto_mock_config):
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