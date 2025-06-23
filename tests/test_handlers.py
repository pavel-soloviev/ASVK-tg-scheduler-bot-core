import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, User, Chat

@pytest.fixture
def storage():
    return MemoryStorage()

@pytest.fixture
def bot():
    mock = AsyncMock()
    # Настройка базовых методов бота
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
    msg.answer = AsyncMock()  # Имитируем метод answer
    return msg

@pytest.fixture
def callback_query():
    cbq = MagicMock(spec=CallbackQuery)
    cbq.from_user = MagicMock(spec=User)
    cbq.from_user.id = 123
    cbq.from_user.username = "test_user"
    cbq.message = message()  # Используем фикстуру message
    cbq.answer = AsyncMock()
    return cbq