@pytest.mark.asyncio
async def test_homework_menu(bot):
    message = AsyncMock(text="/hw")
    await homework_menu(message, AsyncMock())
    
    keyboard = bot.last_message.reply_markup.inline_keyboard
    assert "Добавить ДЗ" in keyboard[0][0].text
    assert "Посмотреть ДЗ" in keyboard[0][1].text

@pytest.mark.asyncio
async def test_add_homework_flow(bot, mock_supabase):
    # Мокируем ответ Supabase с предметами
    mock_supabase.table.return_value.select.return_value.execute.return_value.data = [
        {"id": 1, "name": "Математика"}
    ]
    
    callback = AsyncMock(data="add_hw")
    state = AsyncMock()
    await action_selected(callback, state)
    
    assert "Выберите предмет" in bot.last_message.text
    assert "Математика" in bot.last_message.reply_markup.inline_keyboard[0][0].text