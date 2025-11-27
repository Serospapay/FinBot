from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from config import EXPENSE_CATEGORIES, INCOME_CATEGORIES


# ==================== REPLY КЛАВІАТУРА (біля поля вводу) ====================

def main_reply_kb():
    """Головна Reply клавіатура - завжди доступна біля поля вводу"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    keyboard.row(
        KeyboardButton(text="💸 Витрата"),
        KeyboardButton(text="💰 Дохід")
    )
    keyboard.row(
        KeyboardButton(text="💳 Баланс"),
        KeyboardButton(text="📝 Історія")
    )
    keyboard.row(
        KeyboardButton(text="📊 Звіти"),
        KeyboardButton(text="🎯 Бюджети")
    )
    keyboard.row(
        KeyboardButton(text="⚡ Швидко"),
        KeyboardButton(text="📤 Експорт")
    )
    
    return keyboard


def quick_reply_kb():
    """Швидка клавіатура для частих операцій"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    keyboard.row(
        KeyboardButton(text="🍔 Їжа"),
        KeyboardButton(text="☕ Кава")
    )
    keyboard.row(
        KeyboardButton(text="🚗 Транспорт"),
        KeyboardButton(text="🎮 Розваги")
    )
    keyboard.row(
        KeyboardButton(text="🏠 Житло"),
        KeyboardButton(text="💊 Здоров'я")
    )
    keyboard.row(
        KeyboardButton(text="« Назад")
    )
    
    return keyboard


# ==================== INLINE КЛАВІАТУРИ (під повідомленнями) ====================

def main_menu_kb():
    """Inline меню для детальних дій"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.row(
        InlineKeyboardButton(text="💸 Додати витрату", callback_data="add_expense"),
        InlineKeyboardButton(text="💰 Додати дохід", callback_data="add_income")
    )
    keyboard.row(
        InlineKeyboardButton(text="📊 Детальна аналітика", callback_data="reports"),
        InlineKeyboardButton(text="💳 Мій баланс", callback_data="balance")
    )
    keyboard.row(
        InlineKeyboardButton(text="🎯 Управління бюджетами", callback_data="budgets")
    )
    keyboard.row(
        InlineKeyboardButton(text="📈 Графіки", callback_data="charts"),
        InlineKeyboardButton(text="📤 Експорт", callback_data="export")
    )
    
    return keyboard


def quick_expense_kb():
    """Швидкі витрати - топові категорії"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton(text="🍔 Їжа", callback_data="quick_cat_expense_🍔 Їжа"),
        InlineKeyboardButton(text="☕ Кава/Снеки", callback_data="quick_cat_expense_🍔 Їжа")
    )
    keyboard.add(
        InlineKeyboardButton(text="🚗 Транспорт", callback_data="quick_cat_expense_🚗 Транспорт"),
        InlineKeyboardButton(text="🎮 Розваги", callback_data="quick_cat_expense_🎮 Розваги")
    )
    keyboard.add(
        InlineKeyboardButton(text="🏠 Житло", callback_data="quick_cat_expense_🏠 Житло"),
        InlineKeyboardButton(text="💊 Здоров'я", callback_data="quick_cat_expense_💊 Здоров'я")
    )
    keyboard.row(
        InlineKeyboardButton(text="📋 Інші категорії", callback_data="add_expense")
    )
    
    return keyboard


def category_kb(trans_type: str):
    """Вибір категорії - компактний grid"""
    categories = EXPENSE_CATEGORIES if trans_type == "expense" else INCOME_CATEGORIES
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    for i in range(0, len(categories), 2):
        if i + 1 < len(categories):
            keyboard.add(
                InlineKeyboardButton(text=categories[i], callback_data=f"cat_{trans_type}_{categories[i]}"),
                InlineKeyboardButton(text=categories[i+1], callback_data=f"cat_{trans_type}_{categories[i+1]}")
            )
        else:
            keyboard.add(
                InlineKeyboardButton(text=categories[i], callback_data=f"cat_{trans_type}_{categories[i]}")
            )
    
    keyboard.row(
        InlineKeyboardButton(text="✖️ Відмінити", callback_data="cancel")
    )
    
    return keyboard


def reports_menu_kb():
    """Меню звітів - компактне"""
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    keyboard.row(
        InlineKeyboardButton(text="Сьогодні", callback_data="report_today")
    )
    keyboard.add(
        InlineKeyboardButton(text="Вчора", callback_data="report_yesterday"),
        InlineKeyboardButton(text="Тиждень", callback_data="report_week"),
        InlineKeyboardButton(text="Місяць", callback_data="report_month")
    )
    keyboard.row(
        InlineKeyboardButton(text="📊 Рік", callback_data="report_year"),
        InlineKeyboardButton(text="🔍 Весь час", callback_data="report_all")
    )
    keyboard.row(
        InlineKeyboardButton(text="📈 Графіки", callback_data="charts")
    )
    
    return keyboard


def charts_menu_kb():
    """Меню графіків"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    keyboard.add(
        InlineKeyboardButton(text="🥧 Витрати по категоріях", callback_data="chart_expense_month")
    )
    keyboard.add(
        InlineKeyboardButton(text="🥧 Доходи по категоріях", callback_data="chart_income_month")
    )
    keyboard.add(
        InlineKeyboardButton(text="📊 Динаміка за рік", callback_data="chart_dynamics_year")
    )
    keyboard.row(
        InlineKeyboardButton(text="◀️ До звітів", callback_data="reports")
    )
    
    return keyboard


def export_menu_kb():
    """Меню експорту"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton(text="📊 Excel", callback_data="export_excel"),
        InlineKeyboardButton(text="📄 CSV", callback_data="export_csv")
    )
    
    return keyboard


def budget_menu_kb():
    """Меню бюджетів"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    keyboard.add(
        InlineKeyboardButton(text="➕ Новий бюджет", callback_data="set_budget")
    )
    keyboard.add(
        InlineKeyboardButton(text="📋 Мої бюджети", callback_data="view_budgets")
    )
    
    return keyboard


def budget_period_kb():
    """Вибір періоду бюджету"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton(text="📅 Місяць", callback_data="budget_period_month"),
        InlineKeyboardButton(text="📅 Рік", callback_data="budget_period_year")
    )
    keyboard.row(
        InlineKeyboardButton(text="✖️ Відмінити", callback_data="cancel")
    )
    
    return keyboard


def back_button_kb():
    """Кнопка назад"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")
    )
    return keyboard


def cancel_button_kb():
    """Кнопка скасування"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(text="✖️ Відмінити", callback_data="cancel")
    )
    return keyboard


def balance_actions_kb():
    """Швидкі дії з балансу"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton(text="💸 Витрата", callback_data="add_expense"),
        InlineKeyboardButton(text="💰 Дохід", callback_data="add_income")
    )
    keyboard.add(
        InlineKeyboardButton(text="📝 Історія", callback_data="view_history"),
        InlineKeyboardButton(text="📊 Звіт", callback_data="report_month")
    )
    keyboard.row(
        InlineKeyboardButton(text="📈 Графіки", callback_data="charts")
    )
    
    return keyboard


def transaction_success_kb():
    """Дії після додавання транзакції"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton(text="➕ Ще витрата", callback_data="add_expense"),
        InlineKeyboardButton(text="💰 Дохід", callback_data="add_income")
    )
    keyboard.add(
        InlineKeyboardButton(text="📊 Баланс", callback_data="balance"),
        InlineKeyboardButton(text="📝 Історія", callback_data="view_history")
    )
    
    return keyboard


def transaction_item_kb(transaction_id: int):
    """Кнопки для кожної транзакції"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton(text="🗑 Видалити", callback_data=f"delete_trans_{transaction_id}")
    )
    
    return keyboard


def budget_item_kb(budget_id: int):
    """Кнопки для кожного бюджету"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton(text="✏️ Змінити", callback_data=f"edit_budget_{budget_id}"),
        InlineKeyboardButton(text="🗑 Видалити", callback_data=f"delete_budget_{budget_id}")
    )
    
    return keyboard


def history_navigation_kb(page: int, total_pages: int):
    """Навігація по історії транзакцій"""
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"history_page_{page-1}"))
    
    buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="history_info"))
    
    if page < total_pages:
        buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"history_page_{page+1}"))
    
    if buttons:
        keyboard.row(*buttons)
    
    keyboard.row(
        InlineKeyboardButton(text="🏠 Головна", callback_data="back_main")
    )
    
    return keyboard
