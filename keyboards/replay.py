from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_menu_keyboard():
    """Главное меню"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="👤 Моя анкета"),
        KeyboardButton(text="🔍 Смотреть анкеты"),
        KeyboardButton(text="💌 Мои уведомления"),
        KeyboardButton(text="💝 Мои мэтчи"),
        KeyboardButton(text="🎁 Бесплатный премиум"),
        KeyboardButton(text="⭐ Премиум")
    )
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

def get_profile_menu_keyboard():
    """Меню для работы с анкетой"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="👀 Посмотреть анкету"),
        KeyboardButton(text="✏️ Редактировать анкету"),
        KeyboardButton(text="🗑️ Удалить анкету"),
        KeyboardButton(text="🔙 Назад в меню")
    )
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)

def get_edit_profile_keyboard():
    """Клавиатура для редактирования анкеты"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="✏️ Изменить имя"),
        KeyboardButton(text="✏️ Изменить возраст"),
        KeyboardButton(text="✏️ Изменить пол"),
        KeyboardButton(text="✏️ Изменить кого ищу"),
        KeyboardButton(text="✏️ Изменить город"),
        KeyboardButton(text="✏️ Изменить интересы"),
        KeyboardButton(text="✏️ Изменить описание"),
        KeyboardButton(text="📷 Изменить фото"),
        KeyboardButton(text="🔙 Назад к анкете"),
        KeyboardButton(text="🏠 Главное меню")
    )
    builder.adjust(2, 2, 2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

def get_profile_view_keyboard():
    """Клавиатура для просмотра анкет"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="❤️"),
        KeyboardButton(text="👎"),
        KeyboardButton(text="🎁"),
        KeyboardButton(text="🚫 Пожаловаться"),
        KeyboardButton(text="🏠 Главное меню")
    )
    builder.adjust(3, 2)
    return builder.as_markup(resize_keyboard=True)

def get_like_notification_keyboard():
    """Клавиатура для уведомления о лайке"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="❤️ Ответить лайком"),
        KeyboardButton(text="👎 Отказать"),
        KeyboardButton(text="⏭️ Пропустить"),
        KeyboardButton(text="🏠 Главное меню")
    )
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)

def get_match_keyboard():
    """Клавиатура при взаимной симпатии"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="👀 Посмотреть анкету"),
        KeyboardButton(text="💌 Написать"),
        KeyboardButton(text="🏠 Главное меню")
    )
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)

def get_premium_menu_keyboard():
    """Меню премиум подписки"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="⭐ Преимущества премиума"),
        KeyboardButton(text="💰 Тарифы и оплата"),
        KeyboardButton(text="🎁 Бесплатный премиум"),
        KeyboardButton(text="📊 Моя статистика"),
        KeyboardButton(text="🏠 Главное меню")
    )
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

def get_premium_tariffs_keyboard():
    """Клавиатура с тарифами премиума"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="⭐ 7 дней - 299 звезд"),
        KeyboardButton(text="⭐ 30 дней - 599 звезд"),
        KeyboardButton(text="⭐ 3 месяца - 799 звезд"),
        KeyboardButton(text="⭐ 1 год - 2590 звезд"),
        KeyboardButton(text="🔙 Назад в премиум меню"),
        KeyboardButton(text="🏠 Главное меню")
    )
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

def get_free_premium_keyboard():
    """Клавиатура для бесплатного премиума"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="📢 Пригласить друзей"),
        KeyboardButton(text="📊 Моя реферальная статистика"),
        KeyboardButton(text="🎁 Получить награду"),
        KeyboardButton(text="🔙 Назад в премиум меню"),
        KeyboardButton(text="🏠 Главное меню")
    )
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

def get_back_to_profile_keyboard():
    """Кнопка возврата к анкете"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="🔙 Назад к анкете"),
        KeyboardButton(text="🏠 Главное меню")
    )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_back_to_menu_keyboard():
    """Кнопка возврата в главное меню"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🏠 Главное меню"))
    return builder.as_markup(resize_keyboard=True)

def get_cancel_keyboard():
    """Клавиатура для отмены"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True)

def get_gender_keyboard():
    """Клавиатура для выбора пола"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="👨 Мужчина"),
        KeyboardButton(text="👩 Женщина"),
        KeyboardButton(text="🧑 Другой")
    )
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)

def get_looking_for_keyboard():
    """Клавиатура для выбора кого ищет пользователь"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="👨 Парня"),
        KeyboardButton(text="👩 Девушку"),
        KeyboardButton(text="👥 Оба")
    )
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)

def get_finish_registration_keyboard():
    """Клавиатура для завершения регистрации"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="✅ Завершить регистрацию"))
    return builder.as_markup(resize_keyboard=True)

def get_continue_viewing_keyboard():
    """Клавиатура для выбора после уведомления о лайках"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="💌 Мои уведомления"),
        KeyboardButton(text="🔍 Продолжить просмотр")
    )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_back_to_premium_keyboard():
    """Кнопка возврата в премиум меню"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="🔙 Назад в премиум меню"),
        KeyboardButton(text="🏠 Главное меню")
    )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_notification_decision_keyboard():
    """Клавиатура для принятия решения по уведомлению (3 кнопки)"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="❤️ Ответить лайком"),
        KeyboardButton(text="👎 Отказать"),
        KeyboardButton(text="🚫 Пожаловаться"),
        KeyboardButton(text="⏭️ Следующий"),
        KeyboardButton(text="🏠 Главное меню")
    )
    builder.adjust(3, 2)
    return builder.as_markup(resize_keyboard=True)