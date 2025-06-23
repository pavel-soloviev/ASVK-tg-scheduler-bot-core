import pytest
from src.handlers import command_start_handler, registration
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_start_command(bot):
    message = AsyncMock(text="/start")
    await command_start_handler(message, AsyncMock())
    assert "Привет" in bot.last_message.text
    assert "Регистрация" in bot.last_message.reply_markup.inline_keyboard[0][0].text

@pytest.mark.asyncio
async def test_registration_flow(bot, mock_supabase):
    callback = AsyncMock(data="registration")
    await registration(callback, AsyncMock())
    
    # Проверяем запрос имени
    assert "Введите ваше ФИО" in bot.last_message.text