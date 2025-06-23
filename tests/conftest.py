import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram_test import MockedBot
from bot.handlers import *

@pytest.fixture
def bot():
    return MockedBot()

@pytest.fixture
def mock_supabase():
    mock = MagicMock()
    # Мокируем стандартные ответы Supabase
    mock.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    return mock