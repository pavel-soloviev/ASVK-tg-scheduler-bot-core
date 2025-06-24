"""Initialize client run bot."""
import supabase as sb
import logging
import sys
import asyncio

from Bot.config import config
from Bot.handlers import router, _

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.client.default import DefaultBotProperties
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import pytz

TOKEN = config.bot_token.get_secret_value()


STORAGE = MemoryStorage()
dp = Dispatcher(storage=STORAGE)


URL = config.url.get_secret_value()
KEY = config.key.get_secret_value()
CLIENT = sb.create_client(URL, KEY)


async def reminder_worker():
    """Check dealines each 60 sec and remind."""
    while True:
        now = datetime.now(pytz.UTC)
        moscow_tz = pytz.timezone('Europe/Moscow')

        response = CLIENT.table("deadlines").select(
            "*").eq("notified", False).gt("deadline_at", now.isoformat()).execute()

        for row in response.data:
            deadline = datetime.fromisoformat(row["deadline_at"]).replace(tzinfo=pytz.UTC)
            delta = deadline - now

            if timedelta(minutes=0) < delta <= timedelta(minutes=1):
                text = (_("Напоминание!\n<b>{title}</b>\nДедлайн в ").format(title=row['title']) +
                        f"{deadline.astimezone(moscow_tz).strftime('%H:%M %d.%m.%Y')}")

                try:
                    await BOT.send_message(row["telegram_id"], text)
                    CLIENT.table("deadlines").update({"notified": True}).eq("id", row["id"]).execute()
                except Exception as e:
                    print(f"Ошибка отправки уведомления: {e}")

        await asyncio.sleep(60)


async def main() -> None:
    """Run bot."""
    dp.include_router(router)
    asyncio.create_task(reminder_worker())
    await dp.start_polling(BOT)

if __name__ == "__main__":
    BOT = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
