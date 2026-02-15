"""Утилітарні функції для валідації та обробки даних"""


def validate_amount(text: str) -> tuple[bool, float]:
    """Валідація суми"""
    try:
        amount = float(text.replace(',', '.').replace(' ', ''))
        if amount <= 0:
            return False, 0
        if amount > 1000000000:  # Максимальна сума 1 млрд
            return False, 0
        return True, amount
    except (ValueError, TypeError):
        return False, 0


def get_safe_description(text: str, max_length: int = 200) -> str:
    """Безпечний опис (обмеження довжини)"""
    if not text or text == '-':
        return None
    text = text.strip()
    if len(text) > max_length:
        return text[:max_length] + '...'
    return text


def escape_html(text: str) -> str:
    """Екранування HTML символів"""
    if not text:
        return ""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))

