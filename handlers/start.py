"""Обробники старту, меню, reply кнопок"""
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database import add_user, get_balance
from texts import Messages
from keyboards import (
    main_menu_kb,
    main_reply_kb,
    category_kb,
    reports_menu_kb,
    budget_menu_kb,
    export_menu_kb,
    quick_expense_kb,
    balance_actions_kb,
)
from services import show_history_page
from states import TransactionState

logger = logging.getLogger(__name__)
router = Router(name="start")

QUICK_CATEGORIES = ["🍔 Їжа", "☕ Кава", "🚗 Транспорт", "🎮 Розваги", "🏠 Житло", "💊 Здоров'я"]
CATEGORY_MAP = {
    "🍔 Їжа": "🍔 Їжа",
    "☕ Кава": "🍔 Їжа",
    "🚗 Транспорт": "🚗 Транспорт",
    "🎮 Розваги": "🎮 Розваги",
    "🏠 Житло": "🏠 Житло",
    "💊 Здоров'я": "💊 Здоров'я",
}


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    if message.from_user:
        await add_user(message.from_user.id, message.from_user.username)
    name = message.from_user.first_name if message.from_user else "Користувач"
    await message.answer(
        Messages.WELCOME.format(name=name),
        parse_mode="HTML",
        reply_markup=main_reply_kb(),
    )
    await message.answer(
        Messages.TIP,
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Скасовано\n\n" + Messages.MAIN_MENU,
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        Messages.MAIN_MENU,
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(Messages.HELP, parse_mode="HTML", reply_markup=main_menu_kb())


@router.message(Command("balance"))
@router.message(F.text == "💳 Баланс")
async def cmd_balance(message: Message, state: FSMContext) -> None:
    await state.clear()
    income, expense, balance = await get_balance(message.from_user.id)
    balance_emoji = "💚" if balance >= 0 else "❤️"
    balance_text = (
        f"{balance_emoji} Ваш баланс\n\n"
        f"📊 {balance:,.2f} грн\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📈 Доходи: +{income:,.2f} грн\n"
        f"📉 Витрати: -{expense:,.2f} грн\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    await message.answer(balance_text, parse_mode="HTML", reply_markup=balance_actions_kb())


@router.message(F.text == "💸 Витрата")
async def reply_add_expense(message: Message, state: FSMContext) -> None:
    await state.set_data({})
    await state.update_data(transaction_type="expense")
    await message.answer(
        "Додати витрату\n\nОберіть категорію:",
        parse_mode="HTML",
        reply_markup=category_kb("expense"),
    )


@router.message(F.text == "💰 Дохід")
async def reply_add_income(message: Message, state: FSMContext) -> None:
    await state.set_data({})
    await state.update_data(transaction_type="income")
    await message.answer(
        "Додати дохід\n\nОберіть категорію:",
        parse_mode="HTML",
        reply_markup=category_kb("income"),
    )


@router.message(F.text == "📊 Звіти")
async def reply_reports(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Аналітика\n\nОберіть період:",
        parse_mode="HTML",
        reply_markup=reports_menu_kb(),
    )


@router.message(F.text == "🎯 Бюджети")
async def reply_budgets(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Бюджети\n\nУправління бюджетами:",
        parse_mode="HTML",
        reply_markup=budget_menu_kb(),
    )


@router.message(F.text == "📤 Експорт")
async def reply_export(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Експорт даних\n\nОберіть формат:",
        parse_mode="HTML",
        reply_markup=export_menu_kb(),
    )


@router.message(F.text == "📝 Історія")
async def reply_history(message: Message, state: FSMContext) -> None:
    await state.clear()
    await show_history_page(message.from_user.id, message, 1, is_new_message=True)


@router.message(F.text == "⚡ Швидко")
async def reply_quick(message: Message, state: FSMContext) -> None:
    await state.set_data({})
    await state.update_data(transaction_type="expense")
    await message.answer(
        "Швидкі витрати\n\nОберіть категорію одним кліком:",
        parse_mode="HTML",
        reply_markup=quick_expense_kb(),
    )


@router.message(F.text.in_(QUICK_CATEGORIES))
async def reply_quick_category(message: Message, state: FSMContext) -> None:
    from datetime import datetime

    category = CATEGORY_MAP.get(message.text or "", "🍔 Їжа")
    today_str = datetime.now().strftime("%Y-%m-%d")
    await state.update_data(
        category=category, transaction_type="expense", transaction_date=today_str
    )
    await state.set_state(TransactionState.waiting_for_amount)
    await message.answer(
        f"Швидка витрата\n\n📁 {category}\n💵 Введіть суму:",
        parse_mode="HTML",
        reply_markup=main_reply_kb(),
    )


@router.message(F.text.in_(["🏠 Головна", "Головна"]))
async def reply_home(message: Message, state: FSMContext) -> None:
    """Швидкий перехід на головну з будь-якого екрану"""
    await state.clear()
    await message.answer(
        Messages.MAIN_MENU,
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )


@router.message(F.text == "« Назад")
async def reply_back(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Головне меню", reply_markup=main_reply_kb())
    await message.answer(
        Messages.MAIN_MENU,
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )
