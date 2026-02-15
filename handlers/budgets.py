"""Обробники бюджетів"""
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import check_budget, get_budgets, set_budget, delete_budget
from keyboards import (
    budget_list_kb,
    budget_menu_kb,
    budget_period_kb,
    category_kb,
    confirm_delete_budget_kb,
)
from states import BudgetState
from texts import Messages
from utils import validate_amount

logger = logging.getLogger(__name__)
router = Router(name="budgets")


@router.callback_query(F.data == "set_budget")
async def set_budget_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(BudgetState.waiting_for_category)
    await callback.message.edit_text(
        "Встановити бюджет\n\nОберіть категорію витрат:",
        parse_mode="HTML",
        reply_markup=category_kb("expense"),
    )
    await callback.answer()


@router.callback_query(
    F.data.startswith("cat_expense_"),
    BudgetState.waiting_for_category,
)
async def budget_select_category(callback: CallbackQuery, state: FSMContext) -> None:
    category = callback.data.replace("cat_expense_", "")
    await state.update_data(budget_category=category)
    await state.set_state(BudgetState.waiting_for_period)
    await callback.message.edit_text(
        f"Встановити бюджет\n\n📁 Категорія: {category}\n\nОберіть період бюджету:",
        parse_mode="HTML",
        reply_markup=budget_period_kb(),
    )
    await callback.answer()


@router.callback_query(
    F.data.startswith("budget_period_"),
    BudgetState.waiting_for_period,
)
async def budget_select_period(callback: CallbackQuery, state: FSMContext) -> None:
    period = callback.data.replace("budget_period_", "")
    await state.update_data(budget_period=period)
    period_name = "місячний" if period == "month" else "річний"
    await state.set_state(BudgetState.waiting_for_amount)
    data = await state.get_data()
    category = data.get("budget_category", "Невідома")
    await callback.message.edit_text(
        f"Встановити бюджет\n\n📁 Категорія: {category}\n"
        f"📅 Період: {period_name}\n\n💵 Введіть суму бюджету (грн):",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(BudgetState.waiting_for_amount, F.text)
async def budget_process_amount(message: Message, state: FSMContext) -> None:
    is_valid, amount = validate_amount(message.text)
    if not is_valid:
        await message.answer(
            "Помилка! Введіть коректну суму.\n"
            "Приклади: 5000, 10000.50\nМаксимальна сума: 1,000,000,000 грн"
        )
        return
    data = await state.get_data()
    category = data.get("budget_category")
    period = data.get("budget_period")
    if not category or not period:
        await message.answer("Помилка! Спробуйте ще раз.", reply_markup=budget_menu_kb())
        await state.clear()
        return
    try:
        await set_budget(message.from_user.id, category, amount, period)
        period_name = "місячний" if period == "month" else "річний"
        await message.answer(
            f"Бюджет встановлено!\n\n📁 Категорія: {category}\n"
            f"📅 Період: {period_name}\n💵 Сума: {amount:.2f} грн",
            parse_mode="HTML",
            reply_markup=budget_menu_kb(),
        )
    except Exception as e:
        logger.error("Помилка встановлення бюджету: %s", e)
        await message.answer(
            "Помилка встановлення бюджету. Спробуйте пізніше.",
            reply_markup=budget_menu_kb(),
        )
    finally:
        await state.clear()


@router.callback_query(F.data == "budgets")
async def show_budgets_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "Бюджети\n\nВстановлюйте бюджети для контролю витрат:",
        parse_mode="HTML",
        reply_markup=budget_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "view_budgets")
async def view_budgets(callback: CallbackQuery) -> None:
    budgets = await get_budgets(callback.from_user.id)
    if not budgets:
        await callback.message.edit_text(
            "У вас ще немає встановлених бюджетів.\n\n"
            "Встановіть бюджет, щоб контролювати витрати!",
            reply_markup=budget_menu_kb(),
        )
        await callback.answer()
        return
    text = "Ваші бюджети:\n\n"
    from datetime import datetime

    today = datetime.now()
    for budget in budgets:
        budget_id, _, category, amount, period = budget[0], budget[1], budget[2], budget[3], budget[4]
        period_name = "Місяць" if period == "month" else "Рік"
        if period == "month":
            start_date = today.replace(day=1).strftime("%Y-%m-%d")
        else:
            start_date = today.replace(month=1, day=1).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
        _, spent = await check_budget(
            callback.from_user.id, category, period, start_date, end_date
        )
        spent = spent or 0
        percentage = (spent / amount) * 100 if amount > 0 else 0
        status_emoji = "🟢" if percentage < 80 else "🟡" if percentage < 100 else "🔴"
        text += f"{status_emoji} {category}\n"
        text += f"   Бюджет: {amount:,.2f} грн ({period_name})\n"
        text += f"   Витрачено: {spent:,.2f} грн ({percentage:.1f}%)\n"
        text += f"   Залишок: {max(0, amount - spent):,.2f} грн\n\n"
    await callback.message.edit_text(
        text, parse_mode="HTML", reply_markup=budget_list_kb(budgets)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delete_budget_"))
async def delete_budget_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    """Показати підтвердження видалення бюджету"""
    await state.clear()
    try:
        budget_id = int(callback.data.replace("delete_budget_", ""))
        await callback.message.edit_text(
            Messages.CONFIRM_DELETE_BUDGET,
            parse_mode="HTML",
            reply_markup=confirm_delete_budget_kb(budget_id),
        )
        await callback.answer()
    except ValueError as e:
        logger.error("Помилка парсингу budget_id: %s", e)
        await callback.answer(Messages.ERRORS["delete_budget"], show_alert=True)


@router.callback_query(F.data.startswith("confirm_del_budget_"))
async def delete_budget_confirm_yes(callback: CallbackQuery, state: FSMContext) -> None:
    """Підтверджене видалення бюджету"""
    await state.clear()
    try:
        budget_id = int(callback.data.replace("confirm_del_budget_", ""))
        success = await delete_budget(budget_id, callback.from_user.id)
        if success:
            await callback.answer("Бюджет видалено!")
            try:
                await callback.message.edit_text(
                    "Бюджет успішно видалено!",
                    reply_markup=budget_menu_kb(),
                )
            except Exception:
                await callback.message.answer(
                    "Бюджет успішно видалено!",
                    reply_markup=budget_menu_kb(),
                )
        else:
            await callback.answer(Messages.ERRORS["delete_budget"], show_alert=True)
    except (ValueError, Exception) as e:
        logger.error("Помилка видалення бюджету (callback): %s", e)
        await callback.answer(Messages.ERRORS["delete_budget"], show_alert=True)


@router.callback_query(F.data == "cancel_del_budget")
async def delete_budget_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """Скасування видалення - повернутися до списку бюджетів"""
    await state.clear()
    budgets = await get_budgets(callback.from_user.id)
    if not budgets:
        await callback.message.edit_text(
            "У вас ще немає встановлених бюджетів.\n\n"
            "Встановіть бюджет, щоб контролювати витрати!",
            reply_markup=budget_menu_kb(),
        )
    else:
        from datetime import datetime

        today = datetime.now()
        text = "Ваші бюджети:\n\n"
        for budget in budgets:
            budget_id, _, category, amount, period = budget[0], budget[1], budget[2], budget[3], budget[4]
            period_name = "Місяць" if period == "month" else "Рік"
            if period == "month":
                start_date = today.replace(day=1).strftime("%Y-%m-%d")
            else:
                start_date = today.replace(month=1, day=1).strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")
            _, spent = await check_budget(
                callback.from_user.id, category, period, start_date, end_date
            )
            spent = spent or 0
            percentage = (spent / amount) * 100 if amount > 0 else 0
            status_emoji = "🟢" if percentage < 80 else "🟡" if percentage < 100 else "🔴"
            text += f"{status_emoji} {category}\n"
            text += f"   Бюджет: {amount:,.2f} грн ({period_name})\n"
            text += f"   Витрачено: {spent:,.2f} грн ({percentage:.1f}%)\n"
            text += f"   Залишок: {max(0, amount - spent):,.2f} грн\n\n"
        await callback.message.edit_text(
            text, parse_mode="HTML", reply_markup=budget_list_kb(budgets)
        )
    await callback.answer("Скасовано")


@router.callback_query(F.data.startswith("edit_budget_"))
async def edit_budget_callback(callback: CallbackQuery) -> None:
    await callback.answer(
        "Щоб змінити бюджет - видаліть поточний та створіть новий.",
        show_alert=True,
    )


@router.message(F.text.startswith("/del_budget_"))
async def delete_budget_cmd(message: Message, state: FSMContext) -> None:
    await state.clear()
    try:
        budget_id = int(message.text.replace("/del_budget_", ""))
        success = await delete_budget(budget_id, message.from_user.id)
        if success:
            await message.answer("Бюджет успішно видалено!", reply_markup=budget_menu_kb())
        else:
            await message.answer("Помилка видалення бюджету.", reply_markup=budget_menu_kb())
    except Exception as e:
        logger.error("Помилка видалення бюджету: %s", e)
        await message.answer("Помилка видалення бюджету.", reply_markup=budget_menu_kb())
