"""Handlers for our bot."""

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

HELP_COMMAND = """
/start - начать работу с ботом
/help - список команд
"""

START_COMMAND = "Добро пожаловать в бот для ленивых АСВКшников!"

router = Router()


@router.message(Command("help"))
async def help_command(message: Message):
    """Answer command /help."""
    await message.reply(text=HELP_COMMAND)


@router.message(Command("start"))
async def start_command(message: Message):
    """Answer command start."""
    await message.answer(text=START_COMMAND)
