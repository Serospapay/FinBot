"""Сервісні функції для handlers"""
import logging
from datetime import datetime

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from database import check_budget, get_recent_transactions
from keyboards import back_button_kb, history_navigation_kb
from texts import Messages
from utils import escape_html

logger = logging.getLogger(__name__)


async def safe_edit_or_answer(
    msg: Message,
    text: str,
    *,
    parse_mode: str = "HTML",
    reply_markup=None,
) -> None:
    """Спроба edit_text; при помилці (фото/документ/застаріле повідомлення) - answer."""
    try:
        await msg.edit_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
    except TelegramBadRequest:
        await msg.answer(text, parse_mode=parse_mode, reply_markup=reply_markup)
    except Exception as e:
        logger.warning("Помилка edit_text, fallback на answer: %s", e)
        await msg.answer(text, parse_mode=parse_mode, reply_markup=reply_markup)


async def show_history_page(
    user_id: int,
    message: Message | CallbackQuery,
    page: int = 1,
    is_new_message: bool = False,
) -> None:
    """Показати сторінку історії транзакцій"""
    msg = message.message if isinstance(message, CallbackQuery) else message
    try:
        per_page = 5
        offset = (page - 1) * per_page
        transactions, total_count = await get_recent_transactions(user_id, per_page, offset)

        if not transactions:
            text = Messages.HISTORY_EMPTY
            if is_new_message:
                await msg.answer(text, parse_mode="HTML", reply_markup=back_button_kb())
            else:
                await safe_edit_or_answer(msg, text, reply_markup=back_button_kb())
            return

        total_pages = (total_count + per_page - 1) // per_page
        text = f"Історія транзакцій\n<i>Сторінка {page} з {total_pages} (всього: {total_count})</i>\n\n"

        for trans in transactions:
            trans_id, _, trans_type, amount, category, description, date, _ = trans
            emoji = "📉" if trans_type == "expense" else "📈"
            sign = "-" if trans_type == "expense" else "+"
            text += f"{emoji} <b>{category}</b>\n"
            text += f"   💵 {sign}{amount:,.2f} грн\n"
            text += f"   📅 {date}\n"
            if description:
                text += f"   📝 {escape_html(description)}\n"
            text += f"   <code>[ID: {trans_id}]</code> /del_{trans_id}\n\n"

        markup = history_navigation_kb(page, total_pages, transactions)
        if is_new_message:
            await msg.answer(text, parse_mode="HTML", reply_markup=markup)
        else:
            await safe_edit_or_answer(msg, text, reply_markup=markup)
    except Exception as e:
        logger.error("Помилка показу історії: %s", e)
        msg_obj = message.message if isinstance(message, CallbackQuery) else message
        try:
            await msg_obj.answer(
                Messages.ERRORS["try_again"],
                reply_markup=back_button_kb(),
            )
        except Exception:
            pass


async def check_and_notify_budget(message: Message, category: str) -> None:
    """Перевірка та сповіщення про бюджет"""
    try:
        user_id = message.from_user.id if message.from_user else 0
        today = datetime.now()
        start_of_month = today.replace(day=1).strftime("%Y-%m-%d")
        end_of_month = today.strftime("%Y-%m-%d")
        budget_amount, spent_amount = await check_budget(
            user_id, category, "month", start_of_month, end_of_month
        )
        if budget_amount and budget_amount > 0:
            percentage = (spent_amount / budget_amount) * 100
            if percentage >= 100:
                await message.answer(
                    Messages.BUDGET_WARNING_100.format(
                        category=category,
                        spent=spent_amount,
                        budget=budget_amount,
                        percent=percentage,
                    ),
                    parse_mode="HTML",
                )
            elif percentage >= 80:
                await message.answer(
                    Messages.BUDGET_WARNING_80.format(
                        category=category,
                        percent=percentage,
                        spent=spent_amount,
                        budget=budget_amount,
                    ),
                    parse_mode="HTML",
                )
    except Exception as e:
        logger.error("Помилка перевірки бюджету: %s", e)
