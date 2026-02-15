"""FSM стани для бота"""
from aiogram.fsm.state import State, StatesGroup


class TransactionState(StatesGroup):
    waiting_for_date = State()
    waiting_for_amount = State()
    waiting_for_description = State()


class BudgetState(StatesGroup):
    waiting_for_category = State()
    waiting_for_period = State()
    waiting_for_amount = State()
