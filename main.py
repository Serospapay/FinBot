import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand

from config import BOT_TOKEN, EXPENSE_CATEGORIES, INCOME_CATEGORIES
from database import (
    init_db, add_user, add_transaction, get_balance, 
    set_budget, get_budgets, check_budget, delete_transaction,
    delete_budget, get_recent_transactions
)
from keyboards import (
    main_menu_kb, category_kb, reports_menu_kb, export_menu_kb,
    budget_menu_kb, budget_period_kb, charts_menu_kb, back_button_kb,
    quick_expense_kb, balance_actions_kb, main_reply_kb, quick_reply_kb,
    transaction_success_kb, transaction_item_kb, budget_item_kb,
    history_navigation_kb
)
from reports import (
    generate_report, get_period_dates, generate_pie_chart, 
    generate_dynamics_chart, export_to_excel, export_to_csv
)
from utils import validate_amount, get_safe_description, escape_html

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ініціалізація бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# FSM стани
class TransactionState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_description = State()


class BudgetState(StatesGroup):
    waiting_for_category = State()
    waiting_for_period = State()
    waiting_for_amount = State()


# Команда /start
@dp.message_handler(commands=['start'], state="*")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    await add_user(message.from_user.id, message.from_user.username)
    
    welcome_text = (
        f"👋 <b>Привіт, {message.from_user.first_name}!</b>\n\n"
        "🎯 Я допоможу тримати твої фінанси під контролем\n\n"
        "💸 <b>Швидко додавай</b> витрати і доходи\n"
        "📊 <b>Аналізуй</b> свої витрати візуально\n"
        "🎯 <b>Контролюй</b> бюджети з сповіщеннями\n"
        "📈 <b>Дивись</b> графіки і тренди\n\n"
        "Обери дію нижче 👇"
    )
    
    await message.answer(
        welcome_text, 
        parse_mode="HTML",
        reply_markup=main_reply_kb()  # Reply клавіатура завжди доступна
    )
    await message.answer(
        "💡 <b>Підказка:</b> Використовуй кнопки внизу для швидкого доступу!",
        parse_mode="HTML",
        reply_markup=main_menu_kb()  # Inline меню для деталей
    )


# Команда /menu
@dp.message_handler(commands=['menu'], state="*")
async def cmd_menu(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "🏠 <b>Головне меню</b>\n\n"
        "Оберіть дію:",
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )


# Команда /help
@dp.message_handler(commands=['help'], state="*")
async def cmd_help(message: types.Message, state: FSMContext):
    await state.finish()
    help_text = (
        "📖 <b>Довідка по боту</b>\n\n"
        
        "🎯 <b>Основні функції:</b>\n"
        "• Додавання доходів і витрат\n"
        "• Перегляд балансу та історії\n"
        "• Встановлення бюджетів\n"
        "• Графіки та звіти\n"
        "• Експорт даних у Excel/CSV\n\n"
        
        "💡 <b>Швидкі команди:</b>\n"
        "/start - Почати роботу\n"
        "/menu - Головне меню\n"
        "/balance - Швидкий баланс\n"
        "/help - Ця довідка\n\n"
        
        "🔧 <b>Корисні поради:</b>\n"
        "• Використовуй кнопки внизу для швидкого доступу\n"
        "• Історія транзакцій доступна через 📝 Історія\n"
        "• Видалення: /del_[ID] для транзакцій\n"
        "• Бюджети автоматично відстежуються\n"
        "• Всі дані зберігаються локально\n\n"
        
        "❓ <b>Питання?</b>\n"
        "Просто почни вводити суму або обери категорію!"
    )
    await message.answer(
        help_text,
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )


# ==================== ОБРОБКА REPLY КНОПОК ====================

@dp.message_handler(lambda m: m.text == "💸 Витрата", state="*")
async def reply_add_expense(message: types.Message, state: FSMContext):
    # Очищаємо дані без finish() щоб не втратити можливість записати нові
    async with state.proxy() as data:
        data.clear()
        data['transaction_type'] = "expense"
    
    await message.answer(
        "💸 <b>Додати витрату</b>\n\n"
        "Оберіть категорію:",
        parse_mode="HTML",
        reply_markup=category_kb("expense")
    )


@dp.message_handler(lambda m: m.text == "💰 Дохід", state="*")
async def reply_add_income(message: types.Message, state: FSMContext):
    # Очищаємо дані без finish() щоб не втратити можливість записати нові
    async with state.proxy() as data:
        data.clear()
        data['transaction_type'] = "income"
    
    await message.answer(
        "💰 <b>Додати дохід</b>\n\n"
        "Оберіть категорію:",
        parse_mode="HTML",
        reply_markup=category_kb("income")
    )


@dp.message_handler(lambda m: m.text == "💳 Баланс", state="*")
async def reply_balance(message: types.Message, state: FSMContext):
    await state.finish()
    income, expense, balance = await get_balance(message.from_user.id)
    
    balance_emoji = "💚" if balance >= 0 else "❤️"
    
    balance_text = (
        f"{balance_emoji} <b>Ваш баланс</b>\n\n"
        f"📊 <b>{balance:,.2f}</b> грн\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📈 Доходи: <b>+{income:,.2f}</b> грн\n"
        f"📉 Витрати: <b>-{expense:,.2f}</b> грн\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    
    await message.answer(balance_text, parse_mode="HTML", reply_markup=balance_actions_kb())


@dp.message_handler(lambda m: m.text == "📊 Звіти", state="*")
async def reply_reports(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "📊 <b>Аналітика</b>\n\n"
        "Оберіть період:",
        parse_mode="HTML",
        reply_markup=reports_menu_kb()
    )


@dp.message_handler(lambda m: m.text == "🎯 Бюджети", state="*")
async def reply_budgets(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "🎯 <b>Бюджети</b>\n\n"
        "Управління бюджетами:",
        parse_mode="HTML",
        reply_markup=budget_menu_kb()
    )


@dp.message_handler(lambda m: m.text == "📤 Експорт", state="*")
async def reply_export(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "📤 <b>Експорт даних</b>\n\n"
        "Оберіть формат:",
        parse_mode="HTML",
        reply_markup=export_menu_kb()
    )


@dp.message_handler(lambda m: m.text == "📝 Історія", state="*")
async def reply_history(message: types.Message, state: FSMContext):
    await state.finish()
    await show_history_page(message.from_user.id, message, 1, is_new_message=True)


@dp.message_handler(lambda m: m.text == "⚡ Швидко", state="*")
async def reply_quick(message: types.Message, state: FSMContext):
    # Очищаємо дані без finish()
    async with state.proxy() as data:
        data.clear()
        data['transaction_type'] = "expense"
    
    await message.answer(
        "⚡ <b>Швидкі витрати</b>\n\n"
        "Оберіть категорію одним кліком:",
        parse_mode="HTML",
        reply_markup=quick_expense_kb()
    )


# Обробка швидких категорій через Reply
@dp.message_handler(lambda m: m.text in ["🍔 Їжа", "☕ Кава", "🚗 Транспорт", "🎮 Розваги", "🏠 Житло", "💊 Здоров'я"], state="*")
async def reply_quick_category(message: types.Message, state: FSMContext):
    # Мапінг кнопок на категорії
    category_map = {
        "🍔 Їжа": "🍔 Їжа",
        "☕ Кава": "🍔 Їжа",
        "🚗 Транспорт": "🚗 Транспорт",
        "🎮 Розваги": "🎮 Розваги",
        "🏠 Житло": "🏠 Житло",
        "💊 Здоров'я": "💊 Здоров'я"
    }
    
    category = category_map.get(message.text)
    
    async with state.proxy() as data:
        data['category'] = category
        data['transaction_type'] = "expense"
    await TransactionState.waiting_for_amount.set()
    
    await message.answer(
        f"⚡ <b>Швидка витрата</b>\n\n"
        f"📁 {category}\n"
        f"💵 Введіть суму:",
        parse_mode="HTML",
        reply_markup=main_reply_kb()
    )


@dp.message_handler(lambda m: m.text == "« Назад", state="*")
async def reply_back(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "🏠 Головне меню",
        reply_markup=main_reply_kb()
    )


# Команда /balance
@dp.message_handler(commands=['balance'], state="*")
async def cmd_balance(message: types.Message, state: FSMContext):
    await state.finish()
    income, expense, balance = await get_balance(message.from_user.id)
    
    balance_emoji = "💚" if balance >= 0 else "❤️"
    
    balance_text = (
        f"{balance_emoji} <b>Ваш баланс</b>\n\n"
        f"📊 <b>{balance:,.2f}</b> грн\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📈 Доходи: <b>+{income:,.2f}</b> грн\n"
        f"📉 Витрати: <b>-{expense:,.2f}</b> грн\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    
    await message.answer(balance_text, parse_mode="HTML", reply_markup=balance_actions_kb())


# ==================== БЮДЖЕТИ (handlers повинні бути ДО загальних) ====================

# Встановити бюджет
@dp.callback_query_handler(lambda c: c.data == "set_budget", state="*")
async def set_budget_start(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await BudgetState.waiting_for_category.set()
    await callback.message.edit_text(
        "🎯 <b>Встановити бюджет</b>\n\n"
        "Оберіть категорію витрат:",
        parse_mode="HTML",
        reply_markup=category_kb("expense")
    )
    await callback.answer()


# Вибір категорії для бюджету (ПЕРЕД загальним handler)
@dp.callback_query_handler(lambda c: c.data.startswith("cat_expense_"), state=BudgetState.waiting_for_category)
async def budget_select_category(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.replace("cat_expense_", "")
    await state.update_data(budget_category=category)
    await BudgetState.waiting_for_period.set()
    
    await callback.message.edit_text(
        f"🎯 <b>Встановити бюджет</b>\n\n"
        f"📁 Категорія: {category}\n\n"
        "Оберіть період бюджету:",
        parse_mode="HTML",
        reply_markup=budget_period_kb()
    )
    await callback.answer()


# Вибір періоду бюджету
@dp.callback_query_handler(lambda c: c.data.startswith("budget_period_"), state=BudgetState.waiting_for_period)
async def budget_select_period(callback: types.CallbackQuery, state: FSMContext):
    period = callback.data.replace("budget_period_", "")
    await state.update_data(budget_period=period)
    
    period_name = "місячний" if period == "month" else "річний"
    await BudgetState.waiting_for_amount.set()
    
    data = await state.get_data()
    category = data.get('budget_category', 'Невідома')
    
    await callback.message.edit_text(
        f"🎯 <b>Встановити бюджет</b>\n\n"
        f"📁 Категорія: {category}\n"
        f"📅 Період: {period_name}\n\n"
        f"💵 Введіть суму бюджету (грн):",
        parse_mode="HTML"
    )
    await callback.answer()


# Отримання суми бюджету
@dp.message_handler(state=BudgetState.waiting_for_amount)
async def budget_process_amount(message: types.Message, state: FSMContext):
    is_valid, amount = validate_amount(message.text)
    
    if not is_valid:
        await message.answer(
            "❌ Помилка! Введіть коректну суму.\n"
            "Приклади: 5000, 10000.50\n"
            "Максимальна сума: 1,000,000,000 грн"
        )
        return
    
    data = await state.get_data()
    category = data.get('budget_category')
    period = data.get('budget_period')
    
    if not category or not period:
        await message.answer(
            "❌ Помилка! Спробуйте ще раз.",
            reply_markup=budget_menu_kb()
        )
        await state.finish()
        return
    
    try:
        await set_budget(message.from_user.id, category, amount, period)
        
        period_name = "місячний" if period == "month" else "річний"
        await message.answer(
            f"✅ <b>Бюджет встановлено!</b>\n\n"
            f"📁 Категорія: {category}\n"
            f"📅 Період: {period_name}\n"
            f"💵 Сума: {amount:.2f} грн",
            parse_mode="HTML",
            reply_markup=budget_menu_kb()
        )
    except Exception as e:
        logger.error(f"Помилка встановлення бюджету: {e}")
        await message.answer(
            "❌ Помилка встановлення бюджету. Спробуйте пізніше.",
            reply_markup=budget_menu_kb()
        )
    finally:
        await state.finish()


# ==================== ТРАНЗАКЦІЇ ====================

# Додавання витрати
@dp.callback_query_handler(lambda c: c.data == "add_expense", state="*")
async def add_expense(callback: types.CallbackQuery, state: FSMContext):
    # Очищаємо дані без finish()
    async with state.proxy() as data:
        data.clear()
        data['transaction_type'] = "expense"
    
    await callback.message.edit_text(
        "💸 <b>Додати витрату</b>\n\n"
        "➜ Оберіть категорію:",
        parse_mode="HTML",
        reply_markup=category_kb("expense")
    )
    await callback.answer()


# Швидка витрата
@dp.callback_query_handler(lambda c: c.data == "quick_expense", state="*")
async def quick_expense(callback: types.CallbackQuery, state: FSMContext):
    # Очищаємо дані без finish()
    async with state.proxy() as data:
        data.clear()
        data['transaction_type'] = "expense"
    
    await callback.message.edit_text(
        "⚡ <b>Швидка витрата</b>\n\n"
        "Оберіть популярну категорію:",
        parse_mode="HTML",
        reply_markup=quick_expense_kb()
    )
    await callback.answer()


# Швидкий вибір категорії
@dp.callback_query_handler(lambda c: c.data.startswith("quick_cat_"), state="*")
async def quick_category(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_", 3)
    if len(parts) < 4:
        await callback.answer("❌ Помилка вибору категорії")
        return
        
    trans_type = parts[2]
    category = parts[3]
    
    async with state.proxy() as data:
        data['category'] = category
        data['transaction_type'] = trans_type
    await TransactionState.waiting_for_amount.set()
    
    await callback.message.edit_text(
        f"⚡ <b>Швидка витрата</b>\n\n"
        f"📁 Категорія: {category}\n"
        f"💵 Введіть суму:",
        parse_mode="HTML"
    )
    await callback.answer()


# Додавання доходу
@dp.callback_query_handler(lambda c: c.data == "add_income", state="*")
async def add_income(callback: types.CallbackQuery, state: FSMContext):
    # Очищаємо дані без finish()
    async with state.proxy() as data:
        data.clear()
        data['transaction_type'] = "income"
    
    await callback.message.edit_text(
        "💰 <b>Додати дохід</b>\n\n"
        "➜ Оберіть категорію:",
        parse_mode="HTML",
        reply_markup=category_kb("income")
    )
    await callback.answer()


# Вибір категорії для транзакцій (має бути ПІСЛЯ бюджетних handlers)
@dp.callback_query_handler(lambda c: c.data.startswith("cat_"), state="*")
async def select_category(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_", 2)
    if len(parts) < 3:
        await callback.answer("❌ Помилка вибору категорії")
        return
        
    trans_type = parts[1]
    category = parts[2]
    
    # Отримуємо існуючий transaction_type або використовуємо з callback
    data = await state.get_data()
    existing_type = data.get('transaction_type', trans_type)
    
    async with state.proxy() as data:
        data['category'] = category
        data['transaction_type'] = existing_type
    await TransactionState.waiting_for_amount.set()
    
    emoji = "💸" if existing_type == "expense" else "💰"
    trans_name = "Витрата" if existing_type == "expense" else "Дохід"
    
    await callback.message.edit_text(
        f"{emoji} <b>{trans_name}</b>\n\n"
        f"📁 Категорія: {category}\n"
        f"💵 Введіть суму:",
        parse_mode="HTML"
    )
    await callback.answer()


# Отримання суми
@dp.message_handler(state=TransactionState.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    is_valid, amount = validate_amount(message.text)
    
    if not is_valid:
        await message.answer(
            "❌ Помилка! Введіть коректну суму.\n"
            "Приклади: 100, 99.50, 1000\n"
            "Максимальна сума: 1,000,000,000 грн"
        )
        return
    
    # Додаємо amount через proxy для надійності
    async with state.proxy() as data:
        data['amount'] = amount
    
    await TransactionState.waiting_for_description.set()
    
    await message.answer(
        "📝 Введіть опис транзакції (або надішліть '-' щоб пропустити):"
    )


# Отримання опису
@dp.message_handler(state=TransactionState.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    # Показуємо індикатор процесу
    processing_msg = await message.answer("⏳ Обробка транзакції...")
    
    description = get_safe_description(message.text)
    
    data = await state.get_data()
    trans_type = data.get('transaction_type')
    category = data.get('category')
    amount = data.get('amount')
    
    if not trans_type or not category or not amount:
        await processing_msg.delete()
        await message.answer(
            "❌ Помилка! Спробуйте ще раз.",
            reply_markup=main_menu_kb()
        )
        await state.finish()
        return
    
    try:
        await add_transaction(
            message.from_user.id,
            trans_type,
            amount,
            category,
            description
        )
        
        # Отримуємо оновлений баланс
        income, expense, balance = await get_balance(message.from_user.id)
        
        emoji = "📉" if trans_type == "expense" else "📈"
        trans_name = "Витрата" if trans_type == "expense" else "Дохід"
        
        safe_desc = escape_html(description) if description else 'Не вказано'
        
        # Видаляємо індикатор і показуємо результат
        await processing_msg.delete()
        
        success_text = (
            f"✅ {emoji} <b>{trans_name} додана!</b>\n\n"
            f"📁 Категорія: {category}\n"
            f"💵 Сума: {amount:.2f} грн\n"
            f"📝 Опис: {safe_desc}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>Новий баланс: {balance:,.2f} грн</b>"
        )
        
        await message.answer(
            success_text,
            parse_mode="HTML",
            reply_markup=transaction_success_kb()
        )
        
        # Перевірка бюджету
        if trans_type == "expense":
            await check_and_notify_budget(message, category)
    except Exception as e:
        logger.error(f"Помилка додавання транзакції: {e}")
        await processing_msg.delete()
        await message.answer(
            "❌ Помилка збереження транзакції. Спробуйте пізніше.",
            reply_markup=main_menu_kb()
        )
    finally:
        await state.finish()


async def check_and_notify_budget(message: types.Message, category: str):
    """Перевірка та сповіщення про бюджет"""
    try:
        user_id = message.from_user.id
        
        # Перевірити місячний бюджет
        today = datetime.now()
        start_of_month = today.replace(day=1).strftime('%Y-%m-%d')
        end_of_month = today.strftime('%Y-%m-%d')
        
        budget_amount, spent_amount = await check_budget(
            user_id, category, "month", start_of_month, end_of_month
        )
        
        if budget_amount and budget_amount > 0:
            percentage = (spent_amount / budget_amount) * 100
            
            if percentage >= 100:
                await message.answer(
                    f"⚠️ <b>Увага!</b> Бюджет на категорію {category} перевищено!\n"
                    f"Витрачено: {spent_amount:.2f} / {budget_amount:.2f} грн ({percentage:.1f}%)",
                    parse_mode="HTML"
                )
            elif percentage >= 80:
                await message.answer(
                    f"⚠️ Увага! Ви витратили {percentage:.1f}% бюджету на {category}\n"
                    f"Витрачено: {spent_amount:.2f} / {budget_amount:.2f} грн",
                    parse_mode="HTML"
                )
    except Exception as e:
        logger.error(f"Помилка перевірки бюджету: {e}")


# ==================== ЗВІТИ ТА АНАЛІТИКА ====================

# Баланс
@dp.callback_query_handler(lambda c: c.data == "balance", state="*")
async def show_balance(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    income, expense, balance = await get_balance(callback.from_user.id)
    
    balance_emoji = "💚" if balance >= 0 else "❤️"
    
    balance_text = (
        f"{balance_emoji} <b>Ваш баланс</b>\n\n"
        f"📊 <b>{balance:,.2f}</b> грн\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📈 Доходи: <b>+{income:,.2f}</b> грн\n"
        f"📉 Витрати: <b>-{expense:,.2f}</b> грн\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    
    await callback.message.edit_text(
        balance_text, 
        parse_mode="HTML", 
        reply_markup=balance_actions_kb()
    )
    await callback.answer()


# Звіти
@dp.callback_query_handler(lambda c: c.data == "reports", state="*")
async def show_reports(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.edit_text(
        "📊 <b>Аналітика</b>\n\n"
        "➜ Оберіть період для аналізу:",
        parse_mode="HTML",
        reply_markup=reports_menu_kb()
    )
    await callback.answer()


# Генерація звіту
@dp.callback_query_handler(lambda c: c.data.startswith("report_"))
async def generate_report_handler(callback: types.CallbackQuery):
    period = callback.data.replace("report_", "")
    start_date, end_date, period_name = get_period_dates(period)
    
    await callback.answer("⏳ Генерую звіт...")
    
    try:
        report = await generate_report(
            callback.from_user.id,
            start_date,
            end_date,
            period_name
        )
        
        await callback.message.edit_text(
            report,
            parse_mode="HTML",
            reply_markup=reports_menu_kb()
        )
    except Exception as e:
        logger.error(f"Помилка генерації звіту: {e}")
        await callback.message.answer(
            "❌ Помилка генерації звіту. Спробуйте пізніше.",
            reply_markup=reports_menu_kb()
        )


# Графіки
@dp.callback_query_handler(lambda c: c.data == "charts", state="*")
async def show_charts(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.edit_text(
        "📈 <b>Графічна аналітика</b>\n\n"
        "Оберіть тип графіка:",
        parse_mode="HTML",
        reply_markup=charts_menu_kb()
    )
    await callback.answer()


# Генерація кругової діаграми витрат
@dp.callback_query_handler(lambda c: c.data == "chart_expense_month")
async def chart_expense(callback: types.CallbackQuery):
    await callback.answer("⏳ Генерую графік...")
    
    try:
        chart = await generate_pie_chart(callback.from_user.id, "expense", "останній місяць")
        
        if chart:
            await callback.message.answer_photo(
                photo=chart,
                caption="🥧 Витрати за останній місяць",
                reply_markup=charts_menu_kb()
            )
        else:
            await callback.message.answer(
                "❌ Недостатньо даних для побудови графіка.\n"
                "Додайте транзакції, щоб побачити аналітику.",
                reply_markup=charts_menu_kb()
            )
    except Exception as e:
        logger.error(f"Помилка генерації графіка витрат: {e}")
        await callback.message.answer(
            "❌ Помилка генерації графіка. Спробуйте пізніше.",
            reply_markup=charts_menu_kb()
        )


# Генерація кругової діаграми доходів
@dp.callback_query_handler(lambda c: c.data == "chart_income_month")
async def chart_income(callback: types.CallbackQuery):
    await callback.answer("⏳ Генерую графік...")
    
    try:
        chart = await generate_pie_chart(callback.from_user.id, "income", "останній місяць")
        
        if chart:
            await callback.message.answer_photo(
                photo=chart,
                caption="🥧 Доходи за останній місяць",
                reply_markup=charts_menu_kb()
            )
        else:
            await callback.message.answer(
                "❌ Недостатньо даних для побудови графіка.\n"
                "Додайте транзакції, щоб побачити аналітику.",
                reply_markup=charts_menu_kb()
            )
    except Exception as e:
        logger.error(f"Помилка генерації графіка доходів: {e}")
        await callback.message.answer(
            "❌ Помилка генерації графіка. Спробуйте пізніше.",
            reply_markup=charts_menu_kb()
        )


# Генерація графіка динаміки
@dp.callback_query_handler(lambda c: c.data == "chart_dynamics_year")
async def chart_dynamics(callback: types.CallbackQuery):
    await callback.answer("⏳ Генерую графік...")
    
    try:
        chart = await generate_dynamics_chart(callback.from_user.id)
        
        if chart:
            await callback.message.answer_photo(
                photo=chart,
                caption="📊 Динаміка доходів та витрат за рік",
                reply_markup=charts_menu_kb()
            )
        else:
            await callback.message.answer(
                "❌ Недостатньо даних для побудови графіка.\n"
                "Додайте транзакції, щоб побачити динаміку.",
                reply_markup=charts_menu_kb()
            )
    except Exception as e:
        logger.error(f"Помилка генерації графіка динаміки: {e}")
        await callback.message.answer(
            "❌ Помилка генерації графіка. Спробуйте пізніше.",
            reply_markup=charts_menu_kb()
        )


# ==================== ІСТОРІЯ ТРАНЗАКЦІЙ ====================

# Перегляд історії
@dp.callback_query_handler(lambda c: c.data == "view_history", state="*")
async def view_history(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await show_history_page(callback.from_user.id, callback.message, 1)
    await callback.answer()


# Навігація по сторінках історії
@dp.callback_query_handler(lambda c: c.data.startswith("history_page_"))
async def history_page_handler(callback: types.CallbackQuery):
    page = int(callback.data.replace("history_page_", ""))
    await show_history_page(callback.from_user.id, callback.message, page)
    await callback.answer()


async def show_history_page(user_id: int, message: types.Message, page: int = 1, is_new_message: bool = False):
    """Показати сторінку історії транзакцій"""
    try:
        per_page = 5
        offset = (page - 1) * per_page
        
        transactions, total_count = await get_recent_transactions(user_id, per_page, offset)
        
        if not transactions:
            text = (
                "📝 <b>Історія транзакцій</b>\n\n"
                "❌ У вас поки немає транзакцій.\n"
                "Почніть додавати доходи та витрати!"
            )
            if is_new_message:
                await message.answer(text, parse_mode="HTML", reply_markup=back_button_kb())
            else:
                await message.edit_text(text, parse_mode="HTML", reply_markup=back_button_kb())
            return
        
        total_pages = (total_count + per_page - 1) // per_page
        
        text = f"📝 <b>Історія транзакцій</b>\n"
        text += f"<i>Сторінка {page} з {total_pages} (всього: {total_count})</i>\n\n"
        
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
        
        if is_new_message:
            await message.answer(
                text,
                parse_mode="HTML",
                reply_markup=history_navigation_kb(page, total_pages)
            )
        else:
            await message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=history_navigation_kb(page, total_pages)
            )
    except Exception as e:
        logger.error(f"Помилка показу історії: {e}")


# Видалення транзакції
@dp.message_handler(lambda m: m.text and m.text.startswith("/del_"), state="*")
async def delete_transaction_cmd(message: types.Message, state: FSMContext):
    """Видалення транзакції через команду"""
    try:
        trans_id = int(message.text.replace("/del_", ""))
        success = await delete_transaction(trans_id, message.from_user.id)
        
        if success:
            await message.answer(
                "✅ Транзакцію успішно видалено!",
                reply_markup=main_menu_kb()
            )
        else:
            await message.answer(
                "❌ Помилка видалення транзакції.",
                reply_markup=main_menu_kb()
            )
    except Exception as e:
        logger.error(f"Помилка видалення транзакції: {e}")
        await message.answer(
            "❌ Помилка видалення транзакції.",
            reply_markup=main_menu_kb()
        )


# ==================== ЕКСПОРТ ====================

# Експорт
@dp.callback_query_handler(lambda c: c.data == "export", state="*")
async def show_export(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.edit_text(
        "📤 <b>Експорт даних</b>\n\n"
        "Оберіть формат для експорту:",
        parse_mode="HTML",
        reply_markup=export_menu_kb()
    )
    await callback.answer()


# Експорт в Excel
@dp.callback_query_handler(lambda c: c.data == "export_excel")
async def export_excel_handler(callback: types.CallbackQuery):
    await callback.answer("⏳ Генерую файл...")
    
    try:
        excel_file = await export_to_excel(callback.from_user.id)
        
        if excel_file:
            filename = f"finance_{datetime.now().strftime('%Y%m%d')}.xlsx"
            await callback.message.answer_document(
                document=(filename, excel_file),
                caption="📊 Ваші фінансові дані в форматі Excel",
                reply_markup=export_menu_kb()
            )
        else:
            await callback.message.answer(
                "❌ Немає даних для експорту.\n"
                "Додайте транзакції, щоб експортувати дані.",
                reply_markup=export_menu_kb()
            )
    except Exception as e:
        logger.error(f"Помилка експорту в Excel: {e}")
        await callback.message.answer(
            "❌ Помилка експорту даних. Спробуйте пізніше.",
            reply_markup=export_menu_kb()
        )


# Експорт в CSV
@dp.callback_query_handler(lambda c: c.data == "export_csv")
async def export_csv_handler(callback: types.CallbackQuery):
    await callback.answer("⏳ Генерую файл...")
    
    try:
        csv_file = await export_to_csv(callback.from_user.id)
        
        if csv_file:
            filename = f"finance_{datetime.now().strftime('%Y%m%d')}.csv"
            await callback.message.answer_document(
                document=(filename, csv_file),
                caption="📄 Ваші фінансові дані в форматі CSV",
                reply_markup=export_menu_kb()
            )
        else:
            await callback.message.answer(
                "❌ Немає даних для експорту.\n"
                "Додайте транзакції, щоб експортувати дані.",
                reply_markup=export_menu_kb()
            )
    except Exception as e:
        logger.error(f"Помилка експорту в CSV: {e}")
        await callback.message.answer(
            "❌ Помилка експорту даних. Спробуйте пізніше.",
            reply_markup=export_menu_kb()
        )


# ==================== БЮДЖЕТИ ====================

# Бюджети
@dp.callback_query_handler(lambda c: c.data == "budgets", state="*")
async def show_budgets_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.edit_text(
        "🎯 <b>Бюджети</b>\n\n"
        "Встановлюйте бюджети для контролю витрат:",
        parse_mode="HTML",
        reply_markup=budget_menu_kb()
    )
    await callback.answer()


# Переглянути бюджети
@dp.callback_query_handler(lambda c: c.data == "view_budgets")
async def view_budgets(callback: types.CallbackQuery):
    budgets = await get_budgets(callback.from_user.id)
    
    if not budgets:
        await callback.message.edit_text(
            "❌ У вас ще немає встановлених бюджетів.\n\n"
            "Встановіть бюджет, щоб контролювати витрати!",
            reply_markup=budget_menu_kb()
        )
        await callback.answer()
        return
    
    text = "🎯 <b>Ваші бюджети:</b>\n\n"
    
    for budget in budgets:
        budget_id = budget[0]
        category = budget[2]
        amount = budget[3]
        period = budget[4]
        period_name = "Місяць" if period == "month" else "Рік"
        
        # Перевірити виконання бюджету
        today = datetime.now()
        if period == "month":
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
        else:
            start_date = today.replace(month=1, day=1).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        
        _, spent = await check_budget(
            callback.from_user.id, category, period, start_date, end_date
        )
        
        spent = spent or 0
        percentage = (spent / amount) * 100 if amount > 0 else 0
        status_emoji = "🟢" if percentage < 80 else "🟡" if percentage < 100 else "🔴"
        
        text += f"{status_emoji} <b>{category}</b>\n"
        text += f"   Бюджет: {amount:,.2f} грн ({period_name})\n"
        text += f"   Витрачено: {spent:,.2f} грн ({percentage:.1f}%)\n"
        text += f"   Залишок: {max(0, amount - spent):,.2f} грн\n"
        text += f"   /del_budget_{budget_id} - видалити\n\n"
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=budget_menu_kb()
    )
    await callback.answer()


# Видалення бюджету
@dp.message_handler(lambda m: m.text and m.text.startswith("/del_budget_"), state="*")
async def delete_budget_cmd(message: types.Message, state: FSMContext):
    """Видалення бюджету через команду"""
    try:
        budget_id = int(message.text.replace("/del_budget_", ""))
        success = await delete_budget(budget_id, message.from_user.id)
        
        if success:
            await message.answer(
                "✅ Бюджет успішно видалено!",
                reply_markup=budget_menu_kb()
            )
        else:
            await message.answer(
                "❌ Помилка видалення бюджету.",
                reply_markup=budget_menu_kb()
            )
    except Exception as e:
        logger.error(f"Помилка видалення бюджету: {e}")
        await message.answer(
            "❌ Помилка видалення бюджету.",
            reply_markup=budget_menu_kb()
        )


# ==================== НАВІГАЦІЯ ====================

# Повернутися до головного меню
@dp.callback_query_handler(lambda c: c.data == "back_main", state="*")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    try:
        await callback.message.edit_text(
            "🏠 <b>Головне меню</b>\n\n"
            "Оберіть дію:",
            parse_mode="HTML",
            reply_markup=main_menu_kb()
        )
    except:
        await callback.message.answer(
            "🏠 <b>Головне меню</b>\n\n"
            "Оберіть дію:",
            parse_mode="HTML",
            reply_markup=main_menu_kb()
        )
    await callback.answer()


# Скасування
@dp.callback_query_handler(lambda c: c.data == "cancel", state="*")
async def cancel_action(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    try:
        await callback.message.edit_text(
            "✖️ Скасовано"
        )
    except:
        await callback.message.answer("✖️ Скасовано")
    await callback.answer()


# Головна функція
async def on_startup(dp):
    try:
        await init_db()
        logger.info("✅ База даних ініціалізована")
        
        # Встановлюємо команди бота (меню з кнопкою)
        commands = [
            BotCommand(command="start", description="🏠 Почати роботу"),
            BotCommand(command="menu", description="📋 Головне меню"),
            BotCommand(command="balance", description="💳 Мій баланс"),
            BotCommand(command="help", description="❓ Довідка")
        ]
        await bot.set_my_commands(commands)
        logger.info("✅ Команди бота встановлено")
        
        logger.info("✅ Бот запущено успішно")
    except Exception as e:
        logger.error(f"❌ Помилка запуску: {e}")
        raise


if __name__ == "__main__":
    import sys
    from aiogram import executor
    
    # Виправлення для Python 3.10+
    if sys.platform == 'win32' and sys.version_info >= (3, 10):
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except AttributeError:
            pass
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
