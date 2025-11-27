import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
from database import get_transactions, get_category_summary, get_balance
import io

# Налаштування для українських символів
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False


async def generate_report(user_id: int, start_date: str, end_date: str, period_name: str):
    """Згенерувати текстовий звіт"""
    try:
        # Отримати баланс
        income_total, expense_total, balance = await get_balance(user_id)
        
        # Отримати транзакції за період
        transactions = await get_transactions(user_id, start_date, end_date)
        
        # Підрахувати за період
        period_income = sum(t[3] for t in transactions if t[2] == 'income')
        period_expense = sum(t[3] for t in transactions if t[2] == 'expense')
        
        # Отримати підсумок по категоріях
        expense_categories = await get_category_summary(user_id, start_date, end_date, 'expense')
        income_categories = await get_category_summary(user_id, start_date, end_date, 'income')
        
        # Формування звіту
        report = f"📊 <b>Звіт за період: {period_name}</b>\n"
        report += f"📅 З {start_date} по {end_date}\n\n"
        
        report += f"💰 <b>Загальний баланс:</b> {balance:,.2f} грн\n"
        report += f"📈 Всього доходів: {income_total:,.2f} грн\n"
        report += f"📉 Всього витрат: {expense_total:,.2f} грн\n\n"
        
        report += f"<b>За звітний період:</b>\n"
        report += f"➕ Доходи: {period_income:,.2f} грн\n"
        report += f"➖ Витрати: {period_expense:,.2f} грн\n"
        report += f"💵 Різниця: {period_income - period_expense:,.2f} грн\n\n"
        
        if expense_categories:
            report += "<b>📉 Витрати по категоріях:</b>\n"
            for cat, total, count in expense_categories:
                report += f"  {cat}: {total:,.2f} грн ({count} транз.)\n"
            report += "\n"
        
        if income_categories:
            report += "<b>📈 Доходи по категоріях:</b>\n"
            for cat, total, count in income_categories:
                report += f"  {cat}: {total:,.2f} грн ({count} транз.)\n"
            report += "\n"
        
        report += f"📊 Всього транзакцій за період: {len(transactions)}"
        
        return report
    except Exception as e:
        return f"❌ Помилка генерації звіту: {str(e)}"


async def generate_pie_chart(user_id: int, trans_type: str, period_name: str):
    """Згенерувати кругову діаграму витрат/доходів"""
    try:
        # Визначити дати (місяць)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Отримати дані
        categories = await get_category_summary(
            user_id, 
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d'),
            trans_type
        )
        
        if not categories or len(categories) == 0:
            return None
        
        # Підготовка даних
        labels = [cat[0] for cat in categories]
        sizes = [cat[1] for cat in categories]
        
        # Створення діаграми
        fig, ax = plt.subplots(figsize=(10, 8))
        colors = plt.cm.Set3(range(len(labels)))
        
        wedges, texts, autotexts = ax.pie(
            sizes, 
            labels=labels, 
            autopct='%1.1f%%', 
            colors=colors, 
            startangle=90
        )
        
        # Поліпшення читабельності
        for text in texts:
            text.set_fontsize(10)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(10)
        
        ax.axis('equal')
        
        title = f"{'Витрати' if trans_type == 'expense' else 'Доходи'} за {period_name}"
        plt.title(title, fontsize=16, fontweight='bold', pad=20)
        
        # Зберегти в пам'ять
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        return buf
    except Exception as e:
        print(f"Помилка генерації графіка: {e}")
        return None


async def generate_dynamics_chart(user_id: int):
    """Згенерувати графік динаміки за рік"""
    try:
        # Визначити дати
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        # Отримати транзакції
        transactions = await get_transactions(
            user_id,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        if not transactions or len(transactions) == 0:
            return None
        
        # Підготовка даних
        df = pd.DataFrame(transactions, columns=[
            'id', 'user_id', 'type', 'amount', 'category', 'description', 'date', 'created_at'
        ])
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.to_period('M')
        
        # Групування по місяцях
        monthly_income = df[df['type'] == 'income'].groupby('month')['amount'].sum()
        monthly_expense = df[df['type'] == 'expense'].groupby('month')['amount'].sum()
        
        # Перевірка чи є дані
        if len(monthly_income) == 0 and len(monthly_expense) == 0:
            return None
        
        # Створення всіх місяців
        if len(df['month'].unique()) > 1:
            all_months = pd.period_range(start=df['month'].min(), end=df['month'].max(), freq='M')
        else:
            all_months = [df['month'].min()]
        
        monthly_income = monthly_income.reindex(all_months, fill_value=0)
        monthly_expense = monthly_expense.reindex(all_months, fill_value=0)
        
        # Створення графіка
        fig, ax = plt.subplots(figsize=(12, 6))
        
        x = range(len(all_months))
        labels = [str(m) for m in all_months]
        
        ax.plot(x, monthly_income.values, marker='o', label='Доходи', linewidth=2, color='green', markersize=6)
        ax.plot(x, monthly_expense.values, marker='o', label='Витрати', linewidth=2, color='red', markersize=6)
        
        ax.set_xlabel('Місяць', fontsize=12)
        ax.set_ylabel('Сума (грн)', fontsize=12)
        ax.set_title('Динаміка доходів та витрат', fontsize=16, fontweight='bold')
        ax.legend(fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Зберегти в пам'ять
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        return buf
    except Exception as e:
        print(f"Помилка генерації графіка динаміки: {e}")
        return None


def get_period_dates(period: str):
    """Отримати дати початку та кінця періоду"""
    end_date = datetime.now()
    
    if period == 'today':
        start_date = end_date
        period_name = "Сьогодні"
    elif period == 'yesterday':
        start_date = end_date - timedelta(days=1)
        end_date = start_date
        period_name = "Вчора"
    elif period == 'week':
        start_date = end_date - timedelta(days=7)
        period_name = "Тиждень"
    elif period == 'month':
        start_date = end_date - timedelta(days=30)
        period_name = "Місяць"
    elif period == 'year':
        start_date = end_date - timedelta(days=365)
        period_name = "Рік"
    else:  # all
        start_date = datetime(2020, 1, 1)
        period_name = "Весь час"
    
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), period_name


async def export_to_excel(user_id: int):
    """Експорт даних в Excel"""
    try:
        transactions = await get_transactions(user_id)
        
        if not transactions or len(transactions) == 0:
            return None
        
        df = pd.DataFrame(transactions, columns=[
            'ID', 'User ID', 'Тип', 'Сума', 'Категорія', 'Опис', 'Дата', 'Створено'
        ])
        
        # Зберегти в пам'ять
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Транзакції')
        buf.seek(0)
        
        return buf
    except Exception as e:
        print(f"Помилка експорту в Excel: {e}")
        return None


async def export_to_csv(user_id: int):
    """Експорт даних в CSV"""
    try:
        transactions = await get_transactions(user_id)
        
        if not transactions or len(transactions) == 0:
            return None
        
        df = pd.DataFrame(transactions, columns=[
            'ID', 'User ID', 'Тип', 'Сума', 'Категорія', 'Опис', 'Дата', 'Створено'
        ])
        
        # Зберегти в пам'ять
        buf = io.BytesIO()
        csv_string = df.to_csv(index=False, encoding='utf-8-sig')
        buf.write(csv_string.encode('utf-8-sig'))
        buf.seek(0)
        
        return buf
    except Exception as e:
        print(f"Помилка експорту в CSV: {e}")
        return None
