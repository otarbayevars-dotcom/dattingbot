from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, FSInputFile, PhotoSize
from aiogram.types.input_media_photo import InputMediaPhoto
from typing import List
import re

from models import Database
from keyboards.replay import *
from keyboards.inline import *

router = Router()
db = Database()

class ProfileCreation(StatesGroup):
    """Состояния для создания анкеты"""
    name = State()
    age = State()
    gender = State()
    looking_for = State()
    city = State()
    interests = State()
    about = State()
    photos = State()

@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    
    # Добавляем пользователя в базу
    db.add_user(message.from_user.id, message.from_user.username)
    
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

@router.message(ProfileCreation.name)
async def process_name(message: Message, state: FSMContext):
    """Обработка имени"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ <b>Создание анкеты отменено.</b>\n\n"
            "🔙 <b>Возвращаюсь в главное меню:</b>",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    if len(message.text) < 2:
        await message.answer(
            "❌ <b>Имя должно содержать минимум 2 символа.</b>\n\n"
            "📝 <b>Попробуй еще раз:</b>",
            parse_mode="HTML"
        )
        return
    
    await state.update_data(name=message.text)
    await message.answer(
        "🎂 <b>Сколько тебе лет?</b>\n\n"
        "ℹ️ <i>Минимальный возраст - 18 лет</i>",
        parse_mode="HTML"
    )
    await state.set_state(ProfileCreation.age)

@router.message(ProfileCreation.age)
async def process_age(message: Message, state: FSMContext):
    """Обработка возраста"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ <b>Создание анкеты отменено.</b>\n\n"
            "🔙 <b>Возвращаюсь в главное меню:</b>",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    if not message.text.isdigit():
        await message.answer(
            "❌ <b>Пожалуйста, введи число.</b>\n\n"
            "🎂 <b>Сколько тебе лет?</b>",
            parse_mode="HTML"
        )
        return
    
    age = int(message.text)
    if age < 18:
        await message.answer(
            "❌ <b>Извини, в боте могут регистрироваться только пользователи старше 18 лет.</b>\n\n"
            "🔙 <b>Возвращаюсь в главное меню:</b>",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()
        return
    if age > 100:
        await message.answer(
            "❌ <b>Пожалуйста, введи реальный возраст.</b>\n\n"
            "🎂 <b>Сколько тебе лет?</b>",
            parse_mode="HTML"
        )
        return
    
    await state.update_data(age=age)
    await message.answer(
        "👫 <b>Выбери свой пол:</b>",
        parse_mode="HTML",
        reply_markup=get_gender_keyboard()
    )
    await state.set_state(ProfileCreation.gender)

@router.message(ProfileCreation.gender, F.text.in_(["👨 Мужчина", "👩 Женщина", "🧑 Другой"]))
async def process_gender(message: Message, state: FSMContext):
    """Обработка пола"""
    gender_map = {
        "👨 Мужчина": "Мужчина",
        "👩 Женщина": "Женщина",
        "🧑 Другой": "Другой"
    }
    
    gender = gender_map[message.text]
    await state.update_data(gender=gender)
    await message.answer(
        "💘 <b>Кого ты ищешь?</b>",
        parse_mode="HTML",
        reply_markup=get_looking_for_keyboard()
    )
    await state.set_state(ProfileCreation.looking_for)

@router.message(ProfileCreation.gender)
async def process_gender_invalid(message: Message):
    """Обработка неверного ввода пола"""
    await message.answer(
        "❌ <b>Пожалуйста, выбери пол с помощью кнопок ниже:</b>",
        parse_mode="HTML",
        reply_markup=get_gender_keyboard()
    )

@router.message(ProfileCreation.looking_for, F.text.in_(["👨 Парня", "👩 Девушку", "👥 Оба"]))
async def process_looking_for(message: Message, state: FSMContext):
    """Обработка кого ищет пользователь"""
    looking_map = {
        "👨 Парня": "Парня",
        "👩 Девушку": "Девушку",
        "👥 Оба": "Оба"
    }
    
    looking_for = looking_map[message.text]
    await state.update_data(looking_for=looking_for)
    await message.answer(
        "📍 <b>Из какого ты города?</b>\n\n"
        "ℹ️ <i>Например: Москва, Санкт-Петербург, Новосибирск</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(ProfileCreation.city)

@router.message(ProfileCreation.looking_for)
async def process_looking_for_invalid(message: Message):
    """Обработка неверного ввода"""
    await message.answer(
        "❌ <b>Пожалуйста, выбери вариант с помощью кнопок ниже:</b>",
        parse_mode="HTML",
        reply_markup=get_looking_for_keyboard()
    )

@router.message(ProfileCreation.city)
async def process_city(message: Message, state: FSMContext):
    """Обработка города"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ <b>Создание анкеты отменено.</b>\n\n"
            "🔙 <b>Возвращаюсь в главное меню:</b>",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    if len(message.text) < 2:
        await message.answer(
            "❌ <b>Название города должно содержать минимум 2 символа.</b>\n\n"
            "📍 <b>Попробуй еще раз:</b>",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(city=message.text.title())
    
    # Переходим к выбору интересов
    await message.answer(
        "🎯 <b>Выбери свои интересы</b> (можно выбрать несколько):\n\n"
        "ℹ️ <i>Нажми на интерес, чтобы выбрать/отменить</i>\n"
        "✅ <i>Когда закончишь, нажми 'Готово'</i>",
        parse_mode="HTML",
        reply_markup=get_interests_keyboard()
    )
    await state.set_state(ProfileCreation.interests)

@router.callback_query(ProfileCreation.interests, F.data.startswith("interest_"))
async def process_interest_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора интересов"""
    data = await state.get_data()
    selected_interests = data.get('interests', [])
    
    interest_name = callback.data.replace("interest_", "")
    
    if interest_name in selected_interests:
        selected_interests.remove(interest_name)
    else:
        selected_interests.append(interest_name)
    
    await state.update_data(interests=selected_interests)
    
    # Обновляем клавиатуру
    await callback.message.edit_reply_markup(
        reply_markup=get_interests_keyboard(selected_interests)
    )
    await callback.answer()

@router.callback_query(ProfileCreation.interests, F.data == "interests_done")
async def process_interests_done(callback: CallbackQuery, state: FSMContext):
    """Завершение выбора интересов"""
    data = await state.get_data()
    selected_interests = data.get('interests', [])
    
    if len(selected_interests) == 0:
        await callback.answer("❌ Выбери хотя бы один интерес!")
        return
    
    await callback.message.delete()
    await callback.message.answer(
        "📝 <b>Отлично! Теперь расскажи немного о себе:</b>\n\n"
        "ℹ️ <i>Максимум 500 символов</i>\n"
        "✍️ <i>Расскажи о своих увлечениях, характере, чем занимаешься</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(ProfileCreation.about)

@router.message(ProfileCreation.about)
async def process_about(message: Message, state: FSMContext):
    """Обработка информации о себе"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ <b>Создание анкеты отменено.</b>\n\n"
            "🔙 <b>Возвращаюсь в главное меню:</b>",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    about = message.text
    
    if len(about) > 500:
        await message.answer(
            "❌ <b>Описание слишком длинное. Максимум 500 символов.</b>\n\n"
            "📝 <b>Попробуй еще раз:</b>",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(about=about)
    
    # Инициализируем список фотографий
    await state.update_data(photos=[])
    
    await message.answer(
        "📸 <b>Отлично! Теперь добавь фотографии для своей анкеты.</b>\n\n"
        "📋 <b>Можно загрузить от 1 до 3 фотографий.</b>\n"
        "🖼️ <b>Отправь первую фотографию:</b>\n\n"
        "ℹ️ <i>Отправляй фото как документ (не сжатое)</i>\n"
        "💡 <i>Лучше использовать портретные фото</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(ProfileCreation.photos)

@router.message(ProfileCreation.photos, F.photo)
async def process_photo(message: Message, state: FSMContext):
    """Обработка фотографий"""
    data = await state.get_data()
    photos = data.get('photos', [])
    
    if len(photos) >= 3:
        await message.answer(
            "📸 <b>Максимум 3 фотографии.</b>\n\n"
            "✅ <b>Нажми 'Завершить регистрацию' чтобы закончить.</b>",
            parse_mode="HTML",
            reply_markup=get_finish_registration_keyboard()
        )
        return
    
    # Получаем самую качественную версию фото
    photo = message.photo[-1]
    
    photos.append({
        'file_id': photo.file_id,
        'file_unique_id': photo.file_unique_id
    })
    
    await state.update_data(photos=photos)
    
    if len(photos) == 1:
        await message.answer(
            "✅ <b>Первая фотография добавлена!</b>\n\n"
            f"📋 <b>Можно добавить еще {2 - len(photos)} фото.</b>\n"
            "✅ <b>Или нажми 'Завершить регистрацию', чтобы закончить.</b>",
            parse_mode="HTML",
            reply_markup=get_finish_registration_keyboard()
        )
    elif len(photos) < 3:
        await message.answer(
            f"✅ <b>Фото добавлено! Можно добавить еще {3 - len(photos)}.</b>\n\n"
            "✅ <b>Или нажми 'Завершить регистрацию', чтобы закончить.</b>",
            parse_mode="HTML",
            reply_markup=get_finish_registration_keyboard()
        )
    else:
        await message.answer(
            "✅ <b>Максимальное количество фото достигнуто!</b>\n\n"
            "✅ <b>Нажми 'Завершить регистрацию'.</b>",
            parse_mode="HTML",
            reply_markup=get_finish_registration_keyboard()
        )

@router.message(ProfileCreation.photos, F.text == "✅ Завершить регистрацию")
async def finish_registration(message: Message, state: FSMContext):
    """Завершение регистрации"""
    data = await state.get_data()
    photos = data.get('photos', [])
    
    if len(photos) == 0:
        await message.answer(
            "❌ <b>Нужно добавить хотя бы одну фотографию!</b>\n\n"
            "🖼️ <b>Отправьте фото:</b>",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    # Создаем анкету в базе данных
    user_id = db.add_user(message.from_user.id, message.from_user.username)
    profile_id = db.create_profile(user_id, data)
    
    if profile_id:
        # Сохраняем фотографии
        for i, photo in enumerate(photos):
            db.add_photo(profile_id, photo['file_id'], photo['file_unique_id'], i)
        
        # Получаем созданную анкету для показа
        profile = db.get_user_profile(message.from_user.id)
        
        # Формируем сообщение с анкетой
        profile_text = format_profile_text(profile)
        
        # Отправляем первую фотографию с информацией
        if len(profile['photos']) > 1:
            # Если несколько фото, отправляем альбом
            media = [
                InputMediaPhoto(
                    media=profile['photos'][0],
                    caption=profile_text,
                    parse_mode="HTML"
                )
            ]

            for photo in profile['photos'][1:]:
                media.append(InputMediaPhoto(media=photo))

            await message.answer_media_group(media=media)
            
            # Отправляем дополнительное сообщение с клавиатурой
            await message.answer(
                "🎉 <b>Регистрация завершена! Твоя анкета создана.</b>\n\n"
                "🔍 <b>Теперь ты можешь:</b>\n"
                "• 👀 Смотреть анкеты других пользователей\n"
                "• ✏️ Редактировать свою анкету\n"
                "• ⭐ Получить премиум для большего внимания",
                parse_mode="HTML",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            # Если одна фото, отправляем просто фото с текстом
            await message.answer_photo(
                photo=profile['photos'][0],
                caption=profile_text,
                parse_mode="HTML"
            )
            
            await message.answer(
                "🎉 <b>Регистрация завершена! Твоя анкета создана.</b>\n\n"
                "🔍 <b>Теперь ты можешь:</b>\n"
                "• 👀 Смотреть анкеты других пользователей\n"
                "• ✏️ Редактировать свою анкету\n"
                "• ⭐ Получить премиум для большего внимания",
                parse_mode="HTML",
                reply_markup=get_main_menu_keyboard()
            )
    else:
        await message.answer(
            "❌ <b>Произошла ошибка при создании анкеты.</b>\n\n"
            "🔄 <b>Попробуй еще раз через /start</b>",
            parse_mode="HTML",
            reply_markup=None
        )
    
    await state.clear()

@router.message(ProfileCreation.photos, F.text == "❌ Отмена")
async def cancel_registration(message: Message, state: FSMContext):
    """Отмена регистрации"""
    await state.clear()
    await message.answer(
        "❌ <b>Регистрация отменена.</b>\n\n"
        "🔄 <b>Используй /start, чтобы начать заново.</b>",
        parse_mode="HTML",
        reply_markup=None
    )

def format_profile_text(profile: dict) -> str:
    """Форматирование текста анкеты для отображения"""
    interests_text = ", ".join(profile['interests']) if profile['interests'] else "Не указаны"
    
    return (
        f"👤 <b>{profile['name']}</b>, {profile['age']} лет\n"
        f"📍 <b>Город:</b> {profile['city']}\n"
        f"💘 <b>Ищет:</b> {profile['looking_for']}\n\n"
        f"📝 <b>О себе:</b>\n{profile['about']}\n\n"
        f"🎯 <b>Интересы:</b> {interests_text}\n\n"
        f"🆔 <b>ID анкеты:</b> {profile['id']}"
    )

# ========== ОБРАБОТЧИКИ ГЛАВНОГО МЕНЮ ==========

@router.message(F.text == "👤 Моя анкета")
async def show_my_profile(message: Message, state: FSMContext):
    """Показ своей анкеты - теперь перенаправляет в profile_management"""
    # Импортируем здесь, чтобы избежать циклического импорта
    from handlers.profile_management import my_profile_menu
    await my_profile_menu(message, state)

@router.message(F.text == "🔍 Смотреть анкеты")
async def show_profiles(message: Message, state: FSMContext):
    """Показ анкет других пользователей - теперь перенаправляет в profile_view"""
    # Импортируем здесь, чтобы избежать циклического импорта
    from handlers.profile_view import start_viewing_profiles
    await start_viewing_profiles(message, state)

# ========== ОБРАБОТЧИК ДЛЯ КОМАНДЫ HELP ==========

@router.message(Command("help"))
async def help_command(message: Message):
    """Команда помощи"""
    help_text = (
        "❓ <b>Помощь по использованию бота</b>\n\n"
        
        "🎯 <b>Основные команды:</b>\n"
        "• /start - Начать или создать анкету\n"
        "• /help - Показать эту справку\n"
        "• /profile - Моя анкета\n"
        "• /likes - Мои уведомления о лайках\n"
        "• /next - Следующая анкета\n"
        "• /stats - Моя статистика\n"
        "• /premium - Информация о премиум\n"
        "• /referral - Реферальная программа\n"
        "• /admin - Админ-панель (только для админов)\n\n"
        
        "🔍 <b>Как это работает:</b>\n"
        "1. 📝 Создайте анкету через /start\n"
        "2. 👀 Нажмите 'Смотреть анкеты'\n"
        "3. ❤️ Ставьте лайки понравившимся анкетам\n"
        "4. 💝 Если лайк взаимный - получите уведомление\n"
        "5. ✉️ Напишите человеку через кнопку 'Написать'\n\n"
        
        "⭐ <b>Премиум возможности:</b>\n"
        "• 🚀 Повышенная видимость вашей анкеты\n"
        "• 🔍 Расширенный поиск и фильтры\n"
        "• 💌 Больше возможностей для общения\n"
        "• 🎁 Отправка подарков\n\n"
        
        "🎁 <b>Бесплатный премиум:</b>\n"
        "• 📢 Пригласите 10 друзей\n"
        "• ✅ Каждый должен создать анкету\n"
        "• 🎉 Получите премиум на 1 день!\n\n"
        
        "💡 <b>Советы:</b>\n"
        "• 🖼️ Добавьте качественные фото\n"
        "• 📝 Напишите интересное описание\n"
        "• 🎯 Укажите настоящие интересы\n"
        "• ⭐ Используйте премиум для лучших результатов\n\n"
        
        "🆘 <b>Если возникли проблемы:</b>\n"
        "• 🔄 Перезапустите бота командой /start\n"
        "• ✏️ Отредактируйте анкету если нужно\n"
        "• 📧 Свяжитесь с поддержкой через @админ\n\n"
        
        "🌟 <b>Удачи в поисках!</b>"
    )
    
    await message.answer(help_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())

# ========== ОБРАБОТЧИК ДЛЯ КОМАНДЫ CANCEL ==========

@router.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext):
    """Команда отмены текущего действия"""
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer(
            "ℹ️ <b>Нет активных действий для отмены.</b>\n\n"
            "🎯 <b>Выберите действие:</b>",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    await state.clear()
    await message.answer(
        "❌ <b>Действие отменено.</b>\n\n"
        "🔙 <b>Возвращаюсь в главное меню:</b>",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )