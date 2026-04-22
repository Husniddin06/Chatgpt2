import asyncio
import logging
import sys
import os

# PYTHONPATH ni to'g'rilash
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

try:
    from config import BOT_TOKEN
    from database.db import init_db, init_extras
    from handlers.user_handlers import user_router
    from handlers.admin_handlers import admin_router
    from utils.scheduler import start_scheduler
except ImportError:
    from bot.config import BOT_TOKEN
    from bot.database.db import init_db, init_extras
    from bot.handlers.user_handlers import user_router
    from bot.handlers.admin_handlers import admin_router
    from bot.utils.scheduler import start_scheduler


async def set_commands(bot: Bot):
    await bot.set_my_commands([
        BotCommand(command="start", description="🚀 Boshlash"),
        BotCommand(command="help", description="🆘 Yordam"),
        BotCommand(command="image", description="🎨 Rasm yaratish"),
        BotCommand(command="search", description="🔎 Internetdan qidirish"),
        BotCommand(command="stats", description="📊 Mening hisobim"),
        BotCommand(command="bonus", description="🎁 Kunlik bonus"),
        BotCommand(command="ref", description="👥 Do'stlarni taklif qilish"),
        BotCommand(command="lang", description="🌐 Tilni o'zgartirish"),
        BotCommand(command="promo", description="🎟 Promo-kod"),
        BotCommand(command="premium", description="💎 Premium sotib olish"),
        BotCommand(command="clear", description="🗑 Suhbat tarixini tozalash"),
    ])

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Bot ishga tushmoqda...")
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN topilmadi! Railway Variables bo'limini tekshiring.")
        return
    try:
        await init_db()
        await init_extras()
        start_scheduler()

        bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        dp = Dispatcher()
        dp.include_router(user_router)
        dp.include_router(admin_router)

        await bot.delete_webhook(drop_pending_updates=True)
        await set_commands(bot)
        logger.info("Bot muvaffaqiyatli ishga tushdi.")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Kritik xatolik: {e}")

if __name__ == "__main__":
    asyncio.run(main())
