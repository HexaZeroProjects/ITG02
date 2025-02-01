import asyncio
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
import os
import requests

# Настройки
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://127.0.0.1:8000")

# Проверка токена
if not TOKEN:
    raise ValueError("Необходимо установить переменную окружения TELEGRAM_BOT_TOKEN")

# Инициализация бота, диспетчера и хранилища
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

# Регистрация роутера
dp.include_router(router)

# Обработчик команды /start
@router.message(CommandStart())
async def start(message: Message):
    await message.answer("Добро пожаловать! Введите ваш email для привязки Telegram-аккаунта.")

# Обработчик текстовых сообщений (email для привязки)
@router.message()
async def handle_message(message: Message):
    email = message.text
    telegram_id = message.chat.id

    # Отправка данных в Django
    response = requests.post(
        f"{DJANGO_API_URL}/users/bind-telegram/",
        json={"email": email, "telegram_id": telegram_id}
    )

    if response.status_code == 200:
        data = response.json()
        await message.answer(data.get("message", "Произошла ошибка"))
    else:
        await message.answer("Ошибка сервера. Попробуйте позже.")

# Основная функция
async def main():
    print("Bot is running")
    await dp.start_polling(bot)

# Запуск бота
if __name__ == "__main__":
    asyncio.run(main())
