import logging
from contextlib import asynccontextmanager
from datetime import datetime

import aiosqlite

from config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_connection():
    """
    Контекстний менеджер для отримання з'єднання з БД.
    Для SQLite кожен запит створює нове з'єднання (легковагове).
    При міграції на PostgreSQL можна додати connection pool.
    """
    async with aiosqlite.connect(settings.DB_NAME) as conn:
        yield conn


async def init_db():
    """Ініціалізація бази даних"""
    try:
        async with get_connection() as db:
            # Таблиця користувачів
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблиця транзакцій
            await db.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                    amount REAL NOT NULL CHECK(amount > 0),
                    category TEXT NOT NULL,
                    description TEXT,
                    date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Індекси для оптимізації
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_transactions_user_date 
                ON transactions(user_id, date)
            ''')
            
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_transactions_user_type 
                ON transactions(user_id, type)
            ''')
            
            # Таблиця бюджетів
            await db.execute('''
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL CHECK(amount > 0),
                    period TEXT NOT NULL CHECK(period IN ('month', 'year')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    UNIQUE(user_id, category, period)
                )
            ''')
            
            await db.commit()
    except Exception as e:
        logger.error("Помилка ініціалізації БД: %s", e)
        raise


async def add_user(user_id: int, username: str = None):
    """Додати користувача"""
    try:
        async with get_connection() as db:
            await db.execute(
                'INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
                (user_id, username)
            )
            await db.commit()
    except Exception as e:
        logger.error("Помилка додавання користувача: %s", e)


async def add_transaction(user_id: int, trans_type: str, amount: float, 
                         category: str, description: str = None, date: str = None):
    """Додати транзакцію"""
    try:
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        async with get_connection() as db:
            await db.execute(
                '''INSERT INTO transactions (user_id, type, amount, category, description, date)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (user_id, trans_type, amount, category, description, date)
            )
            await db.commit()
    except Exception as e:
        logger.error("Помилка додавання транзакції: %s", e)
        raise


async def get_transactions(user_id: int, start_date: str = None, end_date: str = None, 
                          trans_type: str = None):
    """Отримати транзакції користувача"""
    try:
        async with get_connection() as db:
            query = 'SELECT * FROM transactions WHERE user_id = ?'
            params = [user_id]
            
            if start_date:
                query += ' AND date >= ?'
                params.append(start_date)
            
            if end_date:
                query += ' AND date <= ?'
                params.append(end_date)
            
            if trans_type:
                query += ' AND type = ?'
                params.append(trans_type)
            
            query += ' ORDER BY date DESC, created_at DESC'
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return rows
    except Exception as e:
        logger.error("Помилка отримання транзакцій: %s", e)
        return []


async def get_balance(user_id: int):
    """Отримати баланс користувача (один запит)"""
    try:
        async with get_connection() as db:
            async with db.execute(
                """SELECT
                    COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0),
                    COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0)
                FROM transactions WHERE user_id = ?""",
                (user_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    total_income, total_expense = row[0], row[1]
                    return total_income, total_expense, total_income - total_expense
            return 0, 0, 0
    except Exception as e:
        logger.error("Помилка отримання балансу: %s", e)
        return 0, 0, 0


async def get_category_summary(user_id: int, start_date: str, end_date: str, trans_type: str):
    """Отримати підсумок по категоріях"""
    try:
        async with get_connection() as db:
            async with db.execute(
                '''SELECT category, SUM(amount) as total, COUNT(*) as count
                   FROM transactions 
                   WHERE user_id = ? AND type = ? AND date BETWEEN ? AND ?
                   GROUP BY category
                   ORDER BY total DESC''',
                (user_id, trans_type, start_date, end_date)
            ) as cursor:
                rows = await cursor.fetchall()
                return rows
    except Exception as e:
        logger.error("Помилка отримання підсумку: %s", e)
        return []


async def set_budget(user_id: int, category: str, amount: float, period: str):
    """Встановити бюджет"""
    try:
        async with get_connection() as db:
            await db.execute(
                '''INSERT OR REPLACE INTO budgets (user_id, category, amount, period)
                   VALUES (?, ?, ?, ?)''',
                (user_id, category, amount, period)
            )
            await db.commit()
    except Exception as e:
        logger.error("Помилка встановлення бюджету: %s", e)
        raise


async def get_budgets(user_id: int, period: str = None):
    """Отримати бюджети"""
    try:
        async with get_connection() as db:
            if period:
                async with db.execute(
                    'SELECT * FROM budgets WHERE user_id = ? AND period = ?',
                    (user_id, period)
                ) as cursor:
                    return await cursor.fetchall()
            else:
                async with db.execute(
                    'SELECT * FROM budgets WHERE user_id = ?',
                    (user_id,)
                ) as cursor:
                    return await cursor.fetchall()
    except Exception as e:
        logger.error("Помилка отримання бюджетів: %s", e)
        return []


async def check_budget(user_id: int, category: str, period: str, start_date: str, end_date: str):
    """Перевірити виконання бюджету"""
    try:
        async with get_connection() as db:
            # Отримати бюджет
            async with db.execute(
                'SELECT amount FROM budgets WHERE user_id = ? AND category = ? AND period = ?',
                (user_id, category, period)
            ) as cursor:
                budget_row = await cursor.fetchone()
                if not budget_row:
                    return None, None
                budget_amount = budget_row[0]
            
            # Отримати витрати
            async with db.execute(
                '''SELECT COALESCE(SUM(amount), 0) FROM transactions 
                   WHERE user_id = ? AND category = ? AND type = "expense" 
                   AND date BETWEEN ? AND ?''',
                (user_id, category, start_date, end_date)
            ) as cursor:
                spent_row = await cursor.fetchone()
                spent_amount = spent_row[0] if spent_row else 0
            
            return budget_amount, spent_amount
    except Exception as e:
        logger.error("Помилка перевірки бюджету: %s", e)
        return None, None


async def delete_transaction(transaction_id: int, user_id: int):
    """Видалити транзакцію"""
    try:
        async with get_connection() as db:
            await db.execute(
                'DELETE FROM transactions WHERE id = ? AND user_id = ?',
                (transaction_id, user_id)
            )
            await db.commit()
            return True
    except Exception as e:
        logger.error("Помилка видалення транзакції: %s", e)
        return False


async def delete_budget(budget_id: int, user_id: int):
    """Видалити бюджет"""
    try:
        async with get_connection() as db:
            await db.execute(
                'DELETE FROM budgets WHERE id = ? AND user_id = ?',
                (budget_id, user_id)
            )
            await db.commit()
            return True
    except Exception as e:
        logger.error("Помилка видалення бюджету: %s", e)
        return False


async def get_recent_transactions(user_id: int, limit: int = 10, offset: int = 0):
    """Отримати останні транзакції з пагінацією"""
    try:
        async with get_connection() as db:
            # Отримати транзакції
            async with db.execute(
                '''SELECT * FROM transactions 
                   WHERE user_id = ? 
                   ORDER BY date DESC, created_at DESC 
                   LIMIT ? OFFSET ?''',
                (user_id, limit, offset)
            ) as cursor:
                transactions = await cursor.fetchall()
            
            # Отримати загальну кількість
            async with db.execute(
                'SELECT COUNT(*) FROM transactions WHERE user_id = ?',
                (user_id,)
            ) as cursor:
                total = await cursor.fetchone()
                total_count = total[0] if total else 0
            
            return transactions, total_count
    except Exception as e:
        logger.error("Помилка отримання транзакцій: %s", e)
        return [], 0
