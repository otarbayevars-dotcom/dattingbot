from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Optional
import asyncio
from datetime import datetime

from models import Database
from keyboards.replay import *
from keyboards.inline_premium import get_write_message_keyboard
from keyboards.inline import InlineKeyboardBuilder
from handlers.admin import send_like_notification, handle_mutual_match

router = Router()
db = Database()

class ViewingStates(StatesGroup):
    """Состояния для просмотра анкет"""
    viewing_profile = State()
    pending_like_response = State()
    report_reason = State()

class ReportStates(StatesGroup):
    """Состояния для жалобы"""
    waiting_for_reason = State()
    confirm_report = State()


def get_report_reasons_keyboard():
    """Клавиатура с причинами жалобы"""
    builder = InlineKeyboardBuilder()
    
    reasons = [
        ("🤥 Фейковый профиль", "report_fake"),
        ("🚫 Не отвечает", "report_no_response"),
        ("🔞 18+ контент", "report_adult"),
        ("📢 Реклама/спам", "report_spam"),
        ("😡 Оскорбления", "report_abuse"),
        ("❌ Другая причина", "report_other"),
        ("🔙 Отмена", "report_cancel")
    ]
    
    for text, callback_data in reasons:
        builder.add(InlineKeyboardButton(text=text, callback_data=callback_data))
    
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()

def get_admin_report_keyboard(report_id: int, profile_id: int):
    """Клавиатура для админа при обработке жалобы"""
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(text="🗑️ Удалить анкету", callback_data=f"admin_delete_{profile_id}_{report_id}"),
        InlineKeyboardButton(text="✉️ Написать пользователю", callback_data=f"admin_message_{profile_id}"),
        InlineKeyboardButton(text="✅ Закрыть жалобу", callback_data=f"admin_close_{report_id}"),
        InlineKeyboardButton(text="👁️ Просмотреть анкету", callback_data=f"admin_view_{profile_id}")
    )
    
    builder.adjust(2, 2)
    return builder.as_markup()

async def send_profile_with_photos(message: Message, profile: dict, caption: str, keyboard=None):
    """Отправка анкеты с фото (одно или несколько)"""
    if not profile['photos']:
        await message.answer(
            caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return
    
    if len(profile['photos']) > 1:
        media = [
            InputMediaPhoto(
                media=profile['photos'][0],
                caption=caption,
                parse_mode="HTML"
            )
        ]
        
        for photo in profile['photos'][1:]:
            media.append(InputMediaPhoto(media=photo))
        
        await message.answer_media_group(media=media)
        if keyboard:
            await message.answer(
                "🎯 <b>Что думаете об этой анкете?</b>", 
                parse_mode="HTML",
                reply_markup=keyboard
            )
    else:
        await message.answer_photo(
            photo=profile['photos'][0],
            caption=caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )

async def get_current_user_data(message: Message) -> tuple:
    """Получение данных текущего пользователя"""
    user_id = db.get_user_id_by_telegram_id(message.from_user.id)
    if not user_id:
        await message.answer("❌ <b>Сначала создайте анкету через /start!</b>", parse_mode="HTML")
        return None, None
    
    user_profile = db.get_user_profile_by_user_id(user_id)
    if not user_profile:
        await message.answer("❌ <b>Сначала создайте анкету через /start!</b>", parse_mode="HTML")
        return None, None
    
    return user_id, user_profile

@router.message(F.text == "🔍 Смотреть анкеты")
async def start_viewing_profiles(message: Message, state: FSMContext):
    """Начало просмотра анкет"""
    user_id, user_profile = await get_current_user_data(message)
    if not user_id:
        return
    
    # Проверяем наличие уведомлений о лайках
    pending_likes = db.get_pending_likes(user_profile['id'])
    if pending_likes:
        # Создаем клавиатуру с двумя кнопками
        builder = ReplyKeyboardBuilder()
        builder.add(
            KeyboardButton(text="💌 Мои уведомления"),
            KeyboardButton(text="🔍 Продолжить просмотр")
        )
        builder.adjust(2)
        
        await message.answer(
            "💌 <b>У вас есть непросмотренные лайки!</b>\n\n"
            "🎯 <b>Что хотите сделать?</b>\n\n"
            "1. 💌 <b>Мои уведомления</b> - просмотреть кто вам понравился\n"
            "2. 🔍 <b>Продолжить просмотр</b> - продолжить смотреть анкеты\n\n"
            "💡 <b>Рекомендация:</b> Сначала посмотрите уведомления!",
            parse_mode="HTML",
            reply_markup=builder.as_markup(resize_keyboard=True)
        )
        return
    
    # Показываем первую анкету
    await show_next_profile(message, state, user_id)

@router.message(F.text == "🔍 Продолжить просмотр")
async def continue_viewing(message: Message, state: FSMContext):
    """Продолжить просмотр анкет"""
    user_id, user_profile = await get_current_user_data(message)
    if not user_id:
        return
    
    await message.answer(
        "👀 <b>Продолжаем просмотр анкет...</b>",
        parse_mode="HTML",
        reply_markup=get_profile_view_keyboard()
    )
    await show_next_profile(message, state, user_id)

async def show_next_profile(message: Message, state: FSMContext, user_id: int = None):
    """Показать следующую анкету"""
    if not user_id:
        user_id = db.get_user_id_by_telegram_id(message.from_user.id)
    
    if not user_id:
        await message.answer("❌ <b>Пользователь не найден!</b>", parse_mode="HTML")
        await state.clear()
        return
    
    # Получаем следующую анкету
    next_profile = db.get_next_profile(user_id)
    
    if not next_profile:
        await message.answer(
            "🎉 <b>Вы просмотрели все доступные анкеты!</b>\n\n"
            "🔄 <b>Попробуйте позже или измените критерии поиска.</b>\n"
            "👥 <b>Новые пользователи появляются каждый день!</b>",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()
        return
    
    # Сохраняем текущую просматриваемую анкету
    await state.update_data(current_profile=next_profile)
    await state.set_state(ViewingStates.viewing_profile)
    
    # Добавляем запись о просмотре
    db.add_view(user_id, next_profile['id'])
    
    # Отправляем анкету
    profile_text = format_profile_preview(next_profile)
    
    if len(next_profile['photos']) > 1:
        media = [
            InputMediaPhoto(
                media=next_profile['photos'][0],
                caption=profile_text,
                parse_mode="HTML"
            )
        ]
        
        for photo in next_profile['photos'][1:]:
            media.append(InputMediaPhoto(media=photo))
        
        await message.answer_media_group(media=media)
        await message.answer(
            "🤔 <b>Что думаете об этой анкете?</b>",
            parse_mode="HTML",
            reply_markup=get_profile_view_keyboard()
        )
    else:
        await message.answer_photo(
            photo=next_profile['photos'][0],
            caption=profile_text,
            parse_mode="HTML",
            reply_markup=get_profile_view_keyboard()
        )

@router.message(ViewingStates.viewing_profile, F.text == "❤️")
async def process_like(message: Message, state: FSMContext):
    """Обработка лайка"""
    user_id, user_profile = await get_current_user_data(message)
    if not user_id:
        await state.clear()
        return
    
    data = await state.get_data()
    current_profile = data.get('current_profile')
    
    if not current_profile:
        await message.answer("❌ <b>Произошла ошибка. Начните просмотр заново.</b>", parse_mode="HTML")
        await state.clear()
        return
    
    # Добавляем лайк
    result = db.add_like(user_id, current_profile['id'], 'like')
    
    if result.get('success') and result.get('is_mutual'):
        # Взаимная симпатия!
        await handle_mutual_match(message, user_id, user_profile, current_profile)
    else:
        await message.answer(
            "❤️ <b>Лайк отправлен!</b>\n\n"
            "⏳ <b>Ждем ответа...</b>\n"
            "💌 <b>Если ответят взаимностью - получите уведомление!</b>",
            parse_mode="HTML"
        )
        
        # Отправляем уведомление владельцу анкеты, если это не бот
        target_telegram_id = db.get_telegram_id_by_profile_id(current_profile['id'])
        if target_telegram_id:
            await send_like_notification(message.bot, user_profile, current_profile, target_telegram_id)
    
    # Показываем следующую анкету
    await asyncio.sleep(1)
    await show_next_profile(message, state, user_id)

@router.message(ViewingStates.viewing_profile, F.text == "👎")
async def process_dislike(message: Message, state: FSMContext):
    """Обработка дизлайка"""
    user_id, _ = await get_current_user_data(message)
    if not user_id:
        await state.clear()
        return
    
    data = await state.get_data()
    current_profile = data.get('current_profile')
    
    if not current_profile:
        await message.answer("❌ <b>Произошла ошибка. Начните просмотр заново.</b>", parse_mode="HTML")
        await state.clear()
        return
    
    # Добавляем дизлайк
    db.add_like(user_id, current_profile['id'], 'dislike')
    
    await message.answer("👎 <b>Отметка сохранена</b>", parse_mode="HTML")
    
    # Показываем следующую анкету
    await asyncio.sleep(0.5)
    await show_next_profile(message, state, user_id)

@router.message(ViewingStates.viewing_profile, F.text == "🚫 Пожаловаться")
async def start_report(message: Message, state: FSMContext):
    """Начало процесса жалобы"""
    user_id, user_profile = await get_current_user_data(message)
    if not user_id:
        await state.clear()
        return
    
    data = await state.get_data()
    current_profile = data.get('current_profile')
    
    if not current_profile:
        await message.answer("❌ <b>Произошла ошибка. Начните просмотр заново.</b>", parse_mode="HTML")
        await state.clear()
        return
    
    # Сохраняем данные для жалобы
    await state.update_data(
        report_target_profile=current_profile,
        report_target_id=current_profile['id']
    )
    
    await message.answer(
        "🚫 <b>Пожаловаться на анкету</b>\n\n"
        "📝 <b>Выберите причину жалобы:</b>\n\n"
        "• 🤥 <b>Фейковый профиль</b> - поддельная анкета\n"
        "• 🚫 <b>Не отвечает</b> - игнорирует сообщения\n"
        "• 🔞 <b>18+ контент</b> - неприемлемый контент\n"
        "• 📢 <b>Реклама/спам</b> - коммерческие предложения\n"
        "• 😡 <b>Оскорбления</b> - грубое поведение\n"
        "• ❌ <b>Другая причина</b> - другая проблема",
        parse_mode="HTML",
        reply_markup=get_report_reasons_keyboard()
    )
    
    await state.set_state(ViewingStates.report_reason)

@router.callback_query(ViewingStates.report_reason, F.data.startswith("report_"))
async def process_report_reason(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора причины жалобы"""
    reason_map = {
        "report_fake": "🤥 Фейковый профиль",
        "report_no_response": "🚫 Не отвечает",
        "report_adult": "🔞 18+ контент",
        "report_spam": "📢 Реклама/спам",
        "report_abuse": "😡 Оскорбления",
        "report_other": "❌ Другая причина"
    }
    
    if callback.data == "report_cancel":
        await callback.message.delete()
        await callback.message.answer(
            "❌ <b>Жалоба отменена.</b>\n\n"
            "🔙 <b>Возвращаемся к просмотру анкет...</b>",
            parse_mode="HTML",
            reply_markup=get_profile_view_keyboard()
        )
        await state.set_state(ViewingStates.viewing_profile)
        await callback.answer()
        return
    
    reason = reason_map.get(callback.data, "❌ Другая причина")
    
    data = await state.get_data()
    target_profile = data.get('report_target_profile')
    
    if not target_profile:
        await callback.message.edit_text(
            "❌ <b>Произошла ошибка. Анкета не найдена.</b>",
            parse_mode="HTML"
        )
        await state.clear()
        await callback.answer()
        return
    
    # Сохраняем причину
    await state.update_data(report_reason=reason)
    
    # Отправляем жалобу админам
    await send_report_to_admins(callback.bot, callback.from_user.id, target_profile, reason)
    
    await callback.message.edit_text(
        f"✅ <b>Жалоба отправлена!</b>\n\n"
        f"📋 <b>Анкета:</b> {target_profile['name']}, {target_profile['age']} лет\n"
        f"📍 <b>Город:</b> {target_profile['city']}\n"
        f"📝 <b>Причина:</b> {reason}\n\n"
        f"👮 <b>Администраторы рассмотрят вашу жалобу в ближайшее время.</b>",
        parse_mode="HTML"
    )
    
    # Показываем следующую анкету
    user_id = db.get_user_id_by_telegram_id(callback.from_user.id)
    if user_id:
        await asyncio.sleep(2)
        await show_next_profile(callback.message, state, user_id)
    
    await callback.answer()

async def send_report_to_admins(bot, reporter_id: int, target_profile: dict, reason: str):
    """Отправка жалобы админам"""
    try:
        # Получаем список админов
        admin_ids = [8383742459]  # Замените на реальные ID админов
        
        # Получаем информацию о жалобщике
        reporter_user = db.cursor.execute(
            "SELECT username FROM users WHERE telegram_id = ?",
            (reporter_id,)
        ).fetchone()
        
        reporter_username = f"@{reporter_user['username']}" if reporter_user and reporter_user['username'] else f"ID: {reporter_id}"
        
        # Формируем сообщение для админа
        report_text = (
            f"🚨 <b>НОВАЯ ЖАЛОБА</b>\n\n"
            f"👤 <b>Жалобщик:</b> {reporter_username}\n"
            f"📅 <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            f"🎯 <b>Анкета нарушителя:</b>\n"
            f"👤 <b>Имя:</b> {target_profile['name']}\n"
            f"🎂 <b>Возраст:</b> {target_profile['age']}\n"
            f"📍 <b>Город:</b> {target_profile['city']}\n"
            f"🆔 <b>ID анкеты:</b> {target_profile['id']}\n\n"
            f"📝 <b>Причина жалобы:</b> {reason}\n\n"
            f"📊 <b>Статистика анкеты:</b>\n"
            f"❤️ <b>Лайков отправлено:</b> 0\n"
            f"👀 <b>Просмотров:</b> 0"
        )
        
        # Создаем запись о жалобе в БД
        db.cursor.execute('''
            INSERT INTO reports 
            (reporter_id, reported_profile_id, reason, status, created_at)
            VALUES (?, ?, ?, 'pending', ?)
        ''', (reporter_id, target_profile['id'], reason, datetime.now().timestamp()))
        
        report_id = db.cursor.lastrowid
        db.connection.commit()
        
        # Отправляем всем админам
        for admin_id in admin_ids:
            try:
                if target_profile['photos']:
                    await bot.send_photo(
                        chat_id=admin_id,
                        photo=target_profile['photos'][0],
                        caption=report_text,
                        parse_mode="HTML",
                        reply_markup=get_admin_report_keyboard(report_id, target_profile['id'])
                    )
                else:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=report_text,
                        parse_mode="HTML",
                        reply_markup=get_admin_report_keyboard(report_id, target_profile['id'])
                    )
            except Exception as e:
                print(f"❌ Ошибка отправки жалобы админу {admin_id}: {e}")
                
    except Exception as e:
        print(f"❌ Ошибка обработки жалобы: {e}")

@router.message(ViewingStates.viewing_profile, F.text == "🏠 Главное меню")
async def back_to_menu_from_view(message: Message, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    await message.answer(
        "↩️ <b>Возвращаюсь в главное меню:</b>",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )

# ========== ОБРАБОТЧИКИ УВЕДОМЛЕНИЙ О ЛАЙКАХ ==========

@router.message(F.text == "💌 Мои уведомления")
async def show_notifications(message: Message, state: FSMContext):
    """Показать уведомления о лайках - ПОЛНЫЕ АНКЕТЫ"""
    print(f"DEBUG: show_notifications вызвана для user_id={message.from_user.id}")
    
    user_id, user_profile = await get_current_user_data(message)
    
    if not user_id:
        print(f"DEBUG: user_id не найден")
        return
    
    if not user_profile:
        print(f"DEBUG: user_profile не найден")
        await message.answer(
            "❌ <b>У вас еще нет анкеты!</b>\n\n"
            "📝 <b>Создайте анкету через команду /start</b>",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    print(f"DEBUG: Анкета найдена, profile_id={user_profile['id']}")
    
    pending_likes = db.get_pending_likes(user_profile['id'])
    
    if not pending_likes or len(pending_likes) == 0:
        print(f"DEBUG: Нет pending_likes или пустой список")
        await message.answer(
            "📭 <b>У вас нет новых уведомлений о лайках.</b>\n\n"
            "👀 <b>Продолжайте просматривать анкеты, чтобы получить больше внимания!</b>",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    print(f"DEBUG: Найдено {len(pending_likes)} лайков, первый: {pending_likes[0]}")
    
    # Сохраняем список лайков для ответа
    await state.update_data(
        pending_likes=pending_likes, 
        current_like_index=0,
        user_profile=user_profile
    )
    await state.set_state(ViewingStates.pending_like_response)
    
    # Показываем первый лайк (ПОЛНУЮ АНКЕТУ)
    await show_next_like_notification(message, state)

async def show_next_like_notification(message: Message, state: FSMContext):
    """Показать следующее уведомление о лайке - ПОЛНАЯ АНКЕТА"""
    data = await state.get_data()
    likes_data = data.get('pending_likes', [])
    current_index = data.get('current_like_index', 0)
    
    print(f"DEBUG: show_next_like_notification: index={current_index}, total={len(likes_data)}")
    
    if current_index >= len(likes_data):
        await message.answer(
            "✅ <b>Все уведомления просмотрены!</b>",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()
        return
    
    like_data = likes_data[current_index]
    print(f"DEBUG: Обработка лайка {current_index}: {like_data}")
    
    # Получаем ПОЛНЫЙ профиль пользователя, который поставил лайк
    from_user_id = db.get_user_id_by_telegram_id(like_data['telegram_id'])
    if from_user_id:
        from_profile = db.get_user_profile_by_user_id(from_user_id)
        
        if from_profile:
            print(f"DEBUG: Найден профиль: {from_profile['name']}")
            
            # Проверяем, не является ли это ботом
            is_bot = db.cursor.execute(
                "SELECT 1 FROM bot_profiles WHERE profile_id = ?",
                (from_profile['id'],)
            ).fetchone()
            
            if is_bot:
                # Помечаем лайк от бота как отвеченный (дизлайк)
                try:
                    db.mark_like_responded(like_data['like_id'], 'dislike')
                    print(f"INFO: Лайк от бота {like_data['name']} автоматически отклонен")
                except Exception as e:
                    print(f"❌ Ошибка отметки лайка от бота: {e}")
                
                # Пропускаем бота и переходим к следующему
                await state.update_data(current_like_index=current_index + 1)
                await asyncio.sleep(0.3)
                await show_next_like_notification(message, state)
                return
            
            # Отправляем ПОЛНУЮ анкету с тремя кнопками
            profile_text = format_full_profile(from_profile)
            
            # Создаем клавиатуру с 3 кнопками
            builder = ReplyKeyboardBuilder()
            builder.add(
                KeyboardButton(text="❤️ Ответить лайком"),
                KeyboardButton(text="👎 Отказать"),
                KeyboardButton(text="🚫 Пожаловаться")
            )
            builder.adjust(3)
            
            # Сохраняем данные профиля
            await state.update_data(
                current_like_id=like_data['like_id'], 
                current_liker_telegram_id=like_data['telegram_id'],
                current_liker_profile=from_profile
            )
            
            print(f"DEBUG: Показываем анкету {from_profile['name']}")
            
            # Отправляем анкету
            if from_profile['photos']:
                if len(from_profile['photos']) > 1:
                    media = [
                        InputMediaPhoto(
                            media=from_profile['photos'][0],
                            caption=profile_text,
                            parse_mode="HTML"
                        )
                    ]
                    
                    for photo in from_profile['photos'][1:]:
                        media.append(InputMediaPhoto(media=photo))
                    
                    await message.answer_media_group(media=media)
                    await message.answer(
                        "💌 <b>Вам понравились! Что думаете об этой анкете?</b>",
                        parse_mode="HTML",
                        reply_markup=builder.as_markup(resize_keyboard=True)
                    )
                else:
                    await message.answer_photo(
                        photo=from_profile['photos'][0],
                        caption=profile_text,
                        parse_mode="HTML",
                        reply_markup=builder.as_markup(resize_keyboard=True)
                    )
            else:
                await message.answer(
                    profile_text + "\n\n💌 <b>Вам понравились! Что думаете об этой анкете?</b>",
                    parse_mode="HTML",
                    reply_markup=builder.as_markup(resize_keyboard=True)
                )
            return
        else:
            print(f"DEBUG: Не найден from_profile для telegram_id={like_data['telegram_id']}")
    else:
        print(f"DEBUG: Не найден from_user_id для telegram_id={like_data['telegram_id']}")
    
    # Если не удалось получить полный профиль
    print(f"DEBUG: Показываем базовую информацию")
    await message.answer(
        f"💌 <b>Кто-то понравился ваша анкета!</b>\n\n"
        f"👤 <b>{like_data['name']}</b>, {like_data['age']} лет\n"
        f"📍 <b>Город:</b> {like_data['city']}\n\n"
        f"❌ <b>Не удалось загрузить полную анкету.</b>",
        parse_mode="HTML",
        reply_markup=get_like_notification_keyboard()
    )
    
    await state.update_data(
        current_like_id=like_data['like_id'],
        current_liker_telegram_id=like_data['telegram_id'],
        current_liker_profile=None
    )

@router.message(ViewingStates.pending_like_response, F.text == "❤️ Ответить лайком")
async def respond_to_like_with_like(message: Message, state: FSMContext):
    """Ответить на лайк взаимностью"""
    user_id, user_profile = await get_current_user_data(message)
    if not user_id:
        await state.clear()
        return
    
    data = await state.get_data()
    current_like_id = data.get('current_like_id')
    liker_telegram_id = data.get('current_liker_telegram_id')
    liker_profile = data.get('current_liker_profile')
    
    if not current_like_id or not liker_telegram_id:
        await message.answer(
            "❌ <b>Произошла ошибка. Попробуйте еще раз.</b>",
            parse_mode="HTML"
        )
        await state.clear()
        return
    
    # Отмечаем лайк как отвеченный
    db.mark_like_responded(current_like_id, 'like')
    
    # Получаем ID пользователя, который поставил лайк
    liker_user_id = db.get_user_id_by_telegram_id(liker_telegram_id)
    
    if liker_user_id and liker_profile:
        # Проверяем, не является ли это ботом
        is_bot = db.cursor.execute(
            "SELECT 1 FROM bot_profiles WHERE profile_id = ?",
            (liker_profile['id'],)
        ).fetchone()
        
        if is_bot:
            # Для ботов просто удаляем лайк
            db.cursor.execute("DELETE FROM likes WHERE id = ?", (current_like_id,))
            db.connection.commit()
            
            await message.answer(
                "❤️ <b>Ответ отправлен!</b>",
                parse_mode="HTML"
            )
        else:
            # Ставим взаимный лайк
            result = db.add_like(user_id, liker_profile['id'], 'like')
            
            if result.get('success'):
                if result.get('is_mutual'):
                    # Взаимная симпатия!
                    from keyboards.inline_premium import get_write_message_keyboard, get_write_message_fallback_keyboard
                    
                    # Получаем username пользователя, который поставил лайк
                    db.cursor.execute('''
                        SELECT username FROM users WHERE id = ?
                    ''', (liker_profile['user_id'],))
                    
                    result_username = db.cursor.fetchone()
                    liker_username = result_username['username'] if result_username and result_username['username'] else None
                    
                    await message.answer(
                        "🎉 <b>Взаимная симпатия!</b>\n\n"
                        f"💝 <b>Вы и {liker_profile['name']} понравились друг другу!</b>\n\n"
                        f"💌 <b>Можете написать {liker_profile['name']}!</b>",
                        parse_mode="HTML",
                        reply_markup=get_write_message_keyboard(liker_telegram_id, liker_username)
                    )
                    
                    # Отправляем уведомление второму пользователю
                    try:
                        current_username = message.from_user.username
                        await message.bot.send_message(
                            chat_id=liker_telegram_id,
                            text=f"🎉 <b>Взаимная симпатия!</b>\n\n"
                                 f"💝 <b>Вы и {user_profile['name']} понравились друг другу!</b>\n\n"
                                 f"💌 <b>Можете написать {user_profile['name']}!</b>",
                            parse_mode="HTML",
                            reply_markup=get_write_message_keyboard(message.from_user.id, current_username)
                        )
                    except Exception as e:
                        print(f"❌ Ошибка отправки уведомления: {e}")
                else:
                    await message.answer(
                        f"❤️ <b>Вы ответили взаимностью {liker_profile['name']}!</b>\n\n"
                        f"⏳ <b>Ждем ответа...</b>\n"
                        f"💌 <b>Если ответит взаимностью - получите уведомление!</b>",
                        parse_mode="HTML"
                    )
            else:
                await message.answer(
                    "❌ <b>Произошла ошибка при отправке лайка.</b>\n\n"
                    "🔄 <b>Попробуйте еще раз.</b>",
                    parse_mode="HTML"
                )
    else:
        await message.answer(
            "❤️ <b>Ответ отправлен!</b>",
            parse_mode="HTML"
        )
    
    # Переходим к следующему уведомлению
    current_index = data.get('current_like_index', 0)
    await state.update_data(current_like_index=current_index + 1)
    
    await asyncio.sleep(1)
    await show_next_like_notification(message, state)

@router.message(ViewingStates.pending_like_response, F.text == "👎 Отказать")
async def respond_to_like_with_dislike(message: Message, state: FSMContext):
    """Отказать в ответ на лайк"""
    data = await state.get_data()
    current_like_id = data.get('current_like_id')
    
    if not current_like_id:
        await message.answer("❌ <b>Произошла ошибка. Попробуйте еще раз.</b>", parse_mode="HTML")
        await state.clear()
        return
    
    # Отмечаем как отказано
    db.mark_like_responded(current_like_id, 'dislike')
    
    await message.answer(
        "👎 <b>Вы отказали пользователю.</b>",
        parse_mode="HTML"
    )
    
    # Переходим к следующему уведомлению
    current_index = data.get('current_like_index', 0)
    await state.update_data(current_like_index=current_index + 1)
    
    await asyncio.sleep(0.5)
    await show_next_like_notification(message, state)

@router.message(ViewingStates.pending_like_response, F.text == "🚫 Пожаловаться")
async def report_from_notification(message: Message, state: FSMContext):
    """Пожаловаться на анкету из уведомлений"""
    data = await state.get_data()
    liker_profile = data.get('current_liker_profile')
    
    if not liker_profile:
        await message.answer(
            "❌ <b>Не удалось получить информацию об анкете.</b>",
            parse_mode="HTML"
        )
        return
    
    # Сохраняем данные для жалобы
    await state.update_data(
        report_target_profile=liker_profile,
        report_target_id=liker_profile['id']
    )
    
    await message.answer(
        "🚫 <b>Пожаловаться на анкету</b>\n\n"
        "📝 <b>Выберите причину жалобы:</b>",
        parse_mode="HTML",
        reply_markup=get_report_reasons_keyboard()
    )
    
    await state.set_state(ViewingStates.report_reason)

@router.message(ViewingStates.pending_like_response, F.text == "⏭️ Следующий")
async def skip_like_notification(message: Message, state: FSMContext):
    """Пропустить уведомление о лайке"""
    data = await state.get_data()
    current_index = data.get('current_like_index', 0)
    await state.update_data(current_like_index=current_index + 1)
    
    await asyncio.sleep(0.3)
    await show_next_like_notification(message, state)

@router.message(ViewingStates.pending_like_response, F.text == "🏠 Главное меню")
async def back_to_menu_from_notifications(message: Message, state: FSMContext):
    """Вернуться в меню из уведомлений"""
    await state.clear()
    await message.answer(
        "↩️ <b>Возвращаюсь в главное меню:</b>",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )

# Команды для управления
@router.message(Command("likes"))
async def check_likes_command(message: Message, state: FSMContext):
    """Команда для проверки лайков"""
    await show_notifications(message, state)

@router.message(Command("next"))
async def next_profile_command(message: Message, state: FSMContext):
    """Команда для показа следующей анкеты"""
    user_id, _ = await get_current_user_data(message)
    if user_id:
        await show_next_profile(message, state, user_id)

# Обработка ошибок и неверных команд
@router.message(ViewingStates.viewing_profile)
async def handle_invalid_viewing_input(message: Message):
    """Обработка неверного ввода при просмотре анкет"""
    await message.answer(
        "❌ <b>Пожалуйста, используйте кнопки для оценки анкеты:</b>\n\n"
        "❤️ - Нравится\n"
        "👎 - Не нравится\n"
        "🎁 - Отправить подарок\n"
        "🏠 - Вернуться в меню",
        parse_mode="HTML",
        reply_markup=get_profile_view_keyboard()
    )

@router.message(ViewingStates.pending_like_response)
async def handle_invalid_notification_input(message: Message):
    """Обработка неверного ввода при ответе на уведомления"""
    await message.answer(
        "❌ <b>Пожалуйста, выберите действие для этого лайка:</b>\n\n"
        "❤️ - Ответить взаимностью\n"
        "👎 - Отказать\n"
        "🚫 - Пожаловаться\n"
        "⏭️ - Следующий\n"
        "🏠 - Вернуться в меню",
        parse_mode="HTML"
    )

def format_profile_preview(profile: dict) -> str:
    """Форматирование предпросмотра анкеты"""
    interests_preview = ', '.join(profile['interests'][:3]) if profile['interests'] else 'Не указаны'
    if len(profile['interests']) > 3:
        interests_preview += f" и ещё {len(profile['interests']) - 3}"
    
    return (
        f"👤 <b>{profile['name']}</b>, {profile['age']} лет\n"
        f"📍 <b>Город:</b> {profile['city']}\n"
        f"💘 <b>Ищет:</b> {profile['looking_for']}\n\n"
        f"🎯 <b>Интересы:</b> {interests_preview}"
    )


def format_full_profile(profile: dict) -> str:
    """Форматирование полной анкеты"""
    interests_text = ", ".join(profile['interests']) if profile['interests'] else "Не указаны"
    
    return (
        f"👤 <b>{profile['name']}</b>, {profile['age']} лет\n"
        f"📍 <b>Город:</b> {profile['city']}\n"
        f"💘 <b>Ищет:</b> {profile['looking_for']}\n\n"
        f"📝 <b>О себе:</b>\n{profile['about']}\n\n"
        f"🎯 <b>Интересы:</b> {interests_text}"
    )


def format_match_notification(user_profile: dict, match_profile: dict) -> str:
    """Форматирование уведомления о мэтче"""
    about_preview = match_profile['about'][:100] + "..." if len(match_profile['about']) > 100 else match_profile['about']
    
    return (
        f"🎉 <b>У вас взаимная симпатия!</b>\n\n"
        f"👤 <b>{match_profile['name']}</b>, {match_profile['age']} лет\n"
        f"📍 <b>Город:</b> {match_profile['city']}\n"
        f"💘 <b>Ищет:</b> {match_profile['looking_for']}\n\n"
        f"📝 <b>О себе:</b>\n{about_preview}"
    )


async def send_like_notification(bot, from_profile: dict, to_profile: dict, to_telegram_id: int):
    """Отправка уведомления о лайке"""
    try:
        # Получаем количество лайков у пользователя
        db.cursor.execute('''
            SELECT COUNT(*) as like_count 
            FROM likes 
            WHERE to_profile_id = ? 
            AND like_type = 'like' 
            AND is_mutual = 0
        ''', (to_profile['id'],))
        
        result = db.cursor.fetchone()
        like_count = result['like_count'] if result else 0
        
        # Создаем текст уведомления
        notification_text = (
            f"💌 <b>Вашей анкетой заинтересовались!</b>\n\n"
            f"👤 <b>{like_count} человек</b> поставили вам лайк\n\n"
            f"✨ <b>Посмотреть, кому вы понравились?</b>\n"
            f"🔍 <b>Используйте команду</b> /likes\n"
            f"💡 <b>Или кнопку</b> '💌 Мои уведомления' в меню"
        )
        
        # Отправляем простое текстовое уведомление
        await bot.send_message(
            chat_id=to_telegram_id,
            text=notification_text,
            parse_mode="HTML"
        )
            
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления о лайке: {e}")


async def handle_mutual_match(message, user_id: int, user_profile: dict, liked_profile: dict):
    """Обработка взаимной симпатии"""
    try:
        from keyboards.inline_premium import get_write_message_keyboard, get_write_message_fallback_keyboard
        
        # Получаем username пользователя, который поставил лайк
        db.cursor.execute('''
            SELECT username FROM users WHERE id = ?
        ''', (liked_profile['user_id'],))
        
        result = db.cursor.fetchone()
        liked_username = result['username'] if result and result['username'] else None
        
        # Отправляем сообщение текущему пользователю
        target_telegram_id = db.get_telegram_id_by_profile_id(liked_profile['id'])
        await message.answer(
            "🎉 <b>Взаимная симпатия!</b>\n\n"
            f"💝 <b>Вы и {liked_profile['name']} понравились друг другу!</b>\n\n"
            f"💌 <b>Можете написать {liked_profile['name']}!</b>",
            parse_mode="HTML",
            reply_markup=get_write_message_keyboard(target_telegram_id, liked_username)
        )
        
        # Отправляем уведомление второму пользователю
        if target_telegram_id:
            try:
                # Получаем username текущего пользователя
                current_username = message.from_user.username
                
                await message.bot.send_message(
                    chat_id=target_telegram_id,
                    text=f"🎉 <b>Взаимная симпатия!</b>\n\n"
                         f"💝 <b>Вы и {user_profile['name']} понравились друг другу!</b>\n\n"
                         f"💌 <b>Можете написать {user_profile['name']}!</b>",
                    parse_mode="HTML",
                    reply_markup=get_write_message_keyboard(message.from_user.id, current_username)
                )
            except Exception as e:
                print(f"❌ Ошибка отправки уведомления о мэтче: {e}")
                
    except Exception as e:
        print(f"❌ Ошибка обработки взаимной симпатии: {e}")