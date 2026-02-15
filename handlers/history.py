"""Обробники історії транзакцій"""
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from database import delete_transaction
from keyboards import back_button_kb, confirm_delete_trans_kb
from services import show_history_page
from texts import Messages

logger = logging.getLogger(__name__)
router = Router(name="history")


@router.callback_query(F.data == "view_history")
async def view_history(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await show_history_page(callback.from_user.id, callback, 1)
    await callback.answer()


@router.callback_query(F.data.startswith("history_page_"))
async def history_page_handler(callback: CallbackQuery) -> None:
    page = int(callback.data.replace("history_page_", ""))
    await show_history_page(callback.from_user.id, callback, page)
    await callback.answer()


@router.callback_query(F.data.regexp(r"^delete_trans_(\d+)_(\d+)$"))
async def delete_transaction_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    """Показати підтвердження видалення транзакції"""
    await state.clear()
    parts = callback.data.split("_")
    trans_id = int(parts[2])
    page = int(parts[3])
    await callback.message.edit_text(
        Messages.CONFIRM_DELETE_TRANS.format(trans_id=trans_id),
        parse_mode="HTML",
        reply_markup=confirm_delete_trans_kb(trans_id, page),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_del_trans_"))
async def delete_transaction_confirm_yes(callback: CallbackQuery, state: FSMContext) -> None:
    """Підтверджене видалення транзакції"""
    await state.clear()
    try:
        trans_id = int(callback.data.replace("confirm_del_trans_", ""))
        success = await delete_transaction(trans_id, callback.from_user.id)
        if success:
            await callback.answer("Видалено!")
            await show_history_page(callback.from_user.id, callback, 1)
        else:
            await callback.answer(Messages.ERRORS["delete_transaction"], show_alert=True)
    except (ValueError, Exception) as e:
        logger.error("Помилка видалення транзакції (callback): %s", e)
        await callback.answer(Messages.ERRORS["delete_transaction"], show_alert=True)


@router.callback_query(F.data.startswith("cancel_del_trans_"))
async def delete_transaction_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """Скасування видалення - повернутися до історії"""
    await state.clear()
    page = int(callback.data.replace("cancel_del_trans_", ""))
    await show_history_page(callback.from_user.id, callback, page)
    await callback.answer("Скасовано")


@router.callback_query(F.data == "history_info")
async def history_info_callback(callback: CallbackQuery) -> None:
    await callback.answer()
