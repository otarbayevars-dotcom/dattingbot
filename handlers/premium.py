from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice, SuccessfulPayment, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import asyncio

from handlers.profile_creation import ProfileCreation
from models import Database
from keyboards.replay import *
from keyboards.inline_premium import *


router = Router()
db = Database()

class PremiumStates(StatesGroup):
    """Состояния для премиум системы"""
    choosing_tariff = State()
    referral_program = State()

@router.message(F.text == "⭐ Премиум")
async def show_premium_menu(message: Message, state: FSMContext):
    """Показать меню премиум подписки"""
    user_id = db.get_user_id_by_telegram_id(message.from_user.id)
    
    if not user_id:
        await message.answer("❌ <b>Сначала создайте анкету через /start!</b>", parse_mode="HTML")
        return
    
    # Проверяем статус премиум подписки
    premium_status = db.get_user_premium_status(user_id)
    
    if premium_status:
        # Пользователь уже имеет премиум
        expires_at = datetime.fromtimestamp(premium_status['expires_at'])
        days_left = max(0, (expires_at - datetime.now()).days)
        
        await message.answer(
            f"🎉 <b>У вас активна премиум подписка!</b>\n\n"
            f"✨ <b>Тип подписки:</b> {premium_status['plan_type']}\n"
            f"⏳ <b>Действует до:</b> {expires_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"📅 <b>Осталось дней:</b> {days_left}\n\n"
            f"🌟 Вы можете продлить подписку или узнать о других возможностях:",
            parse_mode="HTML",
            reply_markup=get_premium_menu_keyboard()
        )
    else:
        await message.answer(
            "⭐ <b>Премиум подписка</b>\n\n"
            "✨ Откройте все возможности бота для знакомств!\n\n"
            "🎯 <b>Выберите действие:</b>",
            parse_mode="HTML",
            reply_markup=get_premium_menu_keyboard()
        )

@router.message(F.text == "🎁 Бесплатный премиум")
async def show_free_premium(message: Message, state: FSMContext):
    """Показать информацию о бесплатном премиуме"""
    user_id = db.get_user_id_by_telegram_id(message.from_user.id)
    
    if not user_id:
        await message.answer("❌ <b>Сначала создайте анкету через /start!</b>", parse_mode="HTML")
        return
    
    print(f"DEBUG: Показ бесплатного премиума для user_id={user_id}")
    
    # Получаем или создаем реферальный код
    referral_info = db.get_referral_code(user_id)
    
    if not referral_info:
        print(f"DEBUG: Создаем новый реферальный код для user_id={user_id}")
        # Создаем реферальный код, если его нет
        referral_code = db.create_referral_code(user_id)
        referral_info = db.get_referral_code(user_id)
    else:
        print(f"DEBUG: Используем существующий код: {referral_info['code']}")
    
    # Получаем статистику по рефералам
    referral_stats = db.get_referral_stats(user_id)
    print(f"DEBUG: Статистика рефералов: total={referral_stats['total']}, completed={referral_stats['completed']}")
    
    # Создаем реферальную ссылку
    try:
        bot_info = await message.bot.get_me()
        bot_username = bot_info.username
        referral_link = f"https://t.me/{bot_username}?start={referral_info['code']}"
        print(f"DEBUG: Создана реферальная ссылка: {referral_link}")
    except Exception as e:
        print(f"❌ Ошибка получения информации о боте: {e}")
        referral_link = f"Используйте код: {referral_info['code']}"
    
    progress_bar = "▓" * referral_stats['completed'] + "░" * (10 - referral_stats['completed'])
    
    await message.answer(
        f"🎁 <b>Бесплатный премиум</b>\n\n"
        f"✨ Получите премиум подписку на 1 день <b>БЕСПЛАТНО!</b>\n\n"
        f"🎯 <b>Как получить:</b>\n"
        f"1. 📢 Пригласите 10 друзей по вашей реферальной ссылке\n"
        f"2. ✅ Каждый друг должен создать анкету в боте\n"
        f"3. 🎉 Когда 10 друзей создадут анкеты - получайте премиум!\n\n"
        f"📊 <b>Ваша статистика:</b>\n"
        f"👥 <b>Приглашено друзей:</b> {referral_stats['total']}\n"
        f"✅ <b>Создали анкеты:</b> {referral_stats['completed']}/10\n"
        f"📈 <b>Прогресс:</b> {progress_bar}\n"
        f"🔢 <b>Процент:</b> {referral_stats['completed'] * 10}%\n\n"
        f"🔗 <b>Ваша реферальная ссылка:</b>\n"
        f"<code>{referral_link}</code>\n\n"
        f"🔑 <b>Или используйте код:</b>\n"
        f"<code>{referral_info['code']}</code>",
        parse_mode="HTML",
        reply_markup=get_free_premium_keyboard()
    )
    
    # Сохраняем реферальную ссылку
    await state.update_data(referral_link=referral_link)

@router.message(F.text == "⭐ Преимущества премиума")
async def show_premium_benefits(message: Message):
    """Показать преимущества премиум подписки"""
    benefits = (
        "✨ <b>Преимущества премиум подписки:</b>\n\n"
        
        "🚀 <b>Повышенная видимость:</b>\n"
        "• 🌟 Ваша анкета показывается в 3 раза чаще\n"
        "• ⬆️ Поднимается в топе поиска каждый день\n"
        "• 🏆 Специальный бейдж премиум пользователя\n\n"
        
        "🔍 <b>Расширенный поиск:</b>\n"
        "• 🔎 Расширенные фильтры поиска\n"
        "• 🎯 Поиск по интересам с точным совпадением\n"
        "• 👀 Видеть, кто просматривал вашу анкету\n\n"
        
        "💌 <b>Особые возможности общения:</b>\n"
        "• 🎁 Отправлять неограниченное количество подарков\n"
        "• 💖 Отправлять суперлайки (уведомление сразу на экране)\n"
        "• 👁️ Видеть, кому вы понравились, первыми\n\n"
        
        "🎯 <b>Дополнительные функции:</b>\n"
        "• 🕶️ Режим невидимки (просматривайте анкеты незаметно)\n"
        "• 📊 Расширенная статистика профиля\n"
        "• ⭐ Приоритетная поддержка\n\n"
        
        "🌟 <b>И многое другое!</b>"
    )
    
    await message.answer(
        benefits,
        parse_mode="HTML",
        reply_markup=get_back_to_premium_keyboard()
    )

@router.message(F.text == "💰 Тарифы и оплата")
async def show_premium_tariffs(message: Message, state: FSMContext):
    """Показать тарифы премиум подписки"""
    user_id = db.get_user_id_by_telegram_id(message.from_user.id)
    
    if not user_id:
        await message.answer("❌ <b>Сначала создайте анкету через /start!</b>", parse_mode="HTML")
        return
    
    tariffs_info = (
        "💰 <b>Тарифы премиум подписки</b>\n\n"
        
        "⭐ <b>7 дней</b> - 299 Telegram Stars\n"
        "➤ <i>Идеально для теста</i>\n"
        "➤ <i>2,14 звезд в день</i>\n\n"
        
        "⭐ <b>30 дней</b> - 599 Telegram Stars\n"
        "➤ <i>Самый популярный тариф</i>\n"
        "➤ <i>Экономия 17%</i>\n"
        "➤ <i>1,99 звезд в день</i>\n\n"
        
        "⭐ <b>3 месяца</b> - 799 Telegram Stars\n"
        "➤ <i>Выгодно для активных</i>\n"
        "➤ <i>Экономия 33%</i>\n"
        "➤ <i>0,88 звезд в день</i>\n\n"
        
        "⭐ <b>1 год</b> - 2590 Telegram Stars\n"
        "➤ <i>Максимальная выгода</i>\n"
        "➤ <i>Экономия 55%</i>\n"
        "➤ <i>+ Бонус: 10 суперлайков</i>\n"
        "➤ <i>0,71 звезд в день</i>\n\n"
        
        "💎 <b>Telegram Stars 2.0</b>\n"
        "🌟 Оплата происходит через Telegram Stars.\n"
        "⭐ Звезды можно получить за переводы в Telegram\n"
        "🎫 или купить в разделе 'Звезды' в настройках.\n\n"
        
        "🎯 <b>Выберите подходящий тариф:</b>"
    )
    
    await message.answer(
        tariffs_info,
        parse_mode="HTML",
        reply_markup=get_premium_tariffs_keyboard()
    )
    
    await state.set_state(PremiumStates.choosing_tariff)

@router.message(PremiumStates.choosing_tariff, F.text.startswith("⭐ "))
async def process_tariff_selection(message: Message, state: FSMContext):
    """Обработка выбора тарифа"""
    user_id = db.get_user_id_by_telegram_id(message.from_user.id)
    
    if not user_id:
        await message.answer("❌ <b>Сначала создайте анкету через /start!</b>", parse_mode="HTML")
        await state.clear()
        return
    
    tariff_text = message.text
    
    # Определяем выбранный тариф
    if "7 дней" in tariff_text:
        stars_amount = 299
        duration_days = 7
        tariff_name = "7 дней"
        daily_cost = stars_amount / duration_days
    elif "30 дней" in tariff_text:
        stars_amount = 599
        duration_days = 30
        tariff_name = "30 дней"
        daily_cost = stars_amount / duration_days
    elif "3 месяца" in tariff_text:
        stars_amount = 799
        duration_days = 90
        tariff_name = "3 месяца"
        daily_cost = stars_amount / duration_days
    elif "1 год" in tariff_text:
        stars_amount = 2590
        duration_days = 365
        tariff_name = "1 год"
        daily_cost = stars_amount / duration_days
    else:
        await message.answer("❌ <b>Пожалуйста, выберите тариф из предложенных.</b>", parse_mode="HTML")
        return
    
    # Создаем запись о платеже
    payment_id, payload = db.create_star_payment(
        user_id, stars_amount, 'premium', duration_days
    )
    
    if not payment_id:
        await message.answer("❌ <b>Произошла ошибка при создании платежа. Попробуйте еще раз.</b>", parse_mode="HTML")
        return
    
    await message.answer(
        f"🛒 <b>Оформление подписки</b>\n\n"
        f"✅ <b>Вы выбрали:</b> {tariff_name}\n"
        f"💰 <b>Стоимость:</b> {stars_amount} Telegram Stars\n"
        f"📅 <b>Длительность:</b> {duration_days} дней\n"
        f"📊 <b>Стоимость в день:</b> {daily_cost:.2f} звезд\n\n"
        f"🔧 <b>Техническая информация:</b>\n"
        f"🆔 <b>ID платежа:</b> {payment_id}\n"
        f"🔑 <b>Payload:</b> {payload}\n\n"
        f"⚠️ <b>Внимание:</b>\n"
        f"Для тестирования оплата через Telegram Stars отключена.\n"
        f"В production версии здесь будет автоматическая оплата.",
        parse_mode="HTML",
        reply_markup=get_back_to_premium_keyboard()
    )
    
    # Сохраняем данные о выбранном тарифе
    await state.update_data(
        selected_tariff=tariff_name,
        stars_amount=stars_amount,
        duration_days=duration_days,
        payment_id=payment_id
    )

@router.message(F.text == "📢 Пригласить друзей")
async def invite_friends(message: Message, state: FSMContext):
    """Пригласить друзей по реферальной ссылке"""
    user_id = db.get_user_id_by_telegram_id(message.from_user.id)
    
    if not user_id:
        await message.answer("❌ <b>Сначала создайте анкету через /start!</b>", parse_mode="HTML")
        return
    
    # Получаем реферальный код
    referral_info = db.get_referral_code(user_id)
    
    if not referral_info:
        referral_code = db.create_referral_code(user_id)
        referral_info = db.get_referral_code(user_id)
    
    # Создаем реферальную ссылку
    bot_username = (await message.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start={referral_info['code']}"
    
    # Получаем статистику
    referral_stats = db.get_referral_stats(user_id)
    
    progress_bar = "▓" * referral_stats['completed'] + "░" * (10 - referral_stats['completed'])
    
    invite_message = (
        f"📢 <b>Пригласите друзей и получите премиум БЕСПЛАТНО!</b>\n\n"
        
        f"🔗 <b>Ваша реферальная ссылка:</b>\n"
        f"<code>{referral_link}</code>\n\n"
        
        f"🔑 <b>Или используйте код:</b>\n"
        f"<code>{referral_info['code']}</code>\n\n"
        
        f"📊 <b>Статистика:</b>\n"
        f"👥 <b>Приглашено:</b> {referral_stats['total']}\n"
        f"✅ <b>Создали анкеты:</b> {referral_stats['completed']}/10\n"
        f"🎯 <b>Осталось:</b> {10 - referral_stats['completed']}\n"
        f"📈 <b>Прогресс:</b> {progress_bar}\n\n"
        
        f"📣 <b>Как делиться ссылкой:</b>\n"
        f"1. 📲 Нажмите 'Поделиться ссылкой'\n"
        f"2. 👥 Выберите друзей или группы\n"
        f"3. ✍️ Добавьте сообщение о боте\n\n"
        
        f"💡 <b>Пример сообщения:</b>\n"
        f"Привет! Я нашел(а) крутого бота для знакомств 😊\n"
        f"Регистрируйся по моей ссылке:\n"
        f"{referral_link}"
    )
    
    await message.answer(
        invite_message,
        parse_mode="HTML",
        reply_markup=get_referral_invite_keyboard(referral_link)
    )

@router.message(F.text == "📊 Моя реферальная статистика")
async def show_referral_stats(message: Message):
    """Показать реферальную статистику"""
    user_id = db.get_user_id_by_telegram_id(message.from_user.id)
    
    if not user_id:
        await message.answer("❌ <b>Сначала создайте анкету через /start!</b>", parse_mode="HTML")
        return
    
    referral_stats = db.get_referral_stats(user_id)
    referral_info = db.get_referral_code(user_id)
    
    if not referral_info:
        referral_info = {'code': 'Нет кода', 'uses': 0, 'max_uses': 10}
    
    progress_bar = "▓" * referral_stats['completed'] + "░" * (10 - referral_stats['completed'])
    
    stats_message = (
        f"📊 <b>Ваша реферальная статистика</b>\n\n"
        
        f"🔑 <b>Ваш реферальный код:</b>\n"
        f"<code>{referral_info['code']}</code>\n\n"
        
        f"📈 <b>Статистика приглашений:</b>\n"
        f"👥 <b>Всего приглашено:</b> {referral_stats['total']}\n"
        f"✅ <b>Создали анкеты:</b> {referral_stats['completed']}\n"
        f"⏳ <b>В процессе:</b> {referral_stats['total'] - referral_stats['completed']}\n\n"
        
        f"🎯 <b>Прогресс к бесплатному премиуму:</b>\n"
        f"📋 <b>Необходимо:</b> 10 друзей с анкетами\n"
        f"✅ <b>У вас есть:</b> {referral_stats['completed']}/10\n"
        f"📊 <b>Прогресс:</b> {progress_bar}\n"
        f"🔢 <b>Процент:</b> {referral_stats['completed'] * 10}%\n\n"
        
        f"🏆 <b>Награда:</b>\n"
        f"🎁 За 10 приглашенных: Премиум на 1 день\n\n"
        
        f"💡 <b>Совет:</b>\n"
        f"📱 Делитесь ссылкой в социальных сетях и чатах!\n"
    )
    
    if referral_stats['completed'] >= 10:
        stats_message += "\n🎉 <b>Вы можете получить награду!</b> Нажмите '🎁 Получить награду'"
    
    await message.answer(
        stats_message,
        parse_mode="HTML",
        reply_markup=get_free_premium_keyboard()
    )

@router.message(F.text == "🎁 Получить награду")
async def claim_referral_reward(message: Message):
    """Получить награду за рефералов"""
    user_id = db.get_user_id_by_telegram_id(message.from_user.id)
    
    if not user_id:
        await message.answer("❌ <b>Сначала создайте анкету через /start!</b>", parse_mode="HTML")
        return
    
    # Пытаемся получить награду
    success = db.claim_referral_reward(user_id)
    
    if success:
        await message.answer(
            "🎉 <b>Поздравляем!</b>\n\n"
            "✅ <b>Вы успешно получили премиум подписку на 1 день!</b>\n\n"
            "✨ Ваши новые возможности уже активны.\n"
            "🌟 Наслаждайтесь всеми преимуществами премиума!\n\n"
            "⏳ <b>Подписка действительна:</b> 24 часа",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        referral_stats = db.get_referral_stats(user_id)
        
        progress_bar = "▓" * referral_stats['completed'] + "░" * (10 - referral_stats['completed'])
        
        await message.answer(
            f"❌ <b>Недостаточно приглашенных друзей</b>\n\n"
            f"🎯 <b>Для получения награды необходимо:</b>\n"
            f"✅ 10 друзей создали анкеты\n\n"
            f"📊 <b>Ваша статистика:</b>\n"
            f"👥 <b>Приглашено:</b> {referral_stats['total']}\n"
            f"✅ <b>Создали анкеты:</b> {referral_stats['completed']}/10\n"
            f"🎯 <b>Осталось:</b> {10 - referral_stats['completed']}\n"
            f"📈 <b>Прогресс:</b> {progress_bar}\n\n"
            f"💪 <b>Продолжайте приглашать друзей!</b>",
            parse_mode="HTML",
            reply_markup=get_free_premium_keyboard()
        )

@router.message(F.text == "📊 Моя статистика")
async def show_user_stats(message: Message):
    """Показать общую статистику пользователя"""
    user_id = db.get_user_id_by_telegram_id(message.from_user.id)
    
    if not user_id:
        await message.answer("❌ <b>Сначала создайте анкету через /start!</b>", parse_mode="HTML")
        return
    
    # Получаем различные статистики
    referral_stats = db.get_referral_stats(user_id)
    premium_status = db.get_user_premium_status(user_id)
    
    # Получаем дату регистрации
    db.cursor.execute('''
        SELECT created_at FROM users WHERE id = ?
    ''', (user_id,))
    
    user_data = db.cursor.fetchone()
    
    if user_data:
        reg_date = datetime.fromtimestamp(user_data['created_at']).strftime('%d.%m.%Y')
    else:
        reg_date = "Неизвестно"
    
    stats_message = (
        "📊 <b>Ваша статистика</b>\n\n"
        
        "👤 <b>Общая информация:</b>\n"
        f"🆔 <b>ID пользователя:</b> {user_id}\n"
        f"📅 <b>Дата регистрации:</b> {reg_date}\n\n"
        
        "👥 <b>Реферальная программа:</b>\n"
        f"📢 <b>Приглашено друзей:</b> {referral_stats['total']}\n"
        f"✅ <b>Создали анкеты:</b> {referral_stats['completed']}\n"
        f"🎯 <b>До награды:</b> {max(0, 10 - referral_stats['completed'])}\n\n"
    )
    
    if premium_status:
        expires_at = datetime.fromtimestamp(premium_status['expires_at'])
        days_left = max(0, (expires_at - datetime.now()).days)
        
        stats_message += (
            "⭐ <b>Премиум статус:</b>\n"
            f"✅ <b>Активен:</b> Да\n"
            f"📋 <b>Тип:</b> {premium_status['plan_type']}\n"
            f"📅 <b>Осталось дней:</b> {days_left}\n"
            f"⏳ <b>Истекает:</b> {expires_at.strftime('%d.%m.%Y')}\n\n"
        )
    else:
        stats_message += (
            "⭐ <b>Премиум статус:</b>\n"
            "❌ <b>Активен:</b> Нет\n\n"
        )
    
    # Добавляем мотивацию
    if referral_stats['completed'] < 5:
        stats_message += (
            "💡 <b>Совет:</b>\n"
            "📢 Пригласите еще друзей, чтобы получить бесплатный премиум!\n"
            "🌟 Это откроет вам все возможности бота."
        )
    elif referral_stats['completed'] < 10:
        stats_message += (
            "🎯 <b>Вы близки к цели!</b>\n"
            f"✅ Осталось всего {10 - referral_stats['completed']} друзей!\n"
            "💪 Продолжайте в том же духе!"
        )
    else:
        stats_message += (
            "🏆 <b>Поздравляем!</b>\n"
            "🎉 Вы уже получили бесплатный премиум!\n"
            "📢 Можете приглашать больше друзей для продления."
        )
    
    await message.answer(
        stats_message,
        parse_mode="HTML",
        reply_markup=get_premium_menu_keyboard()
    )

@router.message(F.text == "🔙 Назад в премиум меню")
async def back_to_premium_menu(message: Message, state: FSMContext):
    """Вернуться в меню премиума"""
    await show_premium_menu(message, state)

@router.message(F.text == "🏠 Главное меню")
async def back_to_main_menu(message: Message, state: FSMContext):
    """Вернуться в главное меню"""
    await state.clear()
    await message.answer(
        "↩️ <b>Возвращаюсь в главное меню:</b>",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )

# Обработка реферальных ссылок при старте
@router.message(Command("start"))
async def start_with_referral(message: Message, state: FSMContext):
    """Обработчик команды /start с реферальными ссылками"""
    # Извлекаем реферальный код из сообщения
    referral_code = None
    if len(message.text.split()) > 1:
        args = message.text.split()[1]
        referral_code = args.strip()
    
    # Проверяем, является ли код валидным реферальным кодом
    if referral_code and len(referral_code) == 8 and referral_code.isalnum():
        print(f"DEBUG: Обнаружен реферальный код: {referral_code}")
        
        # Находим пользователя по реферальному коду
        db.cursor.execute('''
            SELECT user_id FROM referral_codes WHERE code = ?
        ''', (referral_code,))
        
        result = db.cursor.fetchone()
        
        if result:
            referrer_id = result['user_id']
            referred_telegram_id = message.from_user.id
            
            print(f"DEBUG: Найден реферер ID: {referrer_id} для кода: {referral_code}")
            
            # Проверяем, не приглашает ли пользователь сам себя
            referrer_telegram_id = db.get_telegram_id_by_user_id(referrer_id)
            if referrer_telegram_id == referred_telegram_id:
                print(f"DEBUG: Пользователь пытается использовать свою же ссылку")
                referral_code = None
            else:
                print(f"DEBUG: Валидная реферальная ссылка, реферер: {referrer_id}")
        else:
            print(f"DEBUG: Реферальный код не найден: {referral_code}")
            referral_code = None
    else:
        print(f"DEBUG: Невалидный или отсутствующий реферальный код")
        referral_code = None
    
    # Создаем пользователя если его нет
    user_id = db.add_user(message.from_user.id, message.from_user.username)
    print(f"DEBUG: Создан/найден пользователь с ID: {user_id}")
    
    # Проверяем, есть ли уже анкета
    profile = db.get_user_profile(message.from_user.id)
    
    if profile:
        # Если анкета есть, показываем главное меню
        await message.answer(
            "👋 <b>С возвращением!</b>\n\n"
            "🎯 <b>Выберите действие:</b>",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        # Если анкеты нет, начинаем создание
        await message.answer(
            "👋 <b>Привет! Добро пожаловать в бот для знакомств!</b>\n\n"
            "✨ <b>Давай создадим твою анкету.</b>\n\n"
            "📝 <b>Как тебя зовут?</b>",
            parse_mode="HTML"
        )
        await state.set_state(ProfileCreation.name)
    
    # Обрабатываем реферальный код ПОСЛЕ регистрации
    if referral_code and len(referral_code) == 8 and referral_code.isalnum():
        print(f"DEBUG: Обработка реферального кода: {referral_code}")
        await process_referral_code(message, referral_code)

async def process_referral_code(message: Message, referral_code: str):
    """Обработка реферального кода"""
    try:
        print(f"DEBUG: Начало обработки реферального кода: {referral_code}")
        
        # Находим пользователя по реферальному коду
        db.cursor.execute('''
            SELECT user_id FROM referral_codes WHERE code = ?
        ''', (referral_code,))
        
        result = db.cursor.fetchone()
        
        if not result:
            print(f"DEBUG: Реферальный код не найден в БД")
            return
        
        referrer_id = result['user_id']
        print(f"DEBUG: Найден реферер ID: {referrer_id}")
        
        # Получаем ID приглашенного пользователя
        referred_user_id = db.get_user_id_by_telegram_id(message.from_user.id)
        print(f"DEBUG: Приглашенный пользователь ID: {referred_user_id}")
        
        if not referred_user_id:
            print(f"DEBUG: Приглашенный пользователь не найден")
            return
        
        # Проверяем, не приглашает ли пользователь сам себя
        if referrer_id == referred_user_id:
            print(f"DEBUG: Пользователь пытается пригласить сам себя")
            await message.answer(
                "❌ <b>Нельзя использовать свою же реферальную ссылку!</b>",
                parse_mode="HTML"
            )
            return
        
        # Проверяем, не был ли уже добавлен этот реферал
        db.cursor.execute('''
            SELECT id FROM referrals WHERE referrer_id = ? AND referred_id = ?
        ''', (referrer_id, referred_user_id))
        
        existing_referral = db.cursor.fetchone()
        
        if existing_referral:
            print(f"DEBUG: Реферал уже существует")
            await message.answer(
                "ℹ️ <b>Вы уже зарегистрировались по этой реферальной ссылке ранее.</b>",
                parse_mode="HTML"
            )
            return
        
        print(f"DEBUG: Добавление реферала: {referrer_id} -> {referred_user_id}")
        # Добавляем реферала
        success = db.add_referral(referrer_id, referred_user_id)
        
        if success:
            print(f"DEBUG: Реферал успешно добавлен")
            
            # Отправляем уведомление пригласившему
            referrer_telegram_id = db.get_telegram_id_by_user_id(referrer_id)
            
            if referrer_telegram_id:
                try:
                    referral_stats = db.get_referral_stats(referrer_id)
                    
                    await message.bot.send_message(
                        chat_id=referrer_telegram_id,
                        text=f"🎉 <b>По вашей ссылке зарегистрировался новый пользователь!</b>\n\n"
                             f"👤 Пользователь: @{message.from_user.username or 'без username'}\n"
                             f"📊 Теперь у вас {referral_stats['completed']}/10 приглашенных.\n"
                             f"🎯 До награды: {max(0, 10 - referral_stats['completed'])}",
                        parse_mode="HTML"
                    )
                    print(f"DEBUG: Уведомление отправлено рефереру {referrer_telegram_id}")
                except Exception as e:
                    print(f"❌ Ошибка отправки уведомления рефереру: {e}")
            
            # Отправляем уведомление приглашенному
            await message.answer(
                f"🎉 <b>Вы зарегистрировались по реферальной ссылке!</b>\n\n"
                f"🌟 Теперь ваш друг получит +1 к счетчику приглашенных.\n"
                f"📊 Когда он пригласит 10 друзей, получит премиум подписку!\n\n"
                f"💡 <b>Совет:</b> Создайте свою реферальную ссылку в разделе '🎁 Бесплатный премиум'",
                parse_mode="HTML"
            )
            
        else:
            print(f"DEBUG: Ошибка при добавлении реферала")
            
    except Exception as e:
        print(f"❌ Ошибка обработки реферального кода: {e}")

# Callback-обработчики для inline кнопок
@router.callback_query(F.data == "how_to_get_stars")
async def how_to_get_stars(callback: CallbackQuery):
    """Информация о получении Telegram Stars"""
    stars_info = (
        "💎 <b>Как получить Telegram Stars:</b>\n\n"
        
        "1. <b>Пополнение через Telegram:</b>\n"
        "• 📱 Откройте настройки Telegram\n"
        "• ⭐ Перейдите в раздел 'Звезды' (Stars)\n"
        "• 💳 Выберите способ пополнения\n"
        "• 🛒 Купите необходимое количество звезд\n\n"
        
        "2. <b>Получение звезд за переводы:</b>\n"
        "• 💰 Когда вам переводят деньги в Telegram\n"
        "• ⭐ Вы получаете звезды в качестве кэшбека\n"
        "• 🔢 1 рубль ≈ 1 звезда (зависит от региона)\n\n"
        
        "3. <b>Бонусы и акции:</b>\n"
        "• 🎁 Следите за акциями в Telegram\n"
        "• 🤝 Участвуйте в партнерских программах\n"
        "• 🎫 Получайте бонусные звезды\n\n"
        
        "💰 <b>Использование звезд:</b>\n"
        "• 🤖 Оплата цифровых товаров в ботах\n"
        "• ⭐ Покупка премиум подписок\n"
        "• 🔒 Доступ к эксклюзивному контенту\n\n"
        
        "⚡ <b>Быстрый доступ:</b>\n"
        "Нажмите на кнопку ниже, чтобы открыть раздел 'Звезды':"
    )
    
    # Создаем inline клавиатуру с кнопкой для открытия звезд
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="⭐ Открыть Telegram Stars",
            url="tg://settings/stars"
        ),
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="premium_back"
        )
    )
    
    await callback.message.edit_text(
        stars_info,
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("copy_link_"))
async def copy_referral_link(callback: CallbackQuery):
    """Копирование реферальной ссылки"""
    referral_link = callback.data.replace("copy_link_", "")
    
    await callback.answer(
        f"📋 Ссылка скопирована в буфер обмена!\n\n"
        f"🔗 {referral_link}\n\n"
        f"Теперь вы можете вставить её в любое место.",
        show_alert=True
    )

@router.callback_query(F.data == "premium_back")
async def premium_back(callback: CallbackQuery):
    """Возврат в меню премиума"""
    await callback.message.edit_text(
        "⭐ <b>Премиум подписка</b>\n\n"
        "✨ Откройте все возможности бота для знакомств!\n\n"
        "🎯 <b>Выберите действие:</b>",
        parse_mode="HTML",
        reply_markup=get_premium_menu_keyboard()
    )
    await callback.answer()

# Обработчики успешных платежей
@router.pre_checkout_query()
async def pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    """Обработка предварительного запроса на оплату"""
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def successful_payment(message: Message):
    """Обработка успешного платежа"""
    payment = message.successful_payment
    user_id = db.get_user_id_by_telegram_id(message.from_user.id)
    
    if not user_id:
        return
    
    # Обрабатываем платеж
    if payment.invoice_payload.startswith("payment_"):
        try:
            payment_id = int(payment.invoice_payload.split("_")[1])
            
            success = db.complete_star_payment(
                payment_id,
                payment.telegram_payment_charge_id,
                payment.provider_payment_charge_id
            )
            
            if success:
                await message.answer(
                    "✅ <b>Платеж успешно завершен!</b>\n\n"
                    "🎉 Ваша премиум подписка активирована.\n"
                    "🌟 Наслаждайтесь всеми преимуществами!",
                    parse_mode="HTML",
                    reply_markup=get_main_menu_keyboard()
                )
        except Exception as e:
            print(f"❌ Ошибка обработки платежа: {e}")
            await message.answer(
                "⚠️ <b>Произошла ошибка при обработке платежа.</b>\n"
                "Пожалуйста, свяжитесь с поддержкой.",
                parse_mode="HTML"
            )

@router.message(Command("referral"))
async def referral_command(message: Message):
    """Команда для работы с реферальной системой"""
    await show_free_premium(message, None)

@router.callback_query(F.data == "how_to_write_message")
async def how_to_write_message(callback: CallbackQuery):
    """Инструкция как написать сообщение"""
    instructions = (
        "💡 <b>Как написать сообщение человеку:</b>\n\n"
        
        "1. <b>Способ 1:</b>\n"
        "• Перейдите в профиль бота\n"
        "• Нажмите на список участников\n"
        "• Найдите имя человека в списке\n"
        "• Напишите ему сообщение\n\n"
        
        "2. <b>Способ 2:</b>\n"
        "• Попросите человека указать username в анкете\n"
        "• Тогда можно будет написать через @username\n\n"
        
        "3. <b>Способ 3:</b>\n"
        "• Поделитесь ссылкой на свой профиль\n"
        "• Человек сможет написать вам первым\n\n"
        
        "🔒 <b>Почему так происходит:</b>\n"
        "• У пользователя включены настройки приватности\n"
        "• Он запретил получать сообщения по ссылке\n"
        "• Это защита от спама в Telegram\n\n"
        
        "💬 <b>Рекомендация:</b>\n"
        "Попросите человека добавить username в анкету!"
    )
    
    await callback.message.answer(
        instructions,
        parse_mode="HTML"
    )
    await callback.answer()
