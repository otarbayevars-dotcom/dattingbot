from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_interests_keyboard(selected_interests: list = None):
    """Inline-клавиатура для выбора интересов"""
    if selected_interests is None:
        selected_interests = []
    
    interests = [
        "Интим", "Отношения", "Дружба", "Игры",
        "Без обязательств", "Прогулки", "Кино", "Спорт",
        "Путешествия", "Музыка", "Искусство", "Кулинария"
    ]
    
    builder = InlineKeyboardBuilder()
    
    for interest in interests:
        # Добавляем галочку, если интерес уже выбран
        emoji = "✅" if interest in selected_interests else "○"
        builder.add(
            InlineKeyboardButton(
                text=f"{emoji} {interest}",
                callback_data=f"interest_{interest}"
            )
        )
    
    builder.add(
        InlineKeyboardButton(
            text="✅ Готово",
            callback_data="interests_done"
        )
    )
    
    builder.adjust(2)  # 2 кнопки в ряд
    return builder.as_markup()

def get_write_message_keyboard(telegram_id: int, username: str = None):
    """Inline-кнопка для написания сообщения с проверкой приватности"""
    builder = InlineKeyboardBuilder()
    
    if username:
        # Если есть username, используем его
        builder.add(
            InlineKeyboardButton(
                text="💌 Написать сообщение",
                url=f"https://t.me/{username}"
            )
        )
    else:
        # Если нет username, пытаемся использовать user_id
        builder.add(
            InlineKeyboardButton(
                text="💌 Написать сообщение",
                url=f"tg://user?id={telegram_id}"
            )
        )
    
    return builder.as_markup()
