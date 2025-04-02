"""Script file that runs tg bot."""

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from handlers import router


async def main():
    """Start bot and print logs."""
    load_dotenv()
    TOKEN = os.getenv("TG_BOT_TOKEN")

    if not TOKEN:
        raise ValueError("The token was not found! Check .env file")

    bot = Bot(TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    logging.basicConfig(level=logging.INFO)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
