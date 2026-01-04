from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from typing import List, Optional
import asyncio
from datetime import datetime

from models import Database
from keyboards.replay import *
from keyboards.inline import get_interests_keyboard

router = Router()
db = Database()

class EditProfileStates(StatesGroup):
    """Состояния для редактирования анкеты"""
    waiting_field = State()
    edit_name = State()
    edit_age = State()
    edit_gender = State()
    edit_looking_for = State()
    edit_city = State()
    edit_interests = State()
    edit_about = State()
    edit_photos = State()
    confirm_delete = State()

@router.message(F.text == "👤 Моя анкета")
async def my_profile_menu(message: Message, state: FSMContext):
    """Меню работы с анкетой"""
    user_id = db.get_user_id_by_telegram_id(message.from_user.id)
    
    if not user_id:
        await message.answer(
            "У вас еще нет анкеты. Создайте её через команду /start",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    profile_exists = db.is_profile_exists(user_id)
    
    if not profile_exists:
        await message.answer(
            "У вас еще нет анкеты. Создайте её через команду /start",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    await message.answer(
        "👤 <b>Моя анкета</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=get_profile_menu_keyboard()
    )

@router.message(F.text == "👀 Посмотреть анкету")
async def view_my_profile(message: Message):
    """Просмотр своей анкеты"""
    profile = db.get_user_profile(message.from_user.id)
    
    if not profile:
        await message.answer(
            "У вас еще нет анкеты. Создайте её через команду /start",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Форматируем текст анкеты
    interests_text = ", ".join(profile['interests']) if profile['interests'] else "Не указаны"
    profile_text = (
        f"👤 <b>Ваша анкета</b>\n\n"
        f"🆔 ID: {profile['id']}\n"
        f"👤 Имя: {profile['name']}\n"
        f"🎂 Возраст: {profile['age']}\n"
        f"👫 Пол: {profile['gender']}\n"
        f"💘 Ищу: {profile['looking_for']}\n"
        f"📍 Город: {profile['city']}\n\n"
        f"📝 <b>О себе:</b>\n{profile['about']}\n\n"
        f"🎯 <b>Интересы:</b>\n{interests_text}\n\n"
        f"📸 Фотографий: {len(profile['photos'])}"
    )
    
    if profile['photos']:
        if len(profile['photos']) > 1:
            media = [
                InputMediaPhoto(
                    media=profile['photos'][0],
                    caption=profile_text
                )
            ]
            for photo in profile['photos'][1:]:
                media.append(InputMediaPhoto(media=photo))
            
            await message.answer_media_group(
                media=media,
                parse_mode='HTML'
                )
            await message.answer(
                "Выберите действие:",
                reply_markup=get_profile_menu_keyboard()
            )
        else:
            await message.answer_photo(
                photo=profile['photos'][0],
                caption=profile_text,
                reply_markup=get_profile_menu_keyboard(),
                parse_mode='HTML'
            )
    else:
        await message.answer(
            profile_text,
            parse_mode="HTML",
            reply_markup=get_profile_menu_keyboard()
        )

@router.message(F.text == "✏️ Редактировать анкету")
async def edit_profile_menu(message: Message, state: FSMContext):
    """Меню редактирования анкеты"""
    user_id = db.get_user_id_by_telegram_id(message.from_user.id)
    
    if not user_id:
        await message.answer(
            "У вас еще нет анкеты. Создайте её через команду /start",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    profile_exists = db.is_profile_exists(user_id)
    
    if not profile_exists:
        await message.answer(
            "У вас еще нет анкеты. Создайте её через команду /start",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    await message.answer(
        "✏️ <b>Редактирование анкеты</b>\n\n"
        "Выберите, что хотите изменить:",
        parse_mode="HTML",
        reply_markup=get_edit_profile_keyboard()
    )

@router.message(F.text == "✏️ Изменить имя")
async def edit_name_start(message: Message, state: FSMContext):
    """Начало изменения имени"""
    await message.answer(
        "✏️ Введите новое имя:\n\n"
        "<i>Имя должно содержать минимум 2 символа</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(EditProfileStates.edit_name)

@router.message(EditProfileStates.edit_name)
async def edit_name_process(message: Message, state: FSMContext):
    """Обработка изменения имени"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "Изменение имени отменено.",
            reply_markup=get_edit_profile_keyboard()
        )
        return
    
    if len(message.text) < 2:
        await message.answer(
            "Имя должно содержать минимум 2 символа. Попробуйте еще раз:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    user_id = db.get_user_id_by_telegram_id(message.from_user.id)
    profile = db.get_user_profile_by_user_id(user_id)
    
    if profile:
        success = db.update_profile(profile['id'], 'name', message.text)
        
        if success:
            await message.answer(
                f"✅ Имя успешно изменено на: {message.text}",
                reply_markup=get_edit_profile_keyboard()
            )
        else:
            await message.answer(
                "❌ Произошла ошибка при изменении имени. Попробуйте еще раз.",
                reply_markup=get_edit_profile_keyboard()
            )
    else:
        await message.answer(
            "❌ Анкета не найдена.",
            reply_markup=get_edit_profile_keyboard()
        )
    
    await state.clear()

@router.message(F.text == "✏️ Изменить возраст")
async def edit_age_start(message: Message, state: FSMContext):
    """Начало изменения возраста"""
    await message.answer(
        "✏️ Введите новый возраст:\n\n"
        "<i>Возраст должен быть от 18 до 100 лет</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(EditProfileStates.edit_age)

@router.message(EditProfileStates.edit_age)
async def edit_age_process(message: Message, state: FSMContext):
    """Обработка изменения возраста"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "Изменение возраста отменено.",
            reply_markup=get_edit_profile_keyboard()
        )
        return
    
    if not message.text.isdigit():
        await message.answer(
            "Пожалуйста, введите число. Введите возраст:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    age = int(message.text)
    
    if age < 18:
        await message.answer(
            "❌ Минимальный возраст - 18 лет. Введите возраст:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    if age > 100:
        await message.answer(
            "❌ Пожалуйста, введите реальный возраст. Введите возраст:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    user_id = db.get_user_id_by_telegram_id(message.from_user.id)
    profile = db.get_user_profile_by_user_id(user_id)
    
    if profile:
        success = db.update_profile(profile['id'], 'age', str(age))
        
        if success:
            await message.answer(
                f"✅ Возраст успешно изменен на: {age}",
                reply_markup=get_edit_profile_keyboard()
            )
        else:
            await message.answer(
                "❌ Произошла ошибка при изменении возраста. Попробуйте еще раз.",
                reply_markup=get_edit_profile_keyboard()
            )
    else:
        await message.answer(
            "❌ Анкета не найдена.",
            reply_markup=get_edit_profile_keyboard()
        )
    
    await state.clear()

@router.message(F.text == "✏️ Изменить пол")
async def edit_gender_start(message: Message, state: FSMContext):
    """Начало изменения пола"""
    await message.answer(
        "✏️ Выберите ваш пол:",
        reply_markup=get_gender_keyboard()
    )
    await state.set_state(EditProfileStates.edit_gender)

@router.message(EditProfileStates.edit_gender, F.text.in_(["👨 Мужчина", "👩 Женщина", "🧑 Другой"]))
async def edit_gender_process(message: Message, state: FSMContext):
    """Обработка изменения пола"""
    gender_map = {
        "👨 Мужчина": "Мужчина",
        "👩 Женщина": "Женщина",
        "🧑 Другой": "Другой"
    }
    
    gender = gender_map[message.text]
    
    user_id = db.get_user_id_by_telegram_id(message.from_user.id)
    profile = db.get_user_profile_by_user_id(user_id)
    
    if profile:
        success = db.update_profile(profile['id'], 'gender', gender)
        
        if success:
            await message.answer(
                f"✅ Пол успешно изменен на: {gender}",
                reply_markup=get_edit_profile_keyboard()
            )
        else:
            await message.answer(
                "❌ Произошла ошибка при изменении пола. Попробуйте еще раз.",
                reply_markup=get_edit_profile_keyboard()
            )
    else:
        await message.answer(
            "❌ Анкета не найдена.",
            reply_markup=get_edit_profile_keyboard()
        )
    
    await state.clear()

@router.message(EditProfileStates.edit_gender)
async def edit_gender_invalid(message: Message):
    """Обработка неверного ввода пола"""
    await message.answer(
        "Пожалуйста, выберите пол с помощью кнопок ниже:",
        reply_markup=get_gender_keyboard()
    )

@router.message(F.text == "✏️ Изменить кого ищу")
async def edit_looking_for_start(message: Message, state: FSMContext):
    """Начало изменения кого ищет"""
    await message.answer(
        "✏️ Кого вы ищете?",
        reply_markup=get_looking_for_keyboard()
    )
    await state.set_state(EditProfileStates.edit_looking_for)

@router.message(EditProfileStates.edit_looking_for, F.text.in_(["👨 Парня", "👩 Девушку", "👥 Оба"]))
async def edit_looking_for_process(message: Message, state: FSMContext):
    """Обработка изменения кого ищет"""
    looking_map = {
        "👨 Парня": "Парня",
        "👩 Девушку": "Девушку",
        "👥 Оба": "Оба"
    }
    
    looking_for = looking_map[message.text]
    
    user_id = db.get_user_id_by_telegram_id(message.from_user.id)
    profile = db.get_user_profile_by_user_id(user_id)
    
    if profile:
        success = db.update_profile(profile['id'], 'looking_for', looking_for)
        
        if success:
            await message.answer(
                f"✅ Теперь вы ищете: {looking_for}",
                reply_markup=get_edit_profile_keyboard()
            )
        else:
            await message.answer(
                "❌ Произошла ошибка при изменении. Попробуйте еще раз.",
                reply_markup=get_edit_profile_keyboard()
            )
    else:
        await message.answer(
            "❌ Анкета не найдена.",
            reply_markup=get_edit_profile_keyboard()
        )
    
    await state.clear()

@router.message(EditProfileStates.edit_looking_for)
async def edit_looking_for_invalid(message: Message):
    """Обработка неверного ввода"""
    await message.answer(
        "Пожалуйста, выберите вариант с помощью кнопок ниже:",
        reply_markup=get_looking_for_keyboard()
    )

@router.message(F.text == "✏️ Изменить город")
async def edit_city_start(message: Message, state: FSMContext):
    """Начало изменения города"""
    await message.answer(
        "✏️ Введите новый город:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(EditProfileStates.edit_city)

@router.message(EditProfileStates.edit_city)
async def edit_city_process(message: Message, state: FSMContext):
    """Обработка изменения города"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "Изменение города отменено.",
            reply_markup=get_edit_profile_keyboard()
        )
        return
    
    if len(message.text) < 2:
        await message.answer(
            "Название города должно содержать минимум 2 символа. Попробуйте еще раз:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    user_id = db.get_user_id_by_telegram_id(message.from_user.id)
    profile = db.get_user_profile_by_user_id(user_id)
    
    if profile:
        success = db.update_profile(profile['id'], 'city', message.text.title())
        
        if success:
            await message.answer(
                f"✅ Город успешно изменен на: {message.text.title()}",
                reply_markup=get_edit_profile_keyboard()
            )
        else:
            await message.answer(
                "❌ Произошла ошибка при изменении города. Попробуйте еще раз.",
                reply_markup=get_edit_profile_keyboard()
            )
    else:
        await message.answer(
            "❌ Анкета не найдена.",
            reply_markup=get_edit_profile_keyboard()
        )
    
    await state.clear()

@router.message(F.text == "✏️ Изменить интересы")
async def edit_interests_start(message: Message, state: FSMContext):
    """Начало изменения интересов"""
    user_id = db.get_user_id_by_telegram_id(message.from_user.id)
    profile = db.get_user_profile_by_user_id(user_id)
    
    if not profile:
        await message.answer(
            "❌ Анкета не найдена.",
            reply_markup=get_edit_profile_keyboard()
        )
        return
    
    await message.answer(
        "✏️ Выберите ваши интересы (можно выбрать несколько):",
        reply_markup=get_interests_keyboard(profile.get('interests', []))
    )
    
    # Сохраняем текущие интересы для редактирования
    await state.update_data(current_interests=profile.get('interests', []))
    await state.set_state(EditProfileStates.edit_interests)

@router.callback_query(EditProfileStates.edit_interests, F.data.startswith("interest_"))
async def edit_interest_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора интересов при редактировании"""
    data = await state.get_data()
    current_interests = data.get('current_interests', [])
    
    interest_name = callback.data.replace("interest_", "")
    
    if interest_name in current_interests:
        current_interests.remove(interest_name)
    else:
        current_interests.append(interest_name)
    
    await state.update_data(current_interests=current_interests)
    
    # Обновляем клавиатуру
    await callback.message.edit_reply_markup(
        reply_markup=get_interests_keyboard(current_interests)
    )
    await callback.answer()

@router.callback_query(EditProfileStates.edit_interests, F.data == "interests_done")
async def edit_interests_done(callback: CallbackQuery, state: FSMContext):
    """Завершение выбора интересов при редактировании"""
    data = await state.get_data()
    current_interests = data.get('current_interests', [])
    
    if len(current_interests) == 0:
        await callback.answer("Выберите хотя бы один интерес!")
        return
    
    user_id = db.get_user_id_by_telegram_id(callback.from_user.id)
    profile = db.get_user_profile_by_user_id(user_id)
    
    if profile:
        success = db.update_profile_interests(profile['id'], current_interests)
        
        if success:
            await callback.message.delete()
            await callback.message.answer(
                f"✅ Интересы успешно обновлены!\n\n"
                f"Выбрано интересов: {len(current_interests)}\n"
                f"Список: {', '.join(current_interests)}",
                reply_markup=get_edit_profile_keyboard()
            )
        else:
            await callback.message.delete()
            await callback.message.answer(
                "❌ Произошла ошибка при обновлении интересов. Попробуйте еще раз.",
                reply_markup=get_edit_profile_keyboard()
            )
    else:
        await callback.message.delete()
        await callback.message.answer(
            "❌ Анкета не найдена.",
            reply_markup=get_edit_profile_keyboard()
        )
    
    await state.clear()

@router.message(F.text == "✏️ Изменить описание")
async def edit_about_start(message: Message, state: FSMContext):
    """Начало изменения описания"""
    await message.answer(
        "✏️ Напишите новое описание о себе:\n\n"
        "<i>Максимум 500 символов</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(EditProfileStates.edit_about)

@router.message(EditProfileStates.edit_about)
async def edit_about_process(message: Message, state: FSMContext):
    """Обработка изменения описания"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "Изменение описания отменено.",
            reply_markup=get_edit_profile_keyboard()
        )
        return
    
    about = message.text
    
    if len(about) > 500:
        await message.answer(
            "Описание слишком длинное. Максимум 500 символов. Попробуйте еще раз:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    user_id = db.get_user_id_by_telegram_id(message.from_user.id)
    profile = db.get_user_profile_by_user_id(user_id)
    
    if profile:
        success = db.update_profile(profile['id'], 'about', about)
        
        if success:
            await message.answer(
                f"✅ Описание успешно обновлено!",
                reply_markup=get_edit_profile_keyboard()
            )
        else:
            await message.answer(
                "❌ Произошла ошибка при обновлении описания. Попробуйте еще раз.",
                reply_markup=get_edit_profile_keyboard()
            )
    else:
        await message.answer(
            "❌ Анкета не найдена.",
            reply_markup=get_edit_profile_keyboard()
        )
    
    await state.clear()

@router.message(F.text == "📷 Изменить фото")
async def edit_photos_start(message: Message, state: FSMContext):
    """Начало изменения фото"""
    await message.answer(
        "📷 <b>Изменение фотографий</b>\n\n"
        "Внимание! При изменении фотографий все старые фото будут удалены.\n\n"
        "Отправьте новые фотографии для анкеты (от 1 до 3 фото):",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    
    # Инициализируем список новых фотографий
    await state.update_data(new_photos=[])
    await state.set_state(EditProfileStates.edit_photos)

@router.message(EditProfileStates.edit_photos, F.photo)
async def edit_photos_process(message: Message, state: FSMContext):
    """Обработка новых фотографий"""
    data = await state.get_data()
    new_photos = data.get('new_photos', [])
    
    if len(new_photos) >= 3:
        await message.answer(
            "Максимум 3 фотографии. Нажмите '✅ Завершить', чтобы сохранить изменения.",
            reply_markup=get_finish_registration_keyboard()
        )
        return
    
    # Получаем самую качественную версию фото
    photo = message.photo[-1]
    
    new_photos.append({
        'file_id': photo.file_id,
        'file_unique_id': photo.file_unique_id
    })
    
    await state.update_data(new_photos=new_photos)
    
    if len(new_photos) == 1:
        await message.answer(
            "✅ Первая фотография добавлена.\n"
            f"Можно добавить еще {2 - len(new_photos)} фото.\n"
            "Или нажмите '✅ Завершить', чтобы сохранить.",
            reply_markup=get_finish_registration_keyboard()
        )
    elif len(new_photos) < 3:
        await message.answer(
            f"✅ Фото добавлено! Можно добавить еще {3 - len(new_photos)}.\n"
            "Или нажмите '✅ Завершить', чтобы сохранить.",
            reply_markup=get_finish_registration_keyboard()
        )
    else:
        await message.answer(
            "✅ Максимальное количество фото достигнуто! Нажмите '✅ Завершить'.",
            reply_markup=get_finish_registration_keyboard()
        )

@router.message(EditProfileStates.edit_photos, F.text == "✅ Завершить")
async def edit_photos_finish(message: Message, state: FSMContext):
    """Завершение изменения фотографий"""
    data = await state.get_data()
    new_photos = data.get('new_photos', [])
    
    if len(new_photos) == 0:
        await message.answer(
            "Нужно добавить хотя бы одну фотографию!",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    user_id = db.get_user_id_by_telegram_id(message.from_user.id)
    profile = db.get_user_profile_by_user_id(user_id)
    
    if profile:
        # Удаляем старые фото
        db.delete_profile_photos(profile['id'])
        
        # Добавляем новые фото
        success_count = 0
        for i, photo in enumerate(new_photos):
            success = db.add_photo(
                profile['id'], 
                photo['file_id'], 
                photo['file_unique_id'], 
                i
            )
            if success:
                success_count += 1
        
        if success_count == len(new_photos):
            await message.answer(
                f"✅ Фотографии успешно обновлены!\n"
                f"Добавлено фото: {success_count}",
                reply_markup=get_edit_profile_keyboard()
            )
        else:
            await message.answer(
                f"⚠️ Добавлено {success_count} из {len(new_photos)} фото.\n"
                f"Возникли проблемы с некоторыми фотографиями.",
                reply_markup=get_edit_profile_keyboard()
            )
    else:
        await message.answer(
            "❌ Анкета не найдена.",
            reply_markup=get_edit_profile_keyboard()
        )
    
    await state.clear()

@router.message(EditProfileStates.edit_photos, F.text == "❌ Отмена")
async def edit_photos_cancel(message: Message, state: FSMContext):
    """Отмена изменения фотографий"""
    await state.clear()
    await message.answer(
        "Изменение фотографий отменено.",
        reply_markup=get_edit_profile_keyboard()
    )

@router.message(F.text == "🗑️ Удалить анкету")
async def delete_profile_start(message: Message, state: FSMContext):
    """Начало удаления анкеты"""
    await message.answer(
        "⚠️ <b>Внимание!</b>\n\n"
        "Вы уверены, что хотите удалить свою анкету?\n\n"
        "Это действие <b>необратимо</b> и приведет к:\n"
        "• Удалению всех ваших фотографий\n"
        "• Удалению всех лайков и просмотров\n"
        "• Потере всех мэтчей\n\n"
        "Для подтверждения введите: <code>ДА, УДАЛИТЬ АНКЕТУ</code>\n"
        "Для отмены нажмите кнопку ниже.",
        parse_mode="HTML",
        reply_markup=get_back_to_profile_keyboard()
    )
    await state.set_state(EditProfileStates.confirm_delete)

@router.message(EditProfileStates.confirm_delete)
async def delete_profile_confirm(message: Message, state: FSMContext):
    """Подтверждение удаления анкеты"""
    if message.text == "ДА, УДАЛИТЬ АНКЕТУ":
        user_id = db.get_user_id_by_telegram_id(message.from_user.id)
        
        if user_id:
            success = db.delete_profile(user_id)
            
            if success:
                await message.answer(
                    "✅ Ваша анкета успешно удалена.\n\n"
                    "Вы можете создать новую анкету через команду /start",
                    reply_markup=get_main_menu_keyboard()
                )
            else:
                await message.answer(
                    "❌ Произошла ошибка при удалении анкеты. Попробуйте позже.",
                    reply_markup=get_profile_menu_keyboard()
                )
        else:
            await message.answer(
                "❌ Пользователь не найден.",
                reply_markup=get_main_menu_keyboard()
            )
    else:
        await message.answer(
            "Удаление анкеты отменено.",
            reply_markup=get_profile_menu_keyboard()
        )
    
    await state.clear()

@router.message(F.text == "🔙 Назад к анкете")
async def back_to_profile_menu(message: Message, state: FSMContext):
    """Возврат к меню анкеты"""
    await state.clear()
    await my_profile_menu(message, state)

@router.message(F.text == "🔙 Назад в меню")
async def back_to_main_menu_from_profile(message: Message, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    await message.answer(
        "Возвращаюсь в главное меню:",
        reply_markup=get_main_menu_keyboard()
    )

@router.message(F.text == "🏠 Главное меню")
async def back_to_main_menu(message: Message, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    await message.answer(
        "Возвращаюсь в главное меню:",
        reply_markup=get_main_menu_keyboard()
    )

@router.message(Command("profile"))
async def profile_command(message: Message, state: FSMContext):
    """Обработчик команды /profile"""
    # Просто перенаправляем на обработчик "Моя анкета"
    from handlers.profile_management import my_profile_menu
    await my_profile_menu(message, state)