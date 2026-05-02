#!/usr/bin/env python3
"""
Тестовый скрипт для проверки зависимостей и запуска бота локально
"""
import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Проверка импорта всех зависимостей"""
    print("=" * 50)
    print("Проверка зависимостей...")
    print("=" * 50)
    
    try:
        import aiogram
        print(f"[OK] aiogram: {aiogram.__version__}")
    except ImportError as e:
        print(f"[FAIL] aiogram: {e}")
        return False
    
    try:
        import aiohttp
        print(f"[OK] aiohttp: {aiohttp.__version__}")
    except ImportError as e:
        print(f"[FAIL] aiohttp: {e}")
        return False
    
    try:
        import environs
        version = getattr(environs, '__version__', 'установлен')
        print(f"[OK] environs: {version}")
    except ImportError as e:
        print(f"[FAIL] environs: {e}")
        return False
    
    try:
        import marshmallow
        print(f"[OK] marshmallow: {marshmallow.__version__}")
        # Проверка наличия __version_info__
        if hasattr(marshmallow, '__version_info__'):
            print(f"  -> __version_info__: {marshmallow.__version_info__}")
        else:
            print(f"  -> [WARN] __version_info__ отсутствует (может быть проблема)")
    except ImportError as e:
        print(f"[FAIL] marshmallow: {e}")
        return False
    
    try:
        from env import bot_token, app_host
        print(f"[OK] env.py: загружен")
        print(f"  -> BOT_TOKEN: {'установлен' if bot_token else 'НЕ УСТАНОВЛЕН'}")
        print(f"  -> APP_HOST: {app_host}")
    except Exception as e:
        print(f"[FAIL] env.py: {e}")
        return False
    
    try:
        from services import process_register_request, process_waybill, process_writeoff
        print(f"[OK] services.py: загружен")
    except Exception as e:
        print(f"[FAIL] services.py: {e}")
        return False
    
    try:
        from bot import bot, dp
        print(f"[OK] bot.py: загружен")
    except Exception as e:
        print(f"[FAIL] bot.py: {e}")
        return False
    
    print("=" * 50)
    print("[OK] Все зависимости установлены!")
    print("=" * 50)
    return True


def test_bot_start():
    """Попытка запуска бота"""
    print("\n" + "=" * 50)
    print("Попытка запуска бота...")
    print("=" * 50)
    
    try:
        from bot import bot, dp
        from env import bot_token
        
        if not bot_token or bot_token == 'your-telegram-bot-token':
            print("[WARN] BOT_TOKEN не установлен в .env файле!")
            print("   Создайте .env файл в корне проекта или установите переменную окружения BOT_TOKEN")
            return False
        
        print(f"[OK] Токен бота установлен")
        print(f"[OK] Бот готов к запуску")
        print("\nДля запуска бота выполните:")
        print("  py bot.py")
        return True
        
    except Exception as e:
        print(f"[FAIL] Ошибка при проверке бота: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("Тестирование Telegram бота")
    print("=" * 50 + "\n")
    
    if not test_imports():
        print("\n[FAIL] Не все зависимости установлены!")
        print("\nУстановите зависимости:")
        print("  py -m pip install -r requirements.txt")
        print("\nИли используйте Docker (рекомендуется):")
        print("  docker compose build --no-cache bot")
        print("  docker compose up bot")
        sys.exit(1)
    
    if not test_bot_start():
        print("\n[FAIL] Бот не готов к запуску!")
        sys.exit(1)
    
    print("\n[OK] Все проверки пройдены! Бот готов к работе.")
    print("\nДля запуска бота:")
    print("  py bot.py")
    print("\nИли через Docker:")
    print("  docker compose build --no-cache bot")
    print("  docker compose up bot")

