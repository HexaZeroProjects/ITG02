import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InputFile, FSInputFile
from aiogram.fsm.storage.memory import MemoryStorage
import os
import requests
from asgiref.sync import sync_to_async


from FlowerDelivery import settings
from core.services_bot import get_admin_orders, get_order_details, get_orders_by_status, get_analyze_products, \
    get_analyze_orders, get_image_url

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

# Обработчик команды /help
@router.message(Command("help"))
async def help_command(message: Message):
    print(f"✅ Бот получил команду /help от {message.chat.id}")  # Вывод в консоль

    help_text = (
        "/start - 🏠 Главное меню\n"
        " /help - Список команд\n"
         " /allorders - 📄📦 Список заказов \n"
        " /zakaz -  🛒 Данные по заказу с ID \n"
        " /statusis - 🔍 Список заказов по статсусам\n"
        " /analiz - 📊 Список заказов по статсусам\n"
        " /Omykot - 🐱 Omykot\n"
       " /cancel – 🚫 завершает текущий процесс.\n"
    )
    # Убедимся, что это строка
    if not isinstance(help_text, str):
        help_text = str(help_text)

    await message.answer(help_text)

@router.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext):
    """
    Сбрасывает текущее состояние пользователя.
    """
    await state.clear()  # Очищаем состояние
    await message.answer("✅ Вы завершили текущий процесс. Вы можете начать новую команду.")


# @router.message(Command("allorders"))
# async def all_orders_command(message: Message):
#     await message.answer("Здесь будут все заказы.")


# import os
# from datetime import datetime
# from aiogram.types import FSInputFile

# @router.message(Command("allorders"))
# async def all_orders_command(message: Message):
#     # Создаем папку, если её нет
#     orders_dir = "media/orders"
#     os.makedirs(orders_dir, exist_ok=True)
#
#     # Формируем имя файла с текущей датой и временем
#     current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#     file_name = f"Orders_{current_time}.txt"
#     file_path = os.path.join(orders_dir, file_name)
#
#     # Записываем текущую дату и время в файл
#     with open(file_path, "w", encoding="utf-8") as file:
#         file.write(f"Файл создан: {current_time}\n")
#
#     # Открываем файл корректно перед отправкой
#     document = FSInputFile(file_path)
#
#     # Отправляем файл пользователю
#     await message.answer_document(document, caption="📄 Вот ваш файл с заказами.")

@router.message(Command("Omykot"))
async def omykot_command(message: Message):
    print(f"✅ Бот получил команду /Omykot от {message.chat.id}")  # Вывод в консоль
    if message.text.startswith("/Omykot"):
        await message.answer("Привет")



@router.message(Command("allorders"))
async def all_orders_command(message: Message):
    print(f"✅ Бот получил команду /allorders от {message.chat.id}")  # Вывод в консоль
    try:
        # Получаем заказы с помощью `get_admin_orders()`
        response = await sync_to_async(get_admin_orders)()


        if response["status"] != "success":
            await message.answer("❌ Ошибка при получении заказов.")
            return

        orders = response["orders"]
        if not orders:
            await message.answer("📭 Заказов пока нет.")
            return

        # Создаем папку, если её нет
        orders_dir = "media/orders"
        os.makedirs(orders_dir, exist_ok=True)

        # Формируем имя файла с текущей датой и временем
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"Orders_{current_time}.txt"
        file_path = os.path.join(orders_dir, file_name)

        # Записываем все заказы в файл
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(f"Файл создан: {current_time}\n\n")
            for order in orders:
                file.write(
                    f"ID: {order['id']}\n"
                    f"Дата: {order['created_at']}\n"
                    f"Адрес доставки: {order['delivery_address']}\n"
                    f"Статус: {order['status']}\n"
                    f"Товары: {', '.join(order['items']) if order['items'] else 'Нет товаров'}\n\n"
                )

        # Открываем файл перед отправкой
        document = FSInputFile(file_path)

        # Отправляем файл пользователю
        await message.answer_document(document, caption="📄 Вот ваш файл со всеми заказами.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")


# @router.message()
# async def zakaz_details_command(message: Message):
#     # Проверяем, начинается ли сообщение с "Zakaz" и содержит ли ID
#     if message.text.startswith("Zakaz") and message.text[5:].isdigit():
#         order_id = int(message.text[5:])  # Извлекаем ID заказа
#         try:
#             # Получаем данные о заказе
#             response = await sync_to_async(get_order_details)(order_id)
#
#             if response["status"] != "success":
#                 await message.answer(f"❌ Ошибка: {response.get('message', 'Не удалось получить данные о заказе.')}")
#                 return
#
#             order = response["order"]
#
#             # Формируем текст для отправки
#             order_text = (
#                 f"📦 **Информация о заказе**:\n"
#                 f"ID: {order['id']}\n"
#                 f"Дата: {order['created_at']}\n"
#                 f"Адрес доставки: {order['delivery_address']}\n"
#                 f"Статус: {order['status']}\n"
#                 f"Товары: {', '.join(order['items']) if order['items'] else 'Нет товаров'}"
#             )
#
#             # Отправляем сообщение с информацией о заказе
#             await message.answer(order_text)
#
#         except Exception as e:
#             await message.answer(f"Произошла ошибка: {e}")


# @router.message()
# async def zakaz_details_command(message: Message):
#     print(f"✅ Бот получил команду /ZakazID от {message.chat.id}")  # Вывод в консоль
#     # Проверяем, начинается ли сообщение с "Zakaz"
#     if not message.text.startswith("Zakaz"):
#         return  # Если не начинается с "Zakaz", передаем обработку другим хендлерам
#
#     # Пытаемся извлечь ID заказа
#     try:
#         order_id = int(message.text.replace("Zakaz", "").strip())
#     except ValueError:
#         await message.answer("❌ Неверный формат команды. Используйте: Zakaz<ID заказа>.")
#         return
#
#     # Ваш основной код для обработки заказа
#     response = await sync_to_async(get_order_details)(order_id)
#
#     if response["status"] != "success":
#         await message.answer(response["message"])
#     else:
#         order = response["order"]
#         await message.answer(
#             f"📄 Детали заказа:\n"
#             f"ID: {order['id']}\n"
#             f"Дата: {order['created_at']}\n"
#             f"Адрес доставки: {order['delivery_address']}\n"
#             f"Статус: {order['status']}\n"
#             f"Товары: {', '.join(order['items']) if order['items'] else 'Нет товаров'}"
#         )


# Обработчик для email (сообщения, содержащие @)

# Состояния для запроса ID заказа
class ZakazStates(StatesGroup):
    waiting_for_order_id = State()

# Хендлер для команды /zakaz
# @router.message(Command("zakaz"))
# async def zakaz_start_command(message: Message, state: FSMContext):
#     print(f"✅ Бот получил команду /zakaz от {message.chat.id}")  # Вывод в консоль
#     await message.answer("Введите ID заказа:")
#     await state.set_state(ZakazStates.waiting_for_order_id)

@router.message(Command("zakaz"))
async def zakaz_start_command(message: Message, state: FSMContext):
    print(f"✅ Бот получил команду /zakaz от {message.chat.id}")  # Вывод в консоль
    await state.clear()  # Сбрасываем состояние перед началом
    await message.answer("Введите ID заказа:")
    await state.set_state(ZakazStates.waiting_for_order_id)


# Хендлер для обработки введенного ID заказа
@router.message(ZakazStates.waiting_for_order_id)
async def process_order_id(message: Message, state: FSMContext):
    try:
        # Преобразуем текст в число
        order_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Пожалуйста, введите числовой ID заказа.")
        return

    # Получаем детали заказа
    response = await sync_to_async(get_order_details)(order_id)

    if response["status"] != "success":
        await message.answer(response["message"])
    else:
        order = response["order"]
        await message.answer(
            f"📄 Детали заказа:\n"
            f"ID: {order['id']}\n"
            f"Дата: {order['created_at']}\n"
            f"Адрес доставки: {order['delivery_address']}\n"
            f"Статус: {order['status']}\n"
            f"Товары: {', '.join(order['items']) if order['items'] else 'Нет товаров'}"
        )

    # Сбрасываем состояние
    await state.clear()

from aiogram import F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Создаем группу состояний
class StatusFilterStates(StatesGroup):
    awaiting_status = State()

# Первый шаг: Запрос статуса у пользователя
@router.message(Command("statusis"))
async def statusis_step_one(message: Message, state: FSMContext):
    print(f"✅ Бот получил команду /statusis от {message.chat.id}")  # Лог в консоль
    await message.answer(
        "Введите статус заказа для фильтрации:\n"
        "1. pending - Ожидает подтверждения\n"
        "2. processed - Обрабатывается\n"
        "3. delivered - Доставлен\n"
        "4. canceled - Отменен\n"
        "\n/cancel – завершает текущий процесс."
    )
    # Устанавливаем состояние
    await state.set_state(StatusFilterStates.awaiting_status)

# Второй шаг: Получение статуса и вывод заказов
@router.message(F.text, StatusFilterStates.awaiting_status)
async def statusis_step_two(message: Message, state: FSMContext):
    try:
        # Карта статусов
        status_map = {
            "1": "pending",
            "2": "processed",
            "3": "delivered",
            "4": "canceled",
            "pending": "pending",
            "processed": "processed",
            "delivered": "delivered",
            "canceled": "canceled",
        }

        # Получение статуса
        status_name = status_map.get(message.text.strip().lower())
        if not status_name:
            await message.answer("❌ Неверный статус. Введите цифру от 1 до 4 или одно из названий статусов.")
            return

        # Получение заказов по статусу
        response = await sync_to_async(get_orders_by_status)(status_name)

        if response["status"] != "success":
            await message.answer(f"❌ Ошибка: {response.get('message', 'Не удалось получить заказы.')}")
            return

        order_ids = response["order_ids"]
        if not order_ids:
            await message.answer("📭 Заказы с указанным статусом отсутствуют.")
        else:
            orders_text = "📋 Список заказов с указанным статусом:\n" + ", ".join(map(str, order_ids))
            await message.answer(orders_text)

        # Завершаем состояние
        await state.clear()

    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")
        await state.clear()

# Определяем группу состояний
class AnalyzeState(StatesGroup):
    awaiting_choice = State()
    awaiting_data = State()
    awaiting_status = State()

# Регистрация команды /analiz
@router.message(Command("analiz"))
async def analiz_command(message: Message, state: FSMContext):
    """
    Начальный шаг анализа.
    """
    await message.answer(
        "Выберите, что вы хотите проанализировать:\n"
        "1️⃣ - 📊 Отчет по заказам\n"
        "2️⃣ - 📦 Отчет по товарам\n"
        "\n/cancel – завершает текущий процесс."
    )

    # Устанавливаем состояние
    await state.set_state(AnalyzeState.awaiting_choice)

@router.message()
async def analiz_step_one(message: Message, state: FSMContext):
    """
    Обрабатываем выбор пользователя.
    """
    analiz_type = message.text.strip()
    if analiz_type not in ["1", "2"]:
        await message.answer("❌ Пожалуйста, выберите 1 или 2.")
        return

    if analiz_type == "1":
        # Перейти к отчету по заказам
        await state.set_state("analyzing_orders")
        await message.answer("📊 Выполняется анализ заказов...")
        await analyze_orders(message, state)
    elif analiz_type == "2":
        # Перейти к отчету по товарам
        await state.set_state("analyzing_products")
        await message.answer("📦 Выполняется анализ товаров...")
        await analyze_products(message, state)


async def analyze_orders(message: Message, state: FSMContext):
    """
    Анализ заказов.
    """
    # Здесь запрос данных из базы
    orders_data = await sync_to_async(get_analyze_orders)()

    if not orders_data:
        await message.answer("📭 Нет данных для анализа заказов.")
        await state.clear()
        return

    # Формируем отчет
    report = (
        f"📊 Отчет по заказам:\n"
        f"Всего заказов: {orders_data['total_orders']} на сумму {orders_data['total_amount']} руб.\n"
        f"Ожидает подтверждения: {orders_data['pending_count']} ({orders_data['pending_amount']} руб.)\n"
        f"Обрабатывается: {orders_data['processed_count']} ({orders_data['processed_amount']} руб.)\n"
        f"Доставлен: {orders_data['delivered_count']} ({orders_data['delivered_amount']} руб.)\n"
        f"Отменен: {orders_data['canceled_count']} ({orders_data['canceled_amount']} руб.)"
    )
    await message.answer(report)
    await state.clear()

from django.conf import settings



# async def analyze_products(message: Message, state: FSMContext):
#     """
#     Анализ товаров.
#     """
#     # Получаем данные о товарах
#     products_data = await sync_to_async(get_analyze_products)()
#
#     if not products_data:
#         await message.answer("📭 Нет данных для анализа товаров.")
#         await state.clear()
#         return
#
#     # Формируем топ-3 и антитоп-3
#     await message.answer("📦 Топ-3 продаваемых товаров:")
#     for product in products_data["top_products"]:
#         image_url = product["image"] if product["image"] else None
#         if image_url:
#             await message.answer_photo(
#                 photo=product["image"],
#                 caption=f"{product['name']} — {product['sales']} продаж"
#             )
#         else:
#             await message.answer(
#                 f"{product['name']} — {product['sales']} продаж\n(Изображение отсутствует)"
#             )
#
#     await message.answer("📦 Антитоп-3 продаваемых товаров:")
#     for product in products_data["worst_products"]:
#         image_url = product["image"] if product["image"] else None
#         if image_url:
#             await message.answer_photo(
#                 photo=product["image"],
#                 caption=f"{product['name']} — {product['sales']} продаж"
#             )
#         else:
#             await message.answer(
#                 f"{product['name']} — {product['sales']} продаж\n(Изображение отсутствует)"
#             )
#
#     await state.clear()

from aiogram.types import InputFile
import os

from aiogram.types import InputFile
import os

import os
from aiogram.types import InputFile

import os
from aiogram.types import InputFile


import os
from aiogram.types import InputFile

async def analyze_products(message: Message, state: FSMContext):
    """
    Анализ товаров.
    """
    # Получаем данные о товарах
    products_data = await sync_to_async(get_analyze_products)()

    if not products_data:
        await message.answer("📭 Нет данных для анализа товаров.")
        await state.clear()
        return

    # Формируем топ-3 и антитоп-3
    await message.answer("📦 Топ-3 продаваемых товаров:")
    for product in products_data["top_products"]:
        if product.get("image"):
            image_path = product["image"].path  # Локальный путь к файлу
            if os.path.exists(image_path):  # Проверяем существование файла
                try:
                    # Используем FSInputFile для передачи файла
                    await message.answer_photo(
                        photo=FSInputFile(image_path),  # Заменяем InputFile на FSInputFile
                        caption=f"{product['name']} — {product['sales']} продаж"
                    )
                except Exception as e:
                    await message.answer(
                        f"{product['name']} — {product['sales']} продаж\n(Ошибка при отправке изображения: {e})"
                    )
            else:
                await message.answer(
                    f"{product['name']} — {product['sales']} продаж\n(Файл изображения не найден)"
                )
        else:
            await message.answer(
                f"{product['name']} — {product['sales']} продаж\n(Изображение отсутствует)"
            )

    await message.answer("📦 Антитоп-3 продаваемых товаров:")
    for product in products_data["worst_products"]:
        if product.get("image"):
            image_path = product["image"].path  # Локальный путь к файлу
            if os.path.exists(image_path):  # Проверяем существование файла
                try:
                    # Используем FSInputFile для передачи файла
                    await message.answer_photo(
                        photo=FSInputFile(image_path),  # Заменяем InputFile на FSInputFile
                        caption=f"{product['name']} — {product['sales']} продаж"
                    )
                except Exception as e:
                    await message.answer(
                        f"{product['name']} — {product['sales']} продаж\n(Ошибка при отправке изображения: {e})"
                    )
            else:
                await message.answer(
                    f"{product['name']} — {product['sales']} продаж\n(Файл изображения не найден)"
                )
        else:
            await message.answer(
                f"{product['name']} — {product['sales']} продаж\n(Изображение отсутствует)"
            )

    await state.clear()

# def get_orders_analysis():
#     """
#     Получение данных анализа заказов.
#     """
#     # Пример данных из базы
#     return {
#         "total_orders": 23,
#         "total_amount": 100000,
#         "pending_count": 1,
#         "pending_amount": 100,
#         "processed_count": 15,
#         "processed_amount": 23223,
#         "delivered_count": 10,
#         "delivered_amount": 34343,
#         "canceled_count": 2,
#         "canceled_amount": 34343,
#     }


# def get_products_analysis():
#     """
#     Получение данных анализа товаров.
#     """
#     # Пример данных из базы
#     return {
#         "top_products": [
#             {"name": "Товар 1", "sales": 100, "image": "https://example.com/image1.jpg"},
#             {"name": "Товар 2", "sales": 80, "image": "https://example.com/image2.jpg"},
#             {"name": "Товар 3", "sales": 60, "image": "https://example.com/image3.jpg"},
#         ],
#         "worst_products": [
#             {"name": "Товар 4", "sales": 1, "image": "https://example.com/image4.jpg"},
#             {"name": "Товар 5", "sales": 2, "image": "https://example.com/image5.jpg"},
#             {"name": "Товар 6", "sales": 3, "image": "https://example.com/image6.jpg"},
#         ],
#     }
#




# Команда для завершения процесса
@router.message(Command("cancel"), StatusFilterStates.awaiting_status)
async def cancel_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("✅ Вы завершили текущий процесс. Вы можете начать новую команду.")



# Обработчик для необработанных сообщений
@router.message()
async def fallback_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state:
        # Пользователь в состоянии, но ввел что-то некорректное
        await message.answer("❌ Некорректный ввод. Используйте текущую команду или завершите процесс с помощью /cancel.")
    else:
        # Пользователь не в состоянии и не ввел команду
        await message.answer("❌ Команда не распознана. Используйте /help для списка доступных команд.")


@router.message()
async def handle_message(message: Message):
    # Проверяем, если это команда, не обрабатываем здесь
    if message.text.startswith("/"):
        return  # Даем команде обработаться в другом хендлере

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


# Обработчик для всех остальных сообщений
@router.message()
async def other_messages(message: Message):
    await message.answer("Пожалуйста, введите email (должен содержать @) или используйте команды /start или /help")

# Уведомление о новом заказе
async def notify_new_order(order):
    """
    Отправляет уведомление администратору о новом заказе.
    """
    admin_chat_id = settings.ADMIN_CHAT_ID

    # Форматируем дату
    formatted_date = order.created_at.strftime("%d.%m.%Y %H:%M")

    # Формируем ссылку на заказ
    order_url = f"http://localhost:8000/manage-orders/{order.id}/update/"

    # Формируем сообщение
    message = (
        f"Новый заказ!\n"
        f"ID: {order.id}\n"
        f"Дата: {formatted_date}\n"
        f"Статус: {order.get_status_display()}\n"
        f'Ссылка на заказ: {order_url}'
    )

    # Отправляем сообщение
    await bot.send_message(chat_id=admin_chat_id, text=message)

# Основная функция
async def main():
    print("Bot is running")
    await dp.start_polling(bot)

# Запуск бота
if __name__ == "__main__":
    asyncio.run(main())