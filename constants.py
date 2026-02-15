"""Константи та Enum для callback_data"""
from enum import StrEnum


class CallbackData(StrEnum):
    """Callback data для inline кнопок"""

    ADD_EXPENSE = "add_expense"
    ADD_INCOME = "add_income"
    QUICK_EXPENSE = "quick_expense"
    BALANCE = "balance"
    REPORTS = "reports"
    CHARTS = "charts"
    EXPORT = "export"
    BUDGETS = "budgets"
    SET_BUDGET = "set_budget"
    VIEW_BUDGETS = "view_budgets"
    VIEW_HISTORY = "view_history"
    BACK_MAIN = "back_main"
    CANCEL = "cancel"
    HISTORY_INFO = "history_info"

    # З префіксами (для динамічних callback)
    CAT_EXPENSE = "cat_expense_"
    CAT_INCOME = "cat_income_"
    CAT_PREFIX = "cat_"
    QUICK_CAT_PREFIX = "quick_cat_"
    REPORT_PREFIX = "report_"
    BUDGET_PERIOD_PREFIX = "budget_period_"
    HISTORY_PAGE_PREFIX = "history_page_"
    DELETE_TRANS_PREFIX = "delete_trans_"
    DELETE_BUDGET_PREFIX = "delete_budget_"
    EDIT_BUDGET_PREFIX = "edit_budget_"
    CONFIRM_DELETE_TRANS_PREFIX = "confirm_del_trans_"
    CONFIRM_DELETE_BUDGET_PREFIX = "confirm_del_budget_"
    CANCEL_DELETE_TRANS_PREFIX = "cancel_del_trans_"
    CANCEL_DELETE_BUDGET = "cancel_del_budget"

    # Chart types
    CHART_EXPENSE_MONTH = "chart_expense_month"
    CHART_INCOME_MONTH = "chart_income_month"
    CHART_DYNAMICS_YEAR = "chart_dynamics_year"

    # Export
    EXPORT_EXCEL = "export_excel"
    EXPORT_CSV = "export_csv"
