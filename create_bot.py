from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import os
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode


load_dotenv(override=True)

scheduler = AsyncIOScheduler()
storage = MemoryStorage()

bot = Bot(token=os.getenv('BOT_TOKEN'), 
          default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher(storage=storage)