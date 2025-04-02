"""Inline and reply keyboards for tg bot commands."""

# from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


async def create_shedule_kb():
    """Create inline keyboard for command /shedule."""
    Days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    kb = InlineKeyboardBuilder()
    for day in Days:
        kb.add(InlineKeyboardButton(text=day, callback_data=f"{day}_shedule"))
    return kb.adjust(2).as_markup()
