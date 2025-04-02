"""Handlers for our bot."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import cowsay

import keyboards

HELP_COMMAND = """
/start - начать работу с ботом
/help - список команд
/shedule - расписание занятий
"""

START_COMMAND = "Здорово бродяга!"

Shedule_dict = {"Monday": """10:30 - 12:05  Формалки
                12:50 - 14:25  Прак
                16:20 - 17:55  Сети Курячего)
                """,
                "Tuesday": "В разработке)",
                "Wednesday": "В разработке)",
                "Thursday": "В разработке)",
                "Friday": "В разработке)",
                }

router = Router()


@router.message(Command("help"))
async def help_command(message: Message):
    """Answer command /help."""
    await message.reply(text=HELP_COMMAND)


@router.message(Command("start"))
async def start_command(message: Message):
    """Answer command start."""
    await message.answer(cowsay.cowsay(message=START_COMMAND, cow="dragon"))


@router.message(Command("shedule"))
async def shedule_command(message: Message):
    """Answer command shedule."""
    await message.answer(text="Расписание занятий", reply_markup=await keyboards.create_shedule_kb())


@router.callback_query(F.data.endswith("_shedule"))
async def shedule_per_day(callback: CallbackQuery):
    """Rerutn shedule for particular day."""
    print(callback.data)
    await callback.answer('')
    day = callback.data.split('_')[0]
    await callback.message.answer(Shedule_dict[day])
