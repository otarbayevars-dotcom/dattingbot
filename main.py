import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import os
from dotenv import load_dotenv
from models import Database

from handlers import profile_creation, profile_view, premium, profile_management, admin
import utils

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Токен бота из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не найден в переменных окружения")
    exit(1)

async def on_startup(bot: Bot):
    """Действия при запуске бота"""
    logger.info("🚀 Бот запущен")
    
    # Инициализируем систему автолайков
    try:
        from handlers.admin import init_auto_like_system, auto_like_system
        if auto_like_system:
            await auto_like_system.start_auto_likes()
            logger.info("🤖 Система автолайков запущена")
    except Exception as e:
        logger.error(f"⚠️ Ошибка запуска системы автолайков: {e}")
    
    # Устанавливаем команды бота
    commands = [
        {
            "command": "start",
            "description": "🚀 Запустить бота / создать анкету"
        },
        {
            "command": "help",
            "description": "❓ Помощь по использованию бота"
        },
        {
            "command": "premium",
            "description": "⭐ Информация о премиум подписке"
        },
        {
            "command": "referral",
            "description": "👥 Реферальная программа"
        },
        {
            "command": "stats",
            "description": "📊 Ваша статистика"
        },
        {
            "command": "profile",
            "description": "👤 Моя анкета"
        },
        {
            "command": "admin",
            "description": "🔐 Админ-панель (только для админов)"
        },
        {
            "command": "likes",
            "description": "💌 Мои уведомления"
        },
        {
            "command": "next",
            "description": "➡️ Следующая анкета"
        }
    ]
    
    await bot.set_my_commands(commands)
    
    # Отправляем сообщение админу
    try:
        admin_id = os.getenv("ADMIN_ID")
        if admin_id:
            await bot.send_message(admin_id, "🤖 Бот для знакомств успешно запущен! 🚀")
    except:
        pass

async def on_shutdown(bot: Bot):
    """Действия при остановке бота"""
    logger.info("🛑 Бот остановлен")
    
    # Останавливаем систему автолайков
    try:
        from handlers.admin import auto_like_system
        if auto_like_system:
            await auto_like_system.stop_auto_likes()
            logger.info("🤖 Система автолайков остановлена")
    except Exception as e:
        logger.error(f"⚠️ Ошибка остановки системы автолайков: {e}")
    
    from models import Database
    db = Database()
    db.close()

async def main():
    """Основная функция запуска бота"""
    
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Инициализация системы автолайков
    from handlers.admin import init_auto_like_system
    init_auto_like_system(Database(), bot)
    
    # Регистрация роутеров
    dp.include_router(profile_creation.router)
    dp.include_router(profile_view.router)
    dp.include_router(premium.router)
    dp.include_router(profile_management.router)
    dp.include_router(admin.router)
    
    # Регистрация обработчиков событий
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Запуск бота
    try:
        logger.info("🔄 Запуск polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"💥 Критическая ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())