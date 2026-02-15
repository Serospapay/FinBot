"""Обробники транзакцій"""
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import add_transaction, get_balance, delete_transaction
from keyboards import (
    cancel_button_kb,
    category_kb,
    date_select_kb,
    main_menu_kb,
    main_reply_kb,
    quick_expense_kb,
    transaction_success_kb,
)
from services import check_and_notify_budget
from states import TransactionState
from texts import Messages
from utils import escape_html, get_safe_description, validate_amount

logger = logging.getLogger(__name__)
router = Router(name="transactions")


@router.callback_query(F.data == "add_expense")
async def add_expense(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_data({})
    await state.update_data(transaction_type="expense")
    await callback.message.edit_text(
        "Додати витрату\n\nОберіть категорію:",
        parse_mode="HTML",
        reply_markup=category_kb("expense"),
    )
    await callback.answer()


@router.callback_query(F.data == "quick_expense")
async def quick_expense(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_data({})
    await state.update_data(transaction_type="expense")
    await callback.message.edit_text(
        "Швидка витрата\n\nОберіть популярну категорію:",
        parse_mode="HTML",
        reply_markup=quick_expense_kb(),
    )
    await callback.answer()


# Мапінг швидких категорій на основні (для узгодженості з бюджетами)
QUICK_CAT_MAP = {"☕ Кава": "🍔 Їжа"}


@router.callback_query(F.data.startswith("quick_cat_"))
async def quick_category(callback: CallbackQuery, state: FSMContext) -> None:
    from datetime import datetime

    parts = callback.data.split("_", 3)
    if len(parts) < 4:
        await callback.answer("Помилка вибору категорії")
        return
    trans_type, category = parts[2], parts[3]
    category = QUICK_CAT_MAP.get(category, category)
    today_str = datetime.now().strftime("%Y-%m-%d")
    await state.update_data(
        category=category, transaction_type=trans_type, transaction_date=today_str
    )
    await state.set_state(TransactionState.waiting_for_amount)
    await callback.message.edit_text(
        f"Швидка витрата\n\n📁 Категорія: {category}\n💵 Введіть суму:",
        parse_mode="HTML",
        reply_markup=cancel_button_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "add_income")
async def add_income(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_data({})
    await state.update_data(transaction_type="income")
    await callback.message.edit_text(
        "Додати дохід\n\nОберіть категорію:",
        parse_mode="HTML",
        reply_markup=category_kb("income"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cat_"))
async def select_category(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split("_", 2)
    if len(parts) < 3:
        await callback.answer("Помилка вибору категорії")
        return
    trans_type, category = parts[1], parts[2]
    data = await state.get_data()
    existing_type = data.get("transaction_type", trans_type)
    await state.update_data(category=category, transaction_type=existing_type)
    await state.set_state(TransactionState.waiting_for_date)
    emoji = "💸" if existing_type == "expense" else "💰"
    trans_name = "Витрата" if existing_type == "expense" else "Дохід"
    await callback.message.edit_text(
        f"{emoji} {trans_name}\n\n📁 Категорія: {category}\n\nОберіть дату транзакції:",
        parse_mode="HTML",
        reply_markup=date_select_kb(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("trans_date_"), TransactionState.waiting_for_date)
async def select_date(callback: CallbackQuery, state: FSMContext) -> None:
    """Обробка вибору дати транзакції"""
    from datetime import datetime, timedelta

    choice = callback.data.replace("trans_date_", "")
    today = datetime.now()
    if choice == "today" or choice == "skip":
        date_str = today.strftime("%Y-%m-%d")
    elif choice == "yesterday":
        date_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        await callback.answer("Невідомий вибір")
        return
    await state.update_data(transaction_date=date_str)
    await state.set_state(TransactionState.waiting_for_amount)
    data = await state.get_data()
    category = data.get("category", "")
    trans_type = data.get("transaction_type", "expense")
    emoji = "💸" if trans_type == "expense" else "💰"
    trans_name = "Витрата" if trans_type == "expense" else "Дохід"
    await callback.message.edit_text(
        f"{emoji} {trans_name}\n\n📁 Категорія: {category}\n📅 Дата: {date_str}\n\n💵 Введіть суму:",
        parse_mode="HTML",
        reply_markup=cancel_button_kb(),
    )
    await callback.answer()


@router.message(TransactionState.waiting_for_amount, F.text)
async def process_amount(message: Message, state: FSMContext) -> None:
    is_valid, amount = validate_amount(message.text)
    if not is_valid:
        await message.answer(Messages.ERRORS["invalid_amount"])
        return
    await state.update_data(amount=amount)
    await state.set_state(TransactionState.waiting_for_description)
    await message.answer(
        Messages.ENTER_DESCRIPTION,
        reply_markup=cancel_button_kb(),
    )


@router.message(TransactionState.waiting_for_description, F.text)
async def process_description(message: Message, state: FSMContext) -> None:
    processing_msg = await message.answer(Messages.PROCESSING)
    description = get_safe_description(message.text)
    data = await state.get_data()
    trans_type = data.get("transaction_type")
    category = data.get("category")
    amount = data.get("amount")
    date_str = data.get("transaction_date")
    if not trans_type or not category or not amount:
        await processing_msg.delete()
        await message.answer(Messages.ERRORS["try_again"], reply_markup=main_menu_kb())
        await state.clear()
        return
    try:
        await add_transaction(
            message.from_user.id, trans_type, amount, category, description, date_str
        )
        income, expense, balance = await get_balance(message.from_user.id)
        emoji = "📉" if trans_type == "expense" else "📈"
        trans_name = "Витрата" if trans_type == "expense" else "Дохід"
        safe_desc = escape_html(description) if description else "Не вказано"
        await processing_msg.delete()
        success_text = (
            f"✅ {emoji} {trans_name} додана!\n\n"
            f"📁 Категорія: {category}\n"
            f"💵 Сума: {amount:.2f} грн\n"
            f"📝 Опис: {safe_desc}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💰 Новий баланс: {balance:,.2f} грн"
        )
        await message.answer(
            success_text,
            parse_mode="HTML",
            reply_markup=transaction_success_kb(),
        )
        if trans_type == "expense":
            await check_and_notify_budget(message, category)
    except Exception as e:
        logger.error("Помилка додавання транзакції: %s", e)
        await processing_msg.delete()
        await message.answer(
            Messages.ERRORS["transaction_saved"],
            reply_markup=main_menu_kb(),
        )
    finally:
        await state.clear()


@router.message(F.text.startswith("/del_"))
async def delete_transaction_cmd(message: Message, state: FSMContext) -> None:
    await state.clear()
    try:
        trans_id = int(message.text.replace("/del_", ""))
        success = await delete_transaction(trans_id, message.from_user.id)
        if success:
            await message.answer("Транзакцію успішно видалено!", reply_markup=main_menu_kb())
        else:
            await message.answer(Messages.ERRORS["delete_transaction"], reply_markup=main_menu_kb())
    except Exception as e:
        logger.error("Помилка видалення транзакції: %s", e)
        await message.answer(Messages.ERRORS["delete_transaction"], reply_markup=main_menu_kb())
