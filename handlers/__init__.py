"""Реєстрація всіх обробників"""
from aiogram import Dispatcher

from .start import router as start_router
from .budgets import router as budgets_router
from .transactions import router as transactions_router
from .reports import router as reports_router
from .history import router as history_router
from .export import router as export_router
from .navigation import router as navigation_router


def register_handlers(dp: Dispatcher) -> None:
    """Підключає всі роутери"""
    dp.include_router(start_router)
    dp.include_router(budgets_router)
    dp.include_router(transactions_router)
    dp.include_router(reports_router)
    dp.include_router(history_router)
    dp.include_router(export_router)
    dp.include_router(navigation_router)
