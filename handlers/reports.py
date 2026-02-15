"""Обробники звітів та графіків"""
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery

from database import get_balance
from keyboards import charts_menu_kb, reports_menu_kb
from services import safe_edit_or_answer
from reports import (
    generate_dynamics_chart,
    generate_pie_chart,
    generate_report,
    get_period_dates,
)

logger = logging.getLogger(__name__)
router = Router(name="reports")


@router.callback_query(F.data == "balance")
async def show_balance(callback: CallbackQuery, state: FSMContext) -> None:
    from keyboards import balance_actions_kb

    await state.clear()
    income, expense, balance = await get_balance(callback.from_user.id)
    balance_emoji = "💚" if balance >= 0 else "❤️"
    balance_text = (
        f"{balance_emoji} Ваш баланс\n\n"
        f"📊 {balance:,.2f} грн\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📈 Доходи: +{income:,.2f} грн\n"
        f"📉 Витрати: -{expense:,.2f} грн\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    await safe_edit_or_answer(
        callback.message, balance_text, reply_markup=balance_actions_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "reports")
async def show_reports(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    text = "Аналітика\n\nОберіть період для аналізу:"
    markup = reports_menu_kb()
    await safe_edit_or_answer(callback.message, text, reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data.startswith("report_"))
async def generate_report_handler(callback: CallbackQuery) -> None:
    period = callback.data.replace("report_", "")
    start_date, end_date, period_name = get_period_dates(period)
    await callback.answer("Генерую звіт...")
    try:
        report = await generate_report(
            callback.from_user.id, start_date, end_date, period_name
        )
        await safe_edit_or_answer(
            callback.message, report, reply_markup=reports_menu_kb()
        )
    except Exception as e:
        logger.error("Помилка генерації звіту: %s", e)
        await callback.message.answer(
            "Помилка генерації звіту. Спробуйте пізніше.",
            reply_markup=reports_menu_kb(),
        )


@router.callback_query(F.data == "charts")
async def show_charts(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    text = "Графічна аналітика\n\nОберіть тип графіка:"
    markup = charts_menu_kb()
    await safe_edit_or_answer(callback.message, text, reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data == "chart_expense_month")
async def chart_expense(callback: CallbackQuery) -> None:
    await callback.answer("Генерую графік...")
    try:
        chart = await generate_pie_chart(
            callback.from_user.id, "expense", "останній місяць"
        )
        if chart:
            chart.seek(0)
            photo = BufferedInputFile(chart.read(), filename="chart.png")
            await callback.message.answer_photo(
                photo=photo,
                caption="Витрати за останній місяць",
                reply_markup=charts_menu_kb(),
            )
        else:
            await callback.message.answer(
                "Недостатньо даних для побудови графіка.\n"
                "Додайте транзакції, щоб побачити аналітику.",
                reply_markup=charts_menu_kb(),
            )
    except Exception as e:
        logger.error("Помилка генерації графіка витрат: %s", e)
        await callback.message.answer(
            "Помилка генерації графіка. Спробуйте пізніше.",
            reply_markup=charts_menu_kb(),
        )


@router.callback_query(F.data == "chart_income_month")
async def chart_income(callback: CallbackQuery) -> None:
    await callback.answer("Генерую графік...")
    try:
        chart = await generate_pie_chart(
            callback.from_user.id, "income", "останній місяць"
        )
        if chart:
            chart.seek(0)
            photo = BufferedInputFile(chart.read(), filename="chart.png")
            await callback.message.answer_photo(
                photo=photo,
                caption="Доходи за останній місяць",
                reply_markup=charts_menu_kb(),
            )
        else:
            await callback.message.answer(
                "Недостатньо даних для побудови графіка.\n"
                "Додайте транзакції, щоб побачити аналітику.",
                reply_markup=charts_menu_kb(),
            )
    except Exception as e:
        logger.error("Помилка генерації графіка доходів: %s", e)
        await callback.message.answer(
            "Помилка генерації графіка. Спробуйте пізніше.",
            reply_markup=charts_menu_kb(),
        )


@router.callback_query(F.data == "chart_dynamics_year")
async def chart_dynamics(callback: CallbackQuery) -> None:
    await callback.answer("Генерую графік...")
    try:
        chart = await generate_dynamics_chart(callback.from_user.id)
        if chart:
            chart.seek(0)
            photo = BufferedInputFile(chart.read(), filename="dynamics.png")
            await callback.message.answer_photo(
                photo=photo,
                caption="Динаміка доходів та витрат за рік",
                reply_markup=charts_menu_kb(),
            )
        else:
            await callback.message.answer(
                "Недостатньо даних для побудови графіка.\n"
                "Додайте транзакції, щоб побачити динаміку.",
                reply_markup=charts_menu_kb(),
            )
    except Exception as e:
        logger.error("Помилка генерації графіка динаміки: %s", e)
        await callback.message.answer(
            "Помилка генерації графіка. Спробуйте пізніше.",
            reply_markup=charts_menu_kb(),
        )
