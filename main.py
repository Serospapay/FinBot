"""Головний файл запуску бота"""
import asyncio
import logging
import os
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import settings
from database import init_db
from handlers import register_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

LOCK_FILE = Path(__file__).parent / ".finbot.lock"


def check_another_instance() -> bool:
    """Перевірка чи вже запущений інший екземпляр бота"""
    if not LOCK_FILE.exists():
        return False
    try:
        pid = int(LOCK_FILE.read_text().strip())
        os.kill(pid, 0)
        return True
    except (ValueError, OSError, ProcessLookupError):
        LOCK_FILE.unlink(missing_ok=True)
        return False


def create_lock() -> None:
    """Створити lock-файл"""
    LOCK_FILE.write_text(str(os.getpid()))


def remove_lock() -> None:
    """Видалити lock-файл"""
    LOCK_FILE.unlink(missing_ok=True)


async def main() -> None:
    """Головна функція"""
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    if settings.REDIS_URL:
        try:
            from aiogram.fsm.storage.redis import RedisStorage

            storage = RedisStorage.from_url(settings.REDIS_URL)
            logger.info("Використовується Redis FSM storage")
        except ImportError:
            logger.warning("Пакет redis не встановлено. pip install redis")
            storage = MemoryStorage()
        except Exception as e:
            logger.warning("Redis недоступний, використовується Memory: %s", e)
            storage = MemoryStorage()
    else:
        storage = MemoryStorage()

    dp = Dispatcher(storage=storage)
    register_handlers(dp)

    await init_db()
    logger.info("База даних ініціалізована")
    commands = [
        BotCommand(command="start", description="Почати роботу"),
        BotCommand(command="menu", description="Головне меню"),
        BotCommand(command="balance", description="Мій баланс"),
        BotCommand(command="cancel", description="Скасувати поточну дію"),
        BotCommand(command="help", description="Довідка"),
    ]
    await bot.set_my_commands(commands)
    logger.info("Команди бота встановлено")

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Бот запущено успішно")
    await dp.start_polling(bot)


if __name__ == "__main__":
    if check_another_instance():
        print("Помилка: Бот вже запущений. Зупиніть інший екземпляр перед запуском.")
        sys.exit(1)
    create_lock()
    try:
        asyncio.run(main())
    finally:
        remove_lock()
