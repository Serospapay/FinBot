"""Конфігурація бота через Pydantic Settings"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Налаштування з .env"""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    BOT_TOKEN: str
    DB_NAME: str = "finance.db"
    REDIS_URL: str | None = None  # redis://localhost:6379/0 для Redis FSM


# Категорії (не в .env - статичні)
EXPENSE_CATEGORIES = [
    "🍔 Їжа",
    "🚗 Транспорт",
    "🏠 Житло",
    "👕 Одяг",
    "💊 Здоров'я",
    "🎮 Розваги",
    "📚 Освіта",
    "💰 Інше",
]

INCOME_CATEGORIES = [
    "💼 Зарплата",
    "💸 Бонус",
    "🎁 Подарунок",
    "📈 Інвестиції",
    "💰 Інше",
]

settings = Settings()
