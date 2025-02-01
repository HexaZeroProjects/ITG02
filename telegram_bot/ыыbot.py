import asyncio
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
import os
import requests
from datetime import datetime
from asgiref.sync import sync_to_async
from django.conf import settings

from core.services import get_product_data, get_order_items
from orders.models import Order

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

# Обработчик команды /orders
@router.message(Command("orders"))
async def admin_orders(message: Message):
    """
    Команда для просмотра списка заказов администратором.
    """
    try:
        # Получаем заказы в асинхронном режиме
        orders = await sync_to_async(list)(Order.objects.all().values("id", "created_at", "delivery_address", "status", "items"))
        grouped_orders = {}

        for order in orders:
            order_id = order["id"]
            if order_id not in grouped_orders:
                grouped_orders[order_id] = {
                    "id": order["id"],
                    # Форматируем дату
                    "created_at": datetime.fromisoformat(order["created_at"]).strftime("%d.%m.%Y %H:%M"),
                    "delivery_address": order["delivery_address"],
                    "status": order["status"],
                    "items": [],
                }

            # Получаем данные о товаре через `core/services.py`
            product_data = await sync_to_async(get_product_data)(order["items"])
            if product_data:
                grouped_orders[order_id]["items"].append(f"{product_data['name']} (ид{product_data['id']})")

        if not grouped_orders:
            await message.answer("Заказов пока нет.")
            return

        # Формируем текст для отправки в Telegram
        message_text = "Список заказов:\n"
        for order in grouped_orders.values():
            items_list = ", ".join(order["items"]) if order["items"] else "Нет товаров"
            message_text += (
                f"ID: {order['id']}\n"
                f"Дата: {order['created_at']}\n"
                f"Адрес доставки: {order['delivery_address']}\n"
                f"Товары: {items_list}\n"
                f"Статус: {order['status']}\n\n"
            )

        await message.answer(message_text)

    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")

# Обработчик команды /orderdetails
@router.message(Command("orderdetails"))
async def order_details(message: Message):
    """
    Команда для просмотра состава заказа по его ID.
    """
    try:
        # Получаем ID заказа из сообщения
        args = message.text.split()
        if len(args) < 2:
            await message.answer("Используйте команду так: /orderdetails <ID заказа>")
            return

        order_id = args[1]  # Пример: /orderdetails 123
        order_id = int(order_id)  # Преобразуем в число

        # Получаем состав заказа
        order_items = await sync_to_async(get_order_items)(order_id)

        # Формируем текст с составом заказа
        items_text = "\n".join([f"- {item.name} (x{item.quantity})" for item in order_items]) or "Заказ пуст"

        # Отправляем ответ пользователю
        await message.answer(f"Состав заказа ID {order_id}:\n{items_text}")

    except ValueError:
        await message.answer("ID заказа должен быть числом.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")

# Основная функция
async def main():
    print("Bot is running")

    # Проверяем, подключен ли роутер через sub_routers
    if router not in dp.sub_routers:
        dp.include_router(router)  # Подключаем роутер только если он еще не добавлен

    await dp.start_polling(bot)

# Запуск бота
if __name__ == "__main__":
    asyncio.run(main())