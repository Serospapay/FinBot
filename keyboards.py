from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from config import EXPENSE_CATEGORIES, INCOME_CATEGORIES
from constants import CallbackData


# ==================== REPLY КЛАВІАТУРА (біля поля вводу) ====================

def main_reply_kb():
    """Головна Reply клавіатура - завжди доступна біля поля вводу"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="💸 Витрата"),
                KeyboardButton(text="💰 Дохід"),
            ],
            [
                KeyboardButton(text="💳 Баланс"),
                KeyboardButton(text="📝 Історія"),
            ],
            [
                KeyboardButton(text="📊 Звіти"),
                KeyboardButton(text="🎯 Бюджети"),
            ],
            [
                KeyboardButton(text="⚡ Швидко"),
                KeyboardButton(text="📤 Експорт"),
            ],
            [KeyboardButton(text="🏠 Головна")],
        ],
        resize_keyboard=True,
    )


def quick_reply_kb():
    """Швидка клавіатура для частих операцій"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🍔 Їжа"),
                KeyboardButton(text="☕ Кава"),
            ],
            [
                KeyboardButton(text="🚗 Транспорт"),
                KeyboardButton(text="🎮 Розваги"),
            ],
            [
                KeyboardButton(text="🏠 Житло"),
                KeyboardButton(text="💊 Здоров'я"),
            ],
            [KeyboardButton(text="« Назад")],
        ],
        resize_keyboard=True,
    )


# ==================== INLINE КЛАВІАТУРИ (під повідомленнями) ====================

def main_menu_kb():
    """Inline меню для детальних дій"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💸 Додати витрату", callback_data=CallbackData.ADD_EXPENSE),
                InlineKeyboardButton(text="💰 Додати дохід", callback_data=CallbackData.ADD_INCOME),
            ],
            [
                InlineKeyboardButton(text="📊 Детальна аналітика", callback_data=CallbackData.REPORTS),
                InlineKeyboardButton(text="💳 Мій баланс", callback_data=CallbackData.BALANCE),
            ],
            [
                InlineKeyboardButton(text="🎯 Управління бюджетами", callback_data=CallbackData.BUDGETS),
            ],
            [
                InlineKeyboardButton(text="📈 Графіки", callback_data=CallbackData.CHARTS),
                InlineKeyboardButton(text="📤 Експорт", callback_data=CallbackData.EXPORT),
            ],
        ]
    )


def quick_expense_kb():
    """Швидкі витрати - топові категорії"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🍔 Їжа", callback_data="quick_cat_expense_🍔 Їжа"),
                InlineKeyboardButton(text="☕ Кава/Снеки", callback_data="quick_cat_expense_☕ Кава"),
            ],
            [
                InlineKeyboardButton(text="🚗 Транспорт", callback_data="quick_cat_expense_🚗 Транспорт"),
                InlineKeyboardButton(text="🎮 Розваги", callback_data="quick_cat_expense_🎮 Розваги"),
            ],
            [
                InlineKeyboardButton(text="🏠 Житло", callback_data="quick_cat_expense_🏠 Житло"),
                InlineKeyboardButton(text="💊 Здоров'я", callback_data="quick_cat_expense_💊 Здоров'я"),
            ],
            [
                InlineKeyboardButton(text="📋 Інші категорії", callback_data=CallbackData.ADD_EXPENSE),
                InlineKeyboardButton(text="🏠 Головна", callback_data=CallbackData.BACK_MAIN),
            ],
        ]
    )


def category_kb(trans_type: str):
    """Вибір категорії - компактний grid"""
    categories = EXPENSE_CATEGORIES if trans_type == "expense" else INCOME_CATEGORIES
    rows: list[list[InlineKeyboardButton]] = []
    for i in range(0, len(categories), 2):
        if i + 1 < len(categories):
            rows.append([
                InlineKeyboardButton(text=categories[i], callback_data=f"cat_{trans_type}_{categories[i]}"),
                InlineKeyboardButton(text=categories[i + 1], callback_data=f"cat_{trans_type}_{categories[i + 1]}"),
            ])
        else:
            rows.append([
                InlineKeyboardButton(text=categories[i], callback_data=f"cat_{trans_type}_{categories[i]}"),
            ])
    rows.append([
        InlineKeyboardButton(text="✖️ Відмінити", callback_data=CallbackData.CANCEL),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def reports_menu_kb():
    """Меню звітів - компактне"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Сьогодні", callback_data="report_today")],
            [
                InlineKeyboardButton(text="Вчора", callback_data="report_yesterday"),
                InlineKeyboardButton(text="Тиждень", callback_data="report_week"),
                InlineKeyboardButton(text="Місяць", callback_data="report_month"),
            ],
            [
                InlineKeyboardButton(text="📊 Рік", callback_data="report_year"),
                InlineKeyboardButton(text="🔍 Весь час", callback_data="report_all"),
            ],
            [
                InlineKeyboardButton(text="📈 Графіки", callback_data=CallbackData.CHARTS),
                InlineKeyboardButton(text="🏠 Головна", callback_data=CallbackData.BACK_MAIN),
            ],
        ]
    )


def charts_menu_kb():
    """Меню графіків"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🥧 Витрати по категоріях", callback_data="chart_expense_month")],
            [InlineKeyboardButton(text="🥧 Доходи по категоріях", callback_data="chart_income_month")],
            [InlineKeyboardButton(text="📊 Динаміка за рік", callback_data="chart_dynamics_year")],
            [
                InlineKeyboardButton(text="◀️ До звітів", callback_data=CallbackData.REPORTS),
                InlineKeyboardButton(text="🏠 Головна", callback_data=CallbackData.BACK_MAIN),
            ],
        ]
    )


def export_menu_kb():
    """Меню експорту"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Excel", callback_data="export_excel"),
                InlineKeyboardButton(text="📄 CSV", callback_data="export_csv"),
            ],
            [InlineKeyboardButton(text="🏠 Головна", callback_data=CallbackData.BACK_MAIN)],
        ]
    )


def budget_menu_kb():
    """Меню бюджетів"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Новий бюджет", callback_data=CallbackData.SET_BUDGET)],
            [InlineKeyboardButton(text="📋 Мої бюджети", callback_data=CallbackData.VIEW_BUDGETS)],
            [InlineKeyboardButton(text="🏠 Головна", callback_data=CallbackData.BACK_MAIN)],
        ]
    )


def budget_period_kb():
    """Вибір періоду бюджету"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Місяць", callback_data="budget_period_month"),
                InlineKeyboardButton(text="📅 Рік", callback_data="budget_period_year"),
            ],
            [InlineKeyboardButton(text="✖️ Відмінити", callback_data=CallbackData.CANCEL)],
        ]
    )


def back_button_kb():
    """Кнопка повернення на головну"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Головна", callback_data=CallbackData.BACK_MAIN)],
        ]
    )


def date_select_kb():
    """Вибір дати транзакції"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Сьогодні", callback_data="trans_date_today"),
                InlineKeyboardButton(text="Вчора", callback_data="trans_date_yesterday"),
            ],
            [InlineKeyboardButton(text="Пропустити (сьогодні)", callback_data="trans_date_skip")],
            [InlineKeyboardButton(text="✖️ Відмінити", callback_data=CallbackData.CANCEL)],
        ]
    )


def cancel_button_kb():
    """Кнопка скасування"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✖️ Відмінити", callback_data=CallbackData.CANCEL)],
        ]
    )


def balance_actions_kb():
    """Швидкі дії з балансу"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💸 Витрата", callback_data=CallbackData.ADD_EXPENSE),
                InlineKeyboardButton(text="💰 Дохід", callback_data=CallbackData.ADD_INCOME),
            ],
            [
                InlineKeyboardButton(text="📝 Історія", callback_data=CallbackData.VIEW_HISTORY),
                InlineKeyboardButton(text="📊 Звіт", callback_data="report_month"),
            ],
            [
                InlineKeyboardButton(text="📈 Графіки", callback_data=CallbackData.CHARTS),
                InlineKeyboardButton(text="🏠 Головна", callback_data=CallbackData.BACK_MAIN),
            ],
        ]
    )


def transaction_success_kb():
    """Дії після додавання транзакції"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Ще витрата", callback_data=CallbackData.ADD_EXPENSE),
                InlineKeyboardButton(text="💰 Дохід", callback_data=CallbackData.ADD_INCOME),
            ],
            [
                InlineKeyboardButton(text="📊 Баланс", callback_data=CallbackData.BALANCE),
                InlineKeyboardButton(text="📝 Історія", callback_data=CallbackData.VIEW_HISTORY),
            ],
            [InlineKeyboardButton(text="🏠 Головна", callback_data=CallbackData.BACK_MAIN)],
        ]
    )


def budget_list_kb(budgets: list) -> InlineKeyboardMarkup:
    """Клавіатура з кнопками для списку бюджетів (delete -> confirmation)"""
    rows: list[list[InlineKeyboardButton]] = []
    for budget in budgets:
        budget_id = budget[0]
        rows.append([
            InlineKeyboardButton(text="✏️ Змінити", callback_data=f"edit_budget_{budget_id}"),
            InlineKeyboardButton(text="🗑 Видалити", callback_data=f"delete_budget_{budget_id}"),
        ])
    rows.append([
        InlineKeyboardButton(text="➕ Новий бюджет", callback_data=CallbackData.SET_BUDGET),
    ])
    rows.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data=CallbackData.BUDGETS),
        InlineKeyboardButton(text="🏠 Головна", callback_data=CallbackData.BACK_MAIN),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_delete_trans_kb(trans_id: int, page: int):
    """Клавіатура підтвердження видалення транзакції"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Так, видалити",
                    callback_data=f"confirm_del_trans_{trans_id}",
                ),
                InlineKeyboardButton(
                    text="Ні, скасувати",
                    callback_data=f"cancel_del_trans_{page}",
                ),
            ],
        ]
    )


def confirm_delete_budget_kb(budget_id: int):
    """Клавіатура підтвердження видалення бюджету"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Так, видалити",
                    callback_data=f"confirm_del_budget_{budget_id}",
                ),
                InlineKeyboardButton(
                    text="Ні, скасувати",
                    callback_data=CallbackData.CANCEL_DELETE_BUDGET,
                ),
            ],
        ]
    )


def history_navigation_kb(page: int, total_pages: int, transactions: list = None):
    """Навігація по історії транзакцій з кнопками видалення"""
    rows: list[list[InlineKeyboardButton]] = []
    if transactions:
        for trans in transactions:
            trans_id = trans[0]
            rows.append([
                InlineKeyboardButton(
                    text=f"🗑 Видалити ID:{trans_id}",
                    callback_data=f"delete_trans_{trans_id}_{page}",
                ),
            ])
    nav_buttons: list[InlineKeyboardButton] = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"history_page_{page - 1}"))
    nav_buttons.append(
        InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data=CallbackData.HISTORY_INFO),
    )
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"history_page_{page + 1}"))
    if nav_buttons:
        rows.append(nav_buttons)
    rows.append([InlineKeyboardButton(text="🏠 Головна", callback_data=CallbackData.BACK_MAIN)])
    return InlineKeyboardMarkup(inline_keyboard=rows)
