import sqlite3
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
import math
import secrets
import string

class Database:
    def __init__(self, db_name: str = 'dating_bot.db'):
        self.connection = sqlite3.connect(db_name, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        self.create_tables()
    
    def create_tables(self):
        """Создание таблиц базы данных"""
        
        # Таблица пользователей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица анкет
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                gender TEXT NOT NULL,
                looking_for TEXT NOT NULL,
                city TEXT NOT NULL,
                about TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Таблица интересов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS interests (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS profile_interests (
                profile_id INTEGER NOT NULL,
                interest_id INTEGER NOT NULL,
                FOREIGN KEY (profile_id) REFERENCES profiles (id),
                FOREIGN KEY (interest_id) REFERENCES interests (id),
                PRIMARY KEY (profile_id, interest_id)
            )
        ''')
        
        # Таблица фотографий
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY,
                profile_id INTEGER NOT NULL,
                file_id TEXT NOT NULL,
                file_unique_id TEXT NOT NULL,
                position INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES profiles (id)
            )
        ''')
        
        # Таблица лайков
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY,
                from_user_id INTEGER NOT NULL,
                to_profile_id INTEGER NOT NULL,
                like_type TEXT NOT NULL,
                is_mutual BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_user_id) REFERENCES users (id),
                FOREIGN KEY (to_profile_id) REFERENCES profiles (id),
                UNIQUE(from_user_id, to_profile_id)
            )
        ''')
        
        # Таблица просмотренных анкет
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS views (
                id INTEGER PRIMARY KEY,
                viewer_id INTEGER NOT NULL,
                viewed_profile_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (viewer_id) REFERENCES users (id),
                FOREIGN KEY (viewed_profile_id) REFERENCES profiles (id),
                UNIQUE(viewer_id, viewed_profile_id)
            )
        ''')
        
        # Таблица премиум подписок
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS premium_subscriptions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                plan_type TEXT NOT NULL,
                stars_amount INTEGER DEFAULT 0,
                starts_at TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                payment_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Таблица рефералов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                is_completed BOOLEAN DEFAULT 0,
                reward_claimed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users (id),
                FOREIGN KEY (referred_id) REFERENCES users (id),
                UNIQUE(referred_id)
            )
        ''')
        
        # Таблица реферальных кодов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_codes (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                code TEXT UNIQUE NOT NULL,
                uses INTEGER DEFAULT 0,
                max_uses INTEGER DEFAULT 10,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Таблица бот-анкет
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_profiles (
                id INTEGER PRIMARY KEY,
                profile_id INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                auto_like_interval INTEGER DEFAULT 600,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES profiles (id)
            )
        ''')
        
        # Таблица аффилиатов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS affiliates (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                commission_rate INTEGER DEFAULT 10,
                total_earnings INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Таблица выплат аффилиатам
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS affiliate_payouts (
                id INTEGER PRIMARY KEY,
                affiliate_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (affiliate_id) REFERENCES affiliates (id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY,
                reporter_id INTEGER NOT NULL,
                reported_profile_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                status TEXT DEFAULT 'pending', -- pending, reviewed, closed
                admin_notes TEXT,
                action_taken TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TIMESTAMP,
                FOREIGN KEY (reported_profile_id) REFERENCES profiles (id)
            )
        ''')

        # Таблица администраторов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                role TEXT DEFAULT 'moderator',
                permissions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Таблица рассылок
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS broadcasts (
                id INTEGER PRIMARY KEY,
                admin_id INTEGER NOT NULL,
                message_text TEXT NOT NULL,
                sent_count INTEGER DEFAULT 0,
                total_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                scheduled_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES admins (id)
            )
        ''')
        
        # Таблица платежей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS star_payments (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                stars_amount INTEGER NOT NULL,
                product_type TEXT NOT NULL,
                product_duration INTEGER,
                invoice_payload TEXT,
                telegram_payment_charge_id TEXT,
                provider_payment_charge_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Вставляем предопределенные интересы
        default_interests = [
            'Интим', 'Отношения', 'Дружба', 'Игры',
            'Без обязательств', 'Прогулки', 'Кино', 'Спорт',
            'Путешествия', 'Музыка', 'Искусство', 'Кулинария',
            'Наука', 'Технологии', 'Чтение', 'Фотография'
        ]
        
        for interest in default_interests:
            self.cursor.execute(
                "INSERT OR IGNORE INTO interests (name) VALUES (?)",
                (interest,)
            )
        
        self.connection.commit()
    
    def update_profile(self, profile_id: int, field: str, value: str) -> bool:
        """Обновление поля анкеты"""
        try:
            allowed_fields = ['name', 'age', 'gender', 'looking_for', 'city', 'about']
            if field not in allowed_fields:
                return False
            
            # Используем параметризованный запрос для безопасности
            query = f"UPDATE profiles SET {field} = ?, updated_at = ? WHERE id = ?"
            self.cursor.execute(query, (value, datetime.now().timestamp(), profile_id))
            
            self.connection.commit()
            return True
        except Exception as e:
            print(f"❌ Ошибка обновления анкеты: {e}")
            return False
    
    def update_profile_interests(self, profile_id: int, interests: list) -> bool:
        """Обновление интересов анкеты"""
        try:
            # Удаляем старые интересы
            self.cursor.execute(
                "DELETE FROM profile_interests WHERE profile_id = ?",
                (profile_id,)
            )
            
            # Добавляем новые интересы
            for interest_name in interests:
                self.cursor.execute(
                    "SELECT id FROM interests WHERE name = ?",
                    (interest_name,)
                )
                interest = self.cursor.fetchone()
                if interest:
                    self.cursor.execute(
                        "INSERT INTO profile_interests (profile_id, interest_id) VALUES (?, ?)",
                        (profile_id, interest['id'])
                    )
            
            self.connection.commit()
            return True
        except Exception as e:
            print(f"❌ Ошибка обновления интересов: {e}")
            return False
    
    def delete_profile_photos(self, profile_id: int) -> bool:
        """Удаление всех фото анкеты"""
        try:
            self.cursor.execute(
                "DELETE FROM photos WHERE profile_id = ?",
                (profile_id,)
            )
            self.connection.commit()
            return True
        except Exception as e:
            print(f"❌ Ошибка удаления фото: {e}")
            return False
    
    def delete_profile(self, user_id: int) -> bool:
        """Удаление анкеты пользователя"""
        try:
            # Получаем profile_id
            self.cursor.execute(
                "SELECT id FROM profiles WHERE user_id = ?",
                (user_id,)
            )
            profile = self.cursor.fetchone()
            
            if not profile:
                return False
            
            profile_id = profile['id']
            
            # Удаляем связанные данные
            self.cursor.execute("DELETE FROM profile_interests WHERE profile_id = ?", (profile_id,))
            self.cursor.execute("DELETE FROM photos WHERE profile_id = ?", (profile_id,))
            self.cursor.execute("DELETE FROM likes WHERE to_profile_id = ?", (profile_id,))
            self.cursor.execute("DELETE FROM views WHERE viewed_profile_id = ?", (profile_id,))
            self.cursor.execute("DELETE FROM bot_profiles WHERE profile_id = ?", (profile_id,))
            
            # Удаляем анкету
            self.cursor.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
            
            self.connection.commit()
            return True
        except Exception as e:
            print(f"❌ Ошибка удаления анкеты: {e}")
            return False
    
    def is_profile_exists(self, user_id: int) -> bool:
        """Проверка существования анкеты"""
        self.cursor.execute(
            "SELECT id FROM profiles WHERE user_id = ?",
            (user_id,)
        )
        return self.cursor.fetchone() is not None
    
    # ========== МЕТОДЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ==========
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[dict]:

        self.cursor.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        result = self.cursor.fetchone()
        return dict(result) if result else None

    def add_user(self, telegram_id: int, username: str = None) -> Optional[int]:
        """Добавление нового пользователя"""
        try:
            self.cursor.execute(
                "INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)",
                (telegram_id, username)
            )
            self.connection.commit()
            
            # Получаем ID созданного пользователя
            self.cursor.execute(
                "SELECT id FROM users WHERE telegram_id = ?",
                (telegram_id,)
            )
            result = self.cursor.fetchone()
            return result['id'] if result else None
        except Exception as e:
            print(f"❌ Ошибка добавления пользователя: {e}")
            return None
    
    def get_user_id_by_telegram_id(self, telegram_id: int) -> Optional[int]:
        """Получение user_id по telegram_id"""
        self.cursor.execute(
            "SELECT id FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        result = self.cursor.fetchone()
        return result['id'] if result else None
    
    def get_telegram_id_by_user_id(self, user_id: int) -> Optional[int]:
        """Получение telegram_id по user_id"""
        self.cursor.execute(
            "SELECT telegram_id FROM users WHERE id = ?",
            (user_id,)
        )
        result = self.cursor.fetchone()
        return result['telegram_id'] if result else None
    
    # ========== МЕТОДЫ ДЛЯ АНКЕТ ==========
    
    def create_profile(self, user_id: int, data: dict) -> Optional[int]:

        try:
            print(f"DEBUG: Создание анкеты для user_id={user_id}")
            
            self.cursor.execute('''
                INSERT INTO profiles 
                (user_id, name, age, gender, looking_for, city, about)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                data.get('name'),
                data.get('age'),
                data.get('gender'),
                data.get('looking_for'),
                data.get('city'),
                data.get('about', '')
            ))
            
            profile_id = self.cursor.lastrowid
            print(f"DEBUG: Создана анкета с ID={profile_id}")
            
            # Добавляем интересы
            if 'interests' in data:
                print(f"DEBUG: Добавление интересов: {data['interests']}")
                for interest_name in data['interests']:
                    self.cursor.execute(
                        "SELECT id FROM interests WHERE name = ?",
                        (interest_name,)
                    )
                    interest = self.cursor.fetchone()
                    if interest:
                        self.cursor.execute(
                            "INSERT INTO profile_interests (profile_id, interest_id) VALUES (?, ?)",
                            (profile_id, interest['id'])
                        )
            
            self.connection.commit()
            
            # Помечаем реферала как выполнившего условие
            print(f"DEBUG: Помечаем реферала как выполнившего условие: {user_id}")
            self.mark_referral_completed(user_id)
            
            return profile_id
        except Exception as e:
            print(f"❌ Ошибка создания анкеты: {e}")
            return None
    
    def add_photo(self, profile_id: int, file_id: str, file_unique_id: str, position: int = 0) -> bool:
        """Добавление фото к анкете"""
        try:
            self.cursor.execute('''
                INSERT INTO photos (profile_id, file_id, file_unique_id, position)
                VALUES (?, ?, ?, ?)
            ''', (profile_id, file_id, file_unique_id, position))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"❌ Ошибка добавления фото: {e}")
            return False
    
    def get_user_matches(self, user_id: int) -> List[Dict]:
        """Получение мэтчей пользователя"""
        try:
            # Получаем профиль пользователя
            user_profile = self.get_user_profile_by_user_id(user_id)
            if not user_profile:
                return []
            
            # Находим взаимные лайки
            self.cursor.execute('''
                SELECT DISTINCT p.*
                FROM profiles p
                JOIN likes l1 ON l1.to_profile_id = p.id
                JOIN likes l2 ON l2.to_profile_id = ?
                WHERE l1.from_user_id = ?
                AND l2.from_user_id = p.user_id
                AND l1.like_type = 'like'
                AND l2.like_type = 'like'
                AND l1.is_mutual = 1
                AND p.is_active = 1
            ''', (user_profile['id'], user_id))
            
            matches = []
            for row in self.cursor.fetchall():
                self.cursor.execute(
                    "SELECT file_id FROM photos WHERE profile_id = ? ORDER BY position",
                    (row['id'],)
                )
                photos = [photo['file_id'] for photo in self.cursor.fetchall()]
                
                # Получаем интересы
                self.cursor.execute('''
                    SELECT i.name FROM interests i
                    JOIN profile_interests pi ON i.id = pi.interest_id
                    WHERE pi.profile_id = ?
                ''', (row['id'],))
                
                interests = [interest['name'] for interest in self.cursor.fetchall()]
                
                matches.append({
                    'id': row['id'],
                    'name': row['name'],
                    'age': row['age'],
                    'gender': row['gender'],
                    'looking_for': row['looking_for'],
                    'city': row['city'],
                    'about': row['about'],
                    'interests': interests,
                    'photos': photos
                })
            
            return matches
        except Exception as e:
            print(f"❌ Ошибка получения мэтчей: {e}")
            return []
    
    def get_user_profile(self, telegram_id: int) -> Optional[dict]:
        """Получение анкеты пользователя по telegram_id"""
        self.cursor.execute('''
            SELECT p.* 
            FROM profiles p
            WHERE p.user_id = (SELECT id FROM users WHERE telegram_id = ?)
        ''', (telegram_id,))
        
        profile = self.cursor.fetchone()
        if profile:
            # Получаем фото
            self.cursor.execute(
                "SELECT file_id FROM photos WHERE profile_id = ? ORDER BY position",
                (profile['id'],)
            )
            photos = [row['file_id'] for row in self.cursor.fetchall()]
            
            # Получаем интересы
            self.cursor.execute('''
                SELECT i.name FROM interests i
                JOIN profile_interests pi ON i.id = pi.interest_id
                WHERE pi.profile_id = ?
            ''', (profile['id'],))
            
            interests = [row['name'] for row in self.cursor.fetchall()]
            
            return {
                'id': profile['id'],
                'user_id': profile['user_id'],
                'name': profile['name'],
                'age': profile['age'],
                'gender': profile['gender'],
                'looking_for': profile['looking_for'],
                'city': profile['city'],
                'about': profile['about'],
                'is_active': bool(profile['is_active']),
                'interests': interests,
                'photos': photos
            }
        return None
    
    def get_user_profile_by_user_id(self, user_id: int) -> Optional[dict]:
        """Получение анкеты пользователя по user_id"""
        self.cursor.execute('''
            SELECT p.* 
            FROM profiles p
            WHERE p.user_id = ?
        ''', (user_id,))
        
        profile = self.cursor.fetchone()
        if profile:
            # Получаем фото
            self.cursor.execute(
                "SELECT file_id FROM photos WHERE profile_id = ? ORDER BY position",
                (profile['id'],)
            )
            photos = [row['file_id'] for row in self.cursor.fetchall()]
            
            # Получаем интересы
            self.cursor.execute('''
                SELECT i.name FROM interests i
                JOIN profile_interests pi ON i.id = pi.interest_id
                WHERE pi.profile_id = ?
            ''', (profile['id'],))
            
            interests = [row['name'] for row in self.cursor.fetchall()]
            
            return {
                'id': profile['id'],
                'user_id': profile['user_id'],
                'name': profile['name'],
                'age': profile['age'],
                'gender': profile['gender'],
                'looking_for': profile['looking_for'],
                'city': profile['city'],
                'about': profile['about'],
                'is_active': bool(profile['is_active']),
                'interests': interests,
                'photos': photos
            }
        return None
    
    def get_profile_by_id(self, profile_id: int) -> Optional[dict]:
        """Получение анкеты по ID"""
        self.cursor.execute('''
            SELECT p.* 
            FROM profiles p
            WHERE p.id = ?
        ''', (profile_id,))
        
        profile = self.cursor.fetchone()
        if profile:
            # Получаем фото
            self.cursor.execute(
                "SELECT file_id FROM photos WHERE profile_id = ? ORDER BY position",
                (profile['id'],)
            )
            photos = [row['file_id'] for row in self.cursor.fetchall()]
            
            # Получаем интересы
            self.cursor.execute('''
                SELECT i.name FROM interests i
                JOIN profile_interests pi ON i.id = pi.interest_id
                WHERE pi.profile_id = ?
            ''', (profile['id'],))
            
            interests = [row['name'] for row in self.cursor.fetchall()]
            
            return {
                'id': profile['id'],
                'user_id': profile['user_id'],
                'name': profile['name'],
                'age': profile['age'],
                'gender': profile['gender'],
                'looking_for': profile['looking_for'],
                'city': profile['city'],
                'about': profile['about'],
                'is_active': bool(profile['is_active']),
                'interests': interests,
                'photos': photos
            }
        return None
    
    def get_profile_count(self) -> int:
        """Получение количества анкет"""
        self.cursor.execute("SELECT COUNT(*) FROM profiles WHERE is_active = 1")
        result = self.cursor.fetchone()
        return result[0] if result else 0
    
    # ========== МЕТОДЫ ДЛЯ ПОИСКА АНКЕТ ==========
    
    def get_next_profile(self, user_id: int, filters: dict = None) -> Optional[dict]:
        """Умный поиск следующей анкеты для просмотра"""
        try:
            # Получаем анкету текущего пользователя
            user_profile = self.get_user_profile_by_user_id(user_id)
            if not user_profile:
                return None
            
            looking_for = user_profile['looking_for']
            user_gender = user_profile['gender']
            
            # Определяем какой пол ищем
            gender_filter = self._get_gender_filter(looking_for, user_gender)
            
            # Базовый запрос
            query = '''
                SELECT DISTINCT p.*
                FROM profiles p
                WHERE p.user_id != ?
                AND p.is_active = 1
                AND p.gender IN ({})
                AND p.looking_for IN ({})
                AND NOT EXISTS (
                    SELECT 1 FROM views v 
                    WHERE v.viewer_id = ? AND v.viewed_profile_id = p.id
                )
                AND NOT EXISTS (
                    SELECT 1 FROM likes l 
                    WHERE l.from_user_id = ? AND l.to_profile_id = p.id
                )
            '''.format(
                ','.join(['?' for _ in gender_filter['target_genders']]),
                ','.join(['?' for _ in gender_filter['looking_for_genders']])
            )
            
            params = [user_id, *gender_filter['target_genders'], 
                     *gender_filter['looking_for_genders'], user_id, user_id]
            
            # Добавляем фильтр по городу
            query += " AND p.city = ?"
            params.append(user_profile['city'])
            
            # Добавляем фильтр по возрасту (+- 5 лет)
            query += " AND p.age BETWEEN ? AND ?"
            age_min = max(18, user_profile['age'] - 5)
            age_max = user_profile['age'] + 5
            params.extend([age_min, age_max])
            
            query += " ORDER BY RANDOM() LIMIT 1"
            
            self.cursor.execute(query, params)
            result = self.cursor.fetchone()
            
            if result:
                return self._format_profile_result(result)
            
            # Если не нашли, ищем без фильтра по городу
            query = '''
                SELECT DISTINCT p.*
                FROM profiles p
                WHERE p.user_id != ?
                AND p.is_active = 1
                AND p.gender IN ({})
                AND p.looking_for IN ({})
                AND NOT EXISTS (
                    SELECT 1 FROM views v 
                    WHERE v.viewer_id = ? AND v.viewed_profile_id = p.id
                )
                AND NOT EXISTS (
                    SELECT 1 FROM likes l 
                    WHERE l.from_user_id = ? AND l.to_profile_id = p.id
                )
                AND p.age BETWEEN ? AND ?
                ORDER BY RANDOM() LIMIT 1
            '''.format(
                ','.join(['?' for _ in gender_filter['target_genders']]),
                ','.join(['?' for _ in gender_filter['looking_for_genders']])
            )
            
            params = [user_id, *gender_filter['target_genders'], 
                     *gender_filter['looking_for_genders'], user_id, user_id,
                     age_min, age_max]
            
            self.cursor.execute(query, params)
            result = self.cursor.fetchone()
            
            if result:
                return self._format_profile_result(result)
            
            return None
            
        except Exception as e:
            print(f"❌ Ошибка поиска следующей анкеты: {e}")
            return None
    
    def _get_gender_filter(self, looking_for: str, user_gender: str) -> dict:
        """Определение фильтров по полу"""
        looking_for_map = {
            "Парня": ["Мужчина"],
            "Девушку": ["Женщина"],
            "Оба": ["Мужчина", "Женщина", "Другой"]
        }
        
        target_genders = looking_for_map.get(looking_for, ["Мужчина", "Женщина", "Другой"])
        
        # Пол, который должен искать анкета
        looking_for_genders = []
        if user_gender == "Мужчина":
            looking_for_genders = ["Парня"]
        elif user_gender == "Женщина":
            looking_for_genders = ["Девушку"]
        else:
            looking_for_genders = ["Парня", "Девушку", "Оба"]
        
        return {
            'target_genders': target_genders,
            'looking_for_genders': looking_for_genders
        }
    
    def _format_profile_result(self, result) -> dict:
        """Форматирование результата запроса профиля"""
        profile_id = result['id']
        
        # Получаем фото
        self.cursor.execute(
            "SELECT file_id FROM photos WHERE profile_id = ? ORDER BY position",
            (profile_id,)
        )
        photos = [row['file_id'] for row in self.cursor.fetchall()]
        
        # Получаем интересы
        self.cursor.execute('''
            SELECT i.name FROM interests i
            JOIN profile_interests pi ON i.id = pi.interest_id
            WHERE pi.profile_id = ?
        ''', (profile_id,))
        
        interests = [row['name'] for row in self.cursor.fetchall()]
        
        return {
            'id': result['id'],
            'user_id': result['user_id'],
            'name': result['name'],
            'age': result['age'],
            'gender': result['gender'],
            'looking_for': result['looking_for'],
            'city': result['city'],
            'about': result['about'],
            'is_active': bool(result['is_active']),
            'interests': interests,
            'photos': photos
        }
    
    # ========== МЕТОДЫ ДЛЯ ЛАЙКОВ И ПРОСМОТРОВ ==========
    
    def add_view(self, viewer_id: int, profile_id: int) -> bool:
        """Добавление записи о просмотре анкеты"""
        try:
            self.cursor.execute(
                "INSERT OR IGNORE INTO views (viewer_id, viewed_profile_id) VALUES (?, ?)",
                (viewer_id, profile_id)
            )
            self.connection.commit()
            return True
        except Exception as e:
            print(f"❌ Ошибка добавления просмотра: {e}")
            return False
    
    def add_like(self, from_user_id: int, to_profile_id: int, like_type: str = 'like') -> dict:
        """Добавление лайка/дизлайка"""
        try:
            # Проверяем взаимность
            self.cursor.execute('''
                SELECT 1 FROM likes 
                WHERE from_user_id = (
                    SELECT user_id FROM profiles WHERE id = ?
                ) AND to_profile_id = (
                    SELECT id FROM profiles WHERE user_id = ?
                ) AND like_type = 'like'
            ''', (to_profile_id, from_user_id))
            
            is_mutual = self.cursor.fetchone() is not None
            
            # Добавляем лайк
            self.cursor.execute('''
                INSERT OR REPLACE INTO likes (from_user_id, to_profile_id, like_type, is_mutual)
                VALUES (?, ?, ?, ?)
            ''', (from_user_id, to_profile_id, like_type, is_mutual))
            
            # Если это взаимный лайк, обновляем существующую запись
            if like_type == 'like' and is_mutual:
                self.cursor.execute('''
                    UPDATE likes SET is_mutual = 1 
                    WHERE from_user_id = (
                        SELECT user_id FROM profiles WHERE id = ?
                    ) AND to_profile_id = (
                        SELECT id FROM profiles WHERE user_id = ?
                    )
                ''', (to_profile_id, from_user_id))
            
            self.connection.commit()
            
            return {'success': True, 'is_mutual': is_mutual, 'like_id': self.cursor.lastrowid}
            
        except Exception as e:
            print(f"❌ Ошибка добавления лайка: {e}")
            return {'success': False, 'is_mutual': False, 'like_id': None}
    
    def get_pending_likes(self, profile_id: int) -> list:

        try:
            print(f"DEBUG: Поиск лайков для profile_id={profile_id}")
            
            # Сначала удаляем старые лайки от ботов
            self.cursor.execute('''
                DELETE FROM likes 
                WHERE to_profile_id = ?
                AND from_user_id IN (
                    SELECT p.user_id 
                    FROM profiles p
                    JOIN bot_profiles bp ON p.id = bp.profile_id
                )
                AND (is_mutual = 0 OR like_type = 'like')
            ''', (profile_id,))
            
            if self.cursor.rowcount > 0:
                print(f"DEBUG: Удалено {self.cursor.rowcount} старых лайков от ботов")
            
            self.connection.commit()
            
            # Теперь получаем только лайки от реальных пользователей
            self.cursor.execute('''
                SELECT l.id, u.telegram_id, p.name, p.age, p.city
                FROM likes l
                JOIN users u ON u.id = l.from_user_id
                JOIN profiles p ON p.user_id = l.from_user_id
                WHERE l.to_profile_id = ?
                AND l.like_type = 'like'
                AND l.is_mutual = 0
                AND NOT EXISTS (
                    SELECT 1 FROM likes l2 
                    WHERE l2.from_user_id = (
                        SELECT user_id FROM profiles WHERE id = ?
                    )
                    AND l2.to_profile_id = p.id
                    AND l2.like_type IN ('like', 'dislike')
                )
                AND NOT EXISTS (
                    SELECT 1 FROM bot_profiles bp 
                    WHERE bp.profile_id = p.id
                )
            ''', (profile_id, profile_id))
            
            results = self.cursor.fetchall()
            print(f"DEBUG: Найдено {len(results)} лайков от реальных пользователей")
            
            # Преобразуем в список словарей для удобства
            likes_list = []
            for row in results:
                likes_list.append({
                    'like_id': row[0],  # id
                    'telegram_id': row[1],  # telegram_id
                    'name': row[2],  # name
                    'age': row[3],  # age
                    'city': row[4]   # city
                })
                print(f"DEBUG: Лайк от {row[2]}, telegram_id={row[1]}")
            
            return likes_list
        except Exception as e:
            print(f"❌ Ошибка получения лайков: {e}")
            return []
    
    def mark_like_responded(self, like_id: int, response: str) -> bool:

        try:
            print(f"DEBUG: mark_like_responded: like_id={like_id}, response={response}")
            
            # Если это отказ, то полностью удаляем запись, чтобы больше не показывать
            if response == 'dislike':
                self.cursor.execute(
                    "DELETE FROM likes WHERE id = ?",
                    (like_id,)
                )
                print(f"DEBUG: Лайк {like_id} удален (dislike)")
            else:
                self.cursor.execute(
                    "UPDATE likes SET like_type = ? WHERE id = ?",
                    (response, like_id)
                )
                print(f"DEBUG: Лайк {like_id} обновлен на {response}")
            
            self.connection.commit()
            return True
        except Exception as e:
            print(f"❌ Ошибка отметки лайка: {e}")
            return False
    
    def get_telegram_id_by_profile_id(self, profile_id: int) -> Optional[int]:
        """Получение telegram_id по profile_id"""
        try:
            self.cursor.execute('''
                SELECT u.telegram_id 
                FROM users u
                JOIN profiles p ON p.user_id = u.id
                WHERE p.id = ?
            ''', (profile_id,))
            
            result = self.cursor.fetchone()
            return result['telegram_id'] if result else None
        except Exception as e:
            print(f"❌ Ошибка получения telegram_id: {e}")
            return None
    
    # ========== МЕТОДЫ ДЛЯ ПРЕМИУМ СИСТЕМЫ ==========
    
    def get_user_premium_status(self, user_id: int) -> Optional[dict]:
        """Получение статуса премиум подписки пользователя"""
        try:
            self.cursor.execute('''
                SELECT * FROM premium_subscriptions 
                WHERE user_id = ? AND is_active = 1 AND expires_at > ?
                ORDER BY expires_at DESC
                LIMIT 1
            ''', (user_id, datetime.now().timestamp()))
            
            subscription = self.cursor.fetchone()
            
            if subscription:
                return {
                    'id': subscription['id'],
                    'user_id': subscription['user_id'],
                    'plan_type': subscription['plan_type'],
                    'stars_amount': subscription['stars_amount'],
                    'starts_at': subscription['starts_at'],
                    'expires_at': subscription['expires_at'],
                    'is_active': bool(subscription['is_active']),
                    'payment_id': subscription['payment_id']
                }
            return None
        except Exception as e:
            print(f"❌ Ошибка получения статуса премиума: {e}")
            return None
    
    def has_active_premium(self, user_id: int) -> bool:
        """Проверка наличия активной премиум подписки"""
        subscription = self.get_user_premium_status(user_id)
        return subscription is not None
    
    def create_premium_subscription(self, user_id: int, plan_type: str, 
                                   duration_days: int, stars_amount: int = 0,
                                   payment_id: str = None) -> Optional[int]:
        """Создание премиум подписки"""
        try:
            starts_at = datetime.now().timestamp()
            expires_at = starts_at + (duration_days * 86400)
            
            self.cursor.execute('''
                INSERT INTO premium_subscriptions 
                (user_id, plan_type, stars_amount, starts_at, expires_at, payment_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, plan_type, stars_amount, starts_at, expires_at, payment_id))
            
            subscription_id = self.cursor.lastrowid
            self.connection.commit()
            return subscription_id
        except Exception as e:
            print(f"❌ Ошибка создания премиум подписки: {e}")
            return None
    
    # ========== МЕТОДЫ ДЛЯ РЕФЕРАЛЬНОЙ СИСТЕМЫ ==========
    
    def get_referral_code(self, user_id: int) -> Optional[dict]:
        """Получение реферального кода пользователя"""
        try:
            self.cursor.execute('''
                SELECT code, uses, max_uses FROM referral_codes
                WHERE user_id = ?
            ''', (user_id,))
            
            result = self.cursor.fetchone()
            if result:
                return {
                    'code': result['code'],
                    'uses': result['uses'],
                    'max_uses': result['max_uses']
                }
            return None
        except Exception as e:
            print(f"❌ Ошибка получения реферального кода: {e}")
            return None
    
    def create_referral_code(self, user_id: int, code: str = None) -> str:

        import secrets
        import string
        
        # Проверяем, есть ли уже код
        existing_code = self.get_referral_code(user_id)
        if existing_code:
            return existing_code['code']
        
        # Генерируем новый код если не указан
        if not code:
            alphabet = string.ascii_uppercase + string.digits
            code = ''.join(secrets.choice(alphabet) for _ in range(8))
        
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO referral_codes (user_id, code)
                VALUES (?, ?)
            ''', (user_id, code))
            
            self.connection.commit()
            print(f"DEBUG: Создан реферальный код {code} для пользователя {user_id}")
            return code
        except Exception as e:
            print(f"❌ Ошибка создания реферального кода: {e}")
            # Если ошибка, пытаемся сгенерировать новый код
            return self.create_referral_code(user_id)
    
    def add_referral(self, referrer_id: int, referred_id: int) -> bool:

        try:
            print(f"DEBUG: Добавление реферала: {referrer_id} -> {referred_id}")
            
            # Проверяем, нет ли уже такой записи
            self.cursor.execute('''
                SELECT id FROM referrals WHERE referrer_id = ? AND referred_id = ?
            ''', (referrer_id, referred_id))
            
            if self.cursor.fetchone():
                print(f"DEBUG: Реферал уже существует")
                return False
            
            self.cursor.execute('''
                INSERT INTO referrals (referrer_id, referred_id)
                VALUES (?, ?)
            ''', (referrer_id, referred_id))
            
            print(f"DEBUG: Реферал добавлен в таблицу")
            
            # Увеличиваем счетчик использования кода
            self.cursor.execute('''
                UPDATE referral_codes 
                SET uses = uses + 1 
                WHERE user_id = ?
            ''', (referrer_id,))
            
            print(f"DEBUG: Счетчик кода обновлен")
            
            self.connection.commit()
            print(f"DEBUG: Транзакция закоммичена")
            return True
        except Exception as e:
            print(f"❌ Ошибка добавления реферала: {e}")
            return False
    
    def mark_referral_completed(self, referred_id: int) -> bool:

        try:
            print(f"DEBUG: Отметка реферала как выполнившего условие: {referred_id}")
            
            self.cursor.execute('''
                UPDATE referrals 
                SET is_completed = 1 
                WHERE referred_id = ?
            ''', (referred_id,))
            
            affected_rows = self.cursor.rowcount
            self.connection.commit()
            
            print(f"DEBUG: Обновлено строк: {affected_rows}")
            
            if affected_rows > 0:
                # Проверяем, достиг ли реферер 10 выполненных рефералов
                self.cursor.execute('''
                    SELECT COUNT(*) as completed_count
                    FROM referrals 
                    WHERE referrer_id = (
                        SELECT referrer_id FROM referrals WHERE referred_id = ? LIMIT 1
                    ) AND is_completed = 1
                ''', (referred_id,))
                
                result = self.cursor.fetchone()
                completed_count = result['completed_count'] if result else 0
                
                print(f"DEBUG: Выполненных рефералов у реферера: {completed_count}")
                
                if completed_count >= 10:
                    # Автоматически выдаем награду
                    referrer_id_result = self.cursor.execute(
                        "SELECT referrer_id FROM referrals WHERE referred_id = ? LIMIT 1",
                        (referred_id,)
                    ).fetchone()
                    
                    if referrer_id_result:
                        referrer_id = referrer_id_result['referrer_id']
                        print(f"DEBUG: Реферер достиг 10 рефералов: {referrer_id}")
                        
                        # Проверяем, не получал ли уже награду
                        self.cursor.execute('''
                            SELECT reward_claimed FROM referrals 
                            WHERE referrer_id = ? AND is_completed = 1 
                            LIMIT 1
                        ''', (referrer_id,))
                        
                        reward_check = self.cursor.fetchone()
                        if reward_check and not reward_check['reward_claimed']:
                            print(f"DEBUG: Выдаем награду рефереру {referrer_id}")
                            self.claim_referral_reward(referrer_id)
            
            return True
        except Exception as e:
            print(f"❌ Ошибка отметки реферала: {e}")
            return False
    
    def get_referral_stats(self, user_id: int) -> dict:
        """Получение статистики по рефералам"""
        try:
            self.cursor.execute('''
                SELECT 
                    COUNT(*) as total_referrals,
                    SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as completed_referrals
                FROM referrals 
                WHERE referrer_id = ?
            ''', (user_id,))
            
            result = self.cursor.fetchone()
            return {
                'total': result['total_referrals'] if result and result['total_referrals'] else 0,
                'completed': result['completed_referrals'] if result and result['completed_referrals'] else 0
            }
        except Exception as e:
            print(f"❌ Ошибка получения статистики рефералов: {e}")
            return {'total': 0, 'completed': 0}
    
    def claim_referral_reward(self, user_id: int) -> bool:
        """Получение награды за рефералов"""
        try:
            stats = self.get_referral_stats(user_id)
            
            if stats['completed'] >= 10:
                subscription_id = self.create_premium_subscription(
                    user_id, 'referral', 1, 0, 'referral_reward'
                )
                
                if subscription_id:
                    self.cursor.execute('''
                        UPDATE referrals 
                        SET reward_claimed = 1 
                        WHERE referrer_id = ? AND is_completed = 1 AND reward_claimed = 0
                    ''', (user_id,))
                    
                    self.connection.commit()
                    return True
            
            return False
        except Exception as e:
            print(f"❌ Ошибка получения награды: {e}")
            return False
    
    # ========== МЕТОДЫ ДЛЯ ПЛАТЕЖЕЙ ==========
    
    def create_star_payment(self, user_id: int, stars_amount: int, 
                           product_type: str, product_duration: int = None) -> tuple:
        """Создание записи о платеже"""
        try:
            self.cursor.execute('''
                INSERT INTO star_payments 
                (user_id, stars_amount, product_type, product_duration, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, stars_amount, product_type, product_duration, 'pending'))
            
            payment_id = self.cursor.lastrowid
            payload = f"payment_{payment_id}_{user_id}"
            
            self.cursor.execute('''
                UPDATE star_payments 
                SET invoice_payload = ? 
                WHERE id = ?
            ''', (payload, payment_id))
            
            self.connection.commit()
            return payment_id, payload
        except Exception as e:
            print(f"❌ Ошибка создания платежа: {e}")
            return None, None
    
    def complete_star_payment(self, payment_id: int, 
                             telegram_payment_charge_id: str,
                             provider_payment_charge_id: str) -> bool:
        """Завершение успешного платежа"""
        try:
            self.cursor.execute('''
                UPDATE star_payments 
                SET status = 'completed',
                    telegram_payment_charge_id = ?,
                    provider_payment_charge_id = ?
                WHERE id = ?
            ''', (telegram_payment_charge_id, provider_payment_charge_id, payment_id))
            
            self.cursor.execute('''
                SELECT user_id, product_type, product_duration 
                FROM star_payments 
                WHERE id = ?
            ''', (payment_id,))
            
            payment = self.cursor.fetchone()
            if payment and payment['product_type'] == 'premium' and payment['product_duration']:
                self.create_premium_subscription(
                    payment['user_id'], 'paid', payment['product_duration'], 
                    payment['product_duration'] * 100,
                    f"stars_payment_{payment_id}"
                )
            
            self.connection.commit()
            return True
        except Exception as e:
            print(f"❌ Ошибка завершения платежа: {e}")
            return False
    
    # ========== МЕТОДЫ ДЛЯ АФФИЛИАТОВ (ИСПРАВЛЕНЫ) ==========
    
    def add_affiliate(self, user_id: int, commission_rate: int = 10) -> bool:
        """Добавление аффилиата"""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO affiliates (user_id, commission_rate, is_active)
                VALUES (?, ?, 1)
            ''', (user_id, commission_rate))
            
            self.connection.commit()
            return True
        except Exception as e:
            print(f"❌ Ошибка добавления аффилиата: {e}")
            return False
    
    def get_affiliate_stats(self, affiliate_id: int) -> dict:
        """Получение статистики аффилиата"""
        try:
            # Получаем базовую информацию
            self.cursor.execute('''
                SELECT a.*, u.telegram_id, u.username
                FROM affiliates a
                JOIN users u ON a.user_id = u.id
                WHERE a.id = ?
            ''', (affiliate_id,))
            
            affiliate = self.cursor.fetchone()
            
            if not affiliate:
                return {}
            
            # Получаем статистику по рефералам
            self.cursor.execute('''
                SELECT 
                    COUNT(*) as total_referrals,
                    SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as completed_referrals
                FROM referrals 
                WHERE referrer_id = ?
            ''', (affiliate['user_id'],))
            
            referrals_stats = self.cursor.fetchone()
            
            # Получаем информацию о выплатах
            self.cursor.execute('''
                SELECT 
                    SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) as total_paid,
                    SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END) as total_pending
                FROM affiliate_payouts 
                WHERE affiliate_id = ?
            ''', (affiliate_id,))
            
            payouts_stats = self.cursor.fetchone()
            
            return {
                'id': affiliate['id'],
                'user_id': affiliate['user_id'],
                'telegram_id': affiliate['telegram_id'],
                'username': affiliate['username'],
                'commission_rate': affiliate['commission_rate'],
                'total_earnings': affiliate['total_earnings'],
                'is_active': bool(affiliate['is_active']),
                'referrals_total': referrals_stats['total_referrals'] if referrals_stats else 0,
                'referrals_completed': referrals_stats['completed_referrals'] if referrals_stats else 0,
                'total_paid': payouts_stats['total_paid'] if payouts_stats else 0,
                'total_pending': payouts_stats['total_pending'] if payouts_stats else 0
            }
        except Exception as e:
            print(f"❌ Ошибка получения статистики аффилиата: {e}")
            return {}
    
    def get_all_affiliates(self) -> list:
        """Получение списка всех аффилиатов"""
        try:
            self.cursor.execute('''
                SELECT a.*, u.telegram_id, u.username
                FROM affiliates a
                JOIN users u ON a.user_id = u.id
                ORDER BY a.total_earnings DESC
            ''')
            
            affiliates = []
            for row in self.cursor.fetchall():
                affiliates.append({
                    'id': row['id'],
                    'user_id': row['user_id'],
                    'telegram_id': row['telegram_id'],
                    'username': row['username'],
                    'commission_rate': row['commission_rate'],
                    'total_earnings': row['total_earnings'],
                    'is_active': bool(row['is_active'])
                })
            
            return affiliates
        except Exception as e:
            print(f"❌ Ошибка получения списка аффилиатов: {e}")
            return []
    
    def create_affiliate_payout(self, affiliate_id: int, amount: int) -> Optional[int]:
        """Создание запроса на выплату аффилиату"""
        try:
            self.cursor.execute('''
                INSERT INTO affiliate_payouts (affiliate_id, amount, status)
                VALUES (?, ?, 'pending')
            ''', (affiliate_id, amount))
            
            payout_id = self.cursor.lastrowid
            self.connection.commit()
            return payout_id
        except Exception as e:
            print(f"❌ Ошибка создания выплаты: {e}")
            return None
    
    # ========== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ==========
    
    def close(self):
        """Закрытие соединения с базой данных"""
        self.connection.close()