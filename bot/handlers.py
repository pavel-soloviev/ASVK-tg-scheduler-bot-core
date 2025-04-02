"""Handlers for our bot."""

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
import cowsay

HELP_COMMAND = """
/start - начать работу с ботом
/help - список команд
"""

START_COMMAND = "Здорово бродяга!"

router = Router()


@router.message(Command("help"))
async def help_command(message: Message):
    """Answer command /help."""
    await message.reply(text=HELP_COMMAND)


@router.message(Command("start"))
async def start_command(message: Message):
    """Answer command start."""
    await message.answer(cowsay.cowsay(message=START_COMMAND, cow="dragon"))
