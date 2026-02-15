"""Обробники навігації"""
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from keyboards import main_menu_kb
from services import safe_edit_or_answer
from texts import Messages

logger = logging.getLogger(__name__)
router = Router(name="navigation")


@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await safe_edit_or_answer(
        callback.message, Messages.MAIN_MENU, reply_markup=main_menu_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await safe_edit_or_answer(
        callback.message,
        "Скасовано\n\n" + Messages.MAIN_MENU,
        reply_markup=main_menu_kb(),
    )
    await callback.answer()
