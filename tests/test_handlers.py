"""Tests for handlers."""

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


def message(id=1, user_name='Somebody', text='Mario', msg='Some text'):
    msg = MagicMock(spec=Message)
    msg.from_user = MagicMock(spec=User)
    msg.from_user.id = id
    msg.from_user.username = user_name
    msg.answer = AsyncMock()
    msg.text = text
    msg.message = msg
    return msg


def callback(id="123abc", data="button_1", user_id=111, user_name='Somebody', text='Some text'):
    """Мок CallbackQuery с базовой функциональностью"""
    mock_callback = MagicMock(spec=CallbackQuery)
    mock_callback.id = id  # ID callback-запроса
    mock_callback.data = data  # Данные кнопки
    mock_callback.from_user = MagicMock()  # Мокаем пользователя
    mock_callback.from_user.id = user_id  # Telegram ID пользователя
    mock_callback.from_user.username = user_name
    mock_callback.message = MagicMock()
    mock_callback.message.answer = AsyncMock()
    mock_callback.message.edit_text = AsyncMock()
    mock_callback.answer = AsyncMock()

    return mock_callback


@pytest.mark.asyncio
async def test_start_command():

    msg = message()
    mock_state = AsyncMock(spec=FSMContext)

    await command_start_handler(msg, mock_state)

    msg.answer.assert_called_once()
    args, kwargs = msg.answer.call_args
    assert 'Choose language.' == args[0]



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
    """Ожидаемый результат работы функции - пользователь добавлен в БД и выведена соответствующая команда"""

    msg = message()
    mock_state = AsyncMock(spec=FSMContext)
    await process_name(msg, mock_state)
    msg.answer.assert_called_once()
    args, kwargs = msg.answer.call_args
    assert 'Отлично!' == args[0]


@pytest.mark.asyncio
async def test_wait_command():

    mock_callback = callback()
    mock_state = AsyncMock(spec=FSMContext)
    await wait(mock_callback, mock_state)
    mock_callback.message.answer.assert_called_once_with('Отлично!')
    mock_state.set_state.assert_called_once_with(Registration.passed)


@pytest.mark.asyncio
async def test_homework_menu_command():
    """Проверка меню выбора ДЗ
    Ожидается сообщение от бота с предложением нажать на кнопки с определенным текстом"""

    msg = message()
    mock_state = AsyncMock(spec=FSMContext)
    await homework_menu(msg, mock_state)
    msg.answer.assert_called_once()
    args, kwargs = msg.answer.call_args
    assert 'Выберите действие:' == args[0]
    assert 'Добавить ДЗ' == kwargs['reply_markup'].inline_keyboard[0][0].text
    assert 'Посмотреть ДЗ' == kwargs['reply_markup'].inline_keyboard[1][0].text


@pytest.mark.asyncio
async def test_action_selected_command():
    """Проверка функции выбора действия
    Ожидаемый результат - появилась кнопка с предметами, изменилось состояние машины"""

    mock_callback = callback()
    mock_state = AsyncMock(spec=FSMContext)
    await action_selected(mock_callback, mock_state)
    args, kwargs = mock_callback.message.answer.call_args
    assert 'Выберите предмет:' == args[0]
    mock_state.set_state.assert_called_once_with(HomeWork.selecting_subject)
    mock_callback.answer.assert_called()


@pytest.mark.asyncio
async def test_task_entered_command():

    msg = message()
    mock_state = AsyncMock(spec=FSMContext)

    await task_entered(msg, mock_state)
    msg.answer.assert_called_once()
    args, kwargs = msg.answer.call_args
    assert 'Введите дедлайн в формате ДД.ММ.ГГГГ' == args[0]
    mock_state.set_state.assert_called_once_with(HomeWork.entering_deadline)


@pytest.mark.asyncio
async def test_deadline_entered_command_1():
    """Положительный тест-кейс ввода данных от пользователя о дедлайне домашнего задания
    Ожидаемый результат - успешное добавление ДЗ и изменение состояния машины на зарегистрированного пользователя"""

    msg = message(text='12.12.2025')
    mock_state = AsyncMock(spec=FSMContext)

    await deadline_entered(msg, mock_state)
    msg.answer.assert_called_once()
    args, kwargs = msg.answer.call_args
    assert 'ДЗ успешно добавлено!' == args[0]
    mock_state.set_state.assert_called_once_with(Registration.passed)


@pytest.mark.asyncio
async def test_deadline_entered_command_2():
    """Ложный тест-кейс ввода данных от пользователя о дедлайне домашнего задания из прошлого
    Ожидаемый результат - уведомление пользователя о проблеме"""

    msg = message(text='12.12.2024')
    mock_state = AsyncMock(spec=FSMContext)

    await deadline_entered(msg, mock_state)
    msg.answer.assert_called_once()
    args, kwargs = msg.answer.call_args
    assert 'Дедлайн не может быть в прошлом! Введите корректную дату:' == args[0]


@pytest.mark.asyncio
async def test_deadline_entered_command_3():
    """Ложный тест-кейс ввода данных от пользователя: некорректный формат данных от пользователя
    Ожидаемый результат - уведомление пользователя о проблеме"""

    msg = message(text='It is not a date')
    mock_state = AsyncMock(spec=FSMContext)

    await deadline_entered(msg, mock_state)
    msg.answer.assert_called_once()
    args, kwargs = msg.answer.call_args
    assert 'Неверный формат даты! Введите в формате ДД.ММ.ГГГГ:' == args[0]


@pytest.mark.asyncio
async def test_set_day_command():
    """Проверка команды расписания
    Ожидается сообщение с выбором конкретных кнопок с определенным текстом"""

    msg = message()
    mock_state = AsyncMock(spec=FSMContext)
    await set_day(msg, mock_state)
    msg.answer.assert_called_once()
    args, kwargs = msg.answer.call_args
    assert 'Выбери день недели' == args[0]
    assert 'Понедельник' == kwargs['reply_markup'].inline_keyboard[0][0].text
    assert 'Вторник' == kwargs['reply_markup'].inline_keyboard[1][0].text
    assert 'Среда' == kwargs['reply_markup'].inline_keyboard[2][0].text
    assert 'Четверг' == kwargs['reply_markup'].inline_keyboard[3][0].text
    assert 'Пятница' == kwargs['reply_markup'].inline_keyboard[4][0].text


@pytest.mark.asyncio
async def test_get_help_command():
    """Проверка команды помощи
    Ожидается сообщение с описанием возможных команд"""

    msg = message()
    mock_state = AsyncMock(spec=FSMContext)
    await get_help(msg, mock_state)
    msg.answer.assert_called_once()
    args, kwargs = msg.answer.call_args
    assert '/schedule - просмотр расписания,' in args[0]


@pytest.mark.asyncio
async def test_cmd_deadline_command():
    """Проверка команды дедлайнов
    Ожидается сообщение с информационным выводом и текстом на кнопках"""

    msg = message()
    await cmd_deadline(msg, None)
    msg.answer.assert_called_once()
    args, kwargs = msg.answer.call_args
    assert 'Здесь можно настроить или узнать текущие дедлайны' in args[0]
    assert 'Создать' == kwargs['reply_markup'].inline_keyboard[0][0].text
    assert 'Посмотреть список' == kwargs['reply_markup'].inline_keyboard[0][1].text


@pytest.mark.asyncio
async def test_start_add_deadline_command():
    """Проверка функции создания нового дедлайна
    Ожидаемый результат - вывод сообщения с предложением ввести дату"""

    mock_callback = callback()
    mock_state = AsyncMock(spec=FSMContext)
    await start_add_deadline(mock_callback, mock_state)
    args, kwargs = mock_callback.message.edit_text.call_args
    assert 'Введите дату дедлайна в формате YYYY-MM-DD' == args[0]
    mock_state.set_state.assert_called_once_with(AddDeadline.waiting_for_date)


@pytest.mark.asyncio
async def test_input_time_command():
    """Проверка команды дедлайнов с неверным форматом времени
    Ожидается сообщение с информационным выводом и текстом на кнопках"""

    msg = message(text='No time for this')
    mock_state = AsyncMock(spec=FSMContext)
    await input_time(msg, mock_state)
    msg.answer.assert_called_once()
    args, kwargs = msg.answer.call_args
    assert 'Неверный формат. Введите время как HH:MM' == args[0]
