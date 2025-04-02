"""Script file that runs tg bot."""

import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv


HELP_COMMAND = """
/start - начать работу с ботом
/help - список команд
"""

START_COMMAND = "Добро пожаловать в бот для ленивых АСВКшников!"


async def help_command(message: types.Message):
    """Answer command /help."""
    await message.reply(text=HELP_COMMAND)


async def start_command(message: types.Message):
    """Answer command start."""
    await message.answer(text=START_COMMAND)


async def main():
    """Start bot and print logs."""
    load_dotenv()
    TOKEN = os.getenv("TG_BOT_TOKEN")

    if not TOKEN:
        raise ValueError("The token was not found! Check .env file")

    bot = Bot(TOKEN)
    dp = Dispatcher()

    logging.basicConfig(level=logging.INFO)
    dp.message.register(start_command, Command("start"))
    dp.message.register(help_command, Command("help"))

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
