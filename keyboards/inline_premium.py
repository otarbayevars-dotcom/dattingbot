from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

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
        # Если нет username, пытаемся использовать user_id, но добавляем текст
        builder.add(
            InlineKeyboardButton(
                text="💌 Написать сообщение",
                url=f"tg://user?id={telegram_id}"
            )
        )
    
    return builder.as_markup()


def get_write_message_fallback_keyboard():
    """Клавиатура на случай, если нельзя отправить ссылку"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="ℹ️ Как написать сообщение?",
            callback_data="how_to_write_message"
        )
    )
    return builder.as_markup()

def get_buy_premium_keyboard(tariff: str, stars_amount: int):
    """Inline-клавиатура для покупки премиума"""
    builder = InlineKeyboardBuilder()
    
    # Создаем payload для инвойса
    payload = f"premium_{tariff}_{stars_amount}"
    
    builder.add(
        InlineKeyboardButton(
            text=f"⭐ Купить за {stars_amount} звезд",
            pay=True
        )
    )
    
    builder.add(
        InlineKeyboardButton(
            text="ℹ️ Как получить звезды?",
            callback_data="how_to_get_stars"
        )
    )
    
    builder.adjust(1)
    return builder.as_markup()

def get_referral_invite_keyboard(referral_link: str):
    """Inline-клавиатура для приглашения друзей"""
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(
            text="📢 Поделиться ссылкой",
            url=f"https://t.me/share/url?url={referral_link}"
        )
    )
    
    builder.add(
        InlineKeyboardButton(
            text="📋 Копировать ссылку",
            callback_data=f"copy_link_{referral_link}"
        )
    )
    
    builder.add(
        InlineKeyboardButton(
            text="📊 Статистика",
            callback_data="referral_stats"
        )
    )
    
    builder.adjust(1)
    return builder.as_markup()

def get_premium_features_keyboard():
    """Inline-клавиатура с преимуществами премиума"""
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(
            text="💰 Посмотреть тарифы",
            callback_data="premium_tariffs"
        ),
        InlineKeyboardButton(
            text="🎁 Бесплатный премиум",
            callback_data="free_premium"
        )
    )
    
    builder.adjust(1)
    return builder.as_markup()