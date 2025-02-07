import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage
import os
import requests
from asgiref.sync import sync_to_async
from aiogram import F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from django.conf import settings

from FlowerDelivery import settings
from core.services_bot import get_admin_orders, get_order_details, get_orders_by_status, get_analyze_products, \
	get_analyze_orders, get_image_url, get_products_by_page, is_user_registered, create_order

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


@router.message(CommandStart())
async def start(message: Message):
	"""Приветствие и проверка регистрации."""
	telegram_id = message.chat.id

	# Проверяем, зарегистрирован ли пользователь
	if not await sync_to_async(is_user_registered)(telegram_id):
		await message.answer("🚫 Вы не зарегистрированы! Пожалуйста, зарегистрируйтесь на сайте перед заказом.")
		return  # Не даём пользователю дальше взаимодействовать

	await message.answer("✅ Добро пожаловать! Вы можете оформить заказ через /catalog")


from core.services_bot import get_user_role

@router.message(Command("help"))
async def help_command(message: Message):
	"""Выводит список команд в зависимости от роли пользователя."""
	print(f"✅ Бот получил команду /help от {message.chat.id}")  # Лог в консоль

	telegram_id = message.chat.id
	role = await sync_to_async(get_user_role)(telegram_id)

	print(f"🔍 Определена роль: {role}")  # Лог для проверки

	# Разные списки команд в зависимости от роли
	commands = {
		"admin": (
			"/start - 🏠 Главное меню\n"
			"/help - ℹ️ Список команд\n"
			"/allorders - 📄📦 Список заказов\n"
			"/myorders - 💐 Список моих заказов\n"
			"/zakaz - 🛒 Данные по заказу с ID\n"
			"/statusis - 🔍 Список заказов по статусам\n"
			"/analiz - 📊 Анализ продаж\n"
			"/catalog - 🏪 Каталог товаров\n"
			"/Omykot - 🐱 Omykot\n"
			"/cancel - 🚫 Завершить процесс\n"
		),
		"staff": (
			"/start - 🏠 Главное меню\n"
			"/help - ℹ️ Список команд\n"
			"/myorders - 💐 Список моих заказов\n"
			"/allorders - 📄📦 Список заказов\n"
			"/zakaz - 🛒 Данные по заказу с ID\n"
			"/statusis - 🔍 Список заказов по статусам\n"
			"/cancel - 🚫 Завершить процесс\n"
		),
		"user": (
			"/start - 🏠 Главное меню\n"
			"/help - ℹ️ Список команд\n"
			"/myorders - 💐 Список моих заказов\n"
			"/catalog - 🏪 Каталог товаров\n"
			"/cancel - 🚫 Завершить процесс\n"
		),
		"unknown": "🚫 У вас нет доступа к боту. Пожалуйста, зарегистрируйтесь."
	}

	# Отправляем соответствующий список команд
	await message.answer(commands.get(role, "🚫 Ошибка доступа."))


@router.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext):
	"""
	Сбрасывает текущее состояние пользователя.
	"""
	await state.clear()  # Очищаем состояние
	await message.answer("✅ Вы завершили текущий процесс. Вы можете начать новую команду.")


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.services_bot import get_user_orders


@router.message(Command("myorders"))
async def my_orders(message: Message):
	"""Показывает пользователю его заказы."""
	telegram_id = message.chat.id

	response = await sync_to_async(get_user_orders)(telegram_id)

	if response["status"] == "success":
		await message.answer(f"📜 *Ваши заказы:*\n\n{response['orders']}", parse_mode="Markdown")
	elif response["status"] == "empty":
		await message.answer("ℹ️ У вас пока нет заказов.")
	else:
		await message.answer(f"❌ Ошибка: {response['message']}")


@router.message(Command("catalog"))
async def show_catalog(message: Message):
	"""Показывает первую страницу каталога."""
	await send_catalog_page(message, 1)


from aiogram.fsm.state import State, StatesGroup


class OrderState(StatesGroup):
	entering_address = State()  # Ввод адреса
	entering_phone = State()  # Ввод телефона
	confirming_order = State()  # Подтверждение


@router.message(OrderState.entering_address)
async def enter_address(message: Message, state: FSMContext):
	"""Сохраняем адрес и переходим к следующему шагу."""
	await state.update_data(address=message.text)
	print(f"✅ Состояние установлено: {await state.get_state()}")
	await message.answer("📞 Введите ваш контактный телефон:")
	await state.set_state(OrderState.entering_phone)  # Переход к следующему шагу


@router.message(OrderState.entering_phone)
async def enter_phone(message: Message, state: FSMContext):
	"""Сохраняем телефон и переходим к подтверждению заказа."""
	print(f"📌 Получен телефон: {message.text}")  # 🔹 Лог для проверки

	phone = message.text.strip()

	# Проверяем, что телефон состоит только из цифр
	if not phone.isdigit() or len(phone) < 7:
		await message.answer("❌ Некорректный телефон. Введите корректный номер.")
		return

	await state.update_data(phone=phone)

	# Получаем данные заказа
	data = await state.get_data()
	order_text = (
		f"📦 Ваш заказ:\n"
		f"💐 Товар: {data['selected_product']}\n"
		f"📍 Адрес: {data['address']}\n"
		f"📞 Телефон: {data['phone']}\n\n"
		"✅ Подтвердите заказ (да/нет)."
	)

	await message.answer(order_text)
	await state.set_state(OrderState.confirming_order)  # 🔹 Переход к подтверждению
	print(f"✅ Установлено состояние: {await state.get_state()}")  # 🔹 Лог для проверки


@router.message(OrderState.confirming_order)
async def confirm_order(message: Message, state: FSMContext):
	"""Подтверждает заказ и отправляет его в Django."""
	user_input = message.text.lower().strip()

	if user_input == "да":
		data = await state.get_data()
		telegram_id = message.chat.id

		# Создаём заказ в Django
		response = await sync_to_async(create_order)(
			telegram_id=telegram_id,
			address=data['address'],
			product_id=data['selected_product'],
			quantity=data.get("quantity", 1)  # По умолчанию 1 шт.
		)

		if response["status"] == "success":
			await message.answer(f"✅ Заказ оформлен! Номер заказа: {response['order_id']}")
		else:
			await message.answer(f"❌ Ошибка при оформлении заказа: {response['message']}")

	else:
		await message.answer("🚫 Заказ отменён.")

	await state.clear()  # Сбрасываем состояние после подтверждения


async def send_catalog_page(message: Message, page: int):
	"""Отображает страницу каталога с товарами."""
	data = await sync_to_async(get_products_by_page)(page)
	products = data["products"]

	if not products:
		await message.answer("📭 В каталоге пока нет товаров.")
		return

	keyboard = InlineKeyboardBuilder()

	# # Добавляем товары с кнопками "Выбрать"
	# for product in products:
	#     text = f"💐 {product['name']} — {product['price']} руб."
	#     await message.answer_photo(
	#         # photo=FSInputFile(product['image'].path) if product.get("image") else None,
	#         photo=FSInputFile(product['image']) if product.get("image") else None,
	#         caption=text
	#     )
	#     keyboard.add(InlineKeyboardButton(text=f"✅ Выбрать {product['name']}", callback_data=f"select_{product['id']}"))
	import os

	# Добавляем товары с кнопками "Выбрать"
	for product in products:
		text = f"💐 {product['name']} — {product['price']} руб."

		# Проверяем наличие изображения
		photo = None
		if product.get("image"):
			image_path = product["image"]
			if os.path.exists(image_path):  # Проверяем, существует ли файл
				photo = FSInputFile(image_path)

		if photo:
			await message.answer_photo(photo=photo, caption=text)
		else:
			await message.answer(text)  # Если фото нет, отправляем только текст

		keyboard.add(InlineKeyboardButton(text=f"✅ Выбрать {product['name']}", callback_data=f"select_{product['id']}"))

	# Кнопки листания страниц
	pagination_buttons = []
	if data["current_page"] > 1:
		pagination_buttons.append(InlineKeyboardButton(text="⬅ Назад", callback_data=f"page_{page - 1}"))
	if data["current_page"] < data["total_pages"]:
		pagination_buttons.append(InlineKeyboardButton(text="Вперёд ➡", callback_data=f"page_{page + 1}"))

	if pagination_buttons:
		keyboard.row(*pagination_buttons)

	await message.answer("📖 Листайте каталог:", reply_markup=keyboard.as_markup())


@router.callback_query(lambda c: c.data.startswith("page_"))
async def paginate_catalog(callback: CallbackQuery):
	"""Листает страницы каталога."""
	page = int(callback.data.split("_")[1])
	await send_catalog_page(callback.message, page)
	await callback.answer()


@router.callback_query(lambda c: c.data.startswith("select_"))
async def select_product(callback: CallbackQuery, state: FSMContext):
	"""Фиксирует выбор товара и переходит к оформлению заказа."""
	product_id = int(callback.data.split("_")[1])
	await state.update_data(selected_product=product_id)

	await callback.message.answer(f"✅ Товар добавлен в заказ. Теперь введите адрес доставки:")
	await state.set_state(OrderState.entering_address)
	await callback.answer()


@router.message(Command("Omykot"))
async def omykot_command(message: Message):
	print(f"✅ Бот получил команду /Omykot от {message.chat.id}")  # Вывод в консоль
	if message.text.startswith("/Omykot"):
		await message.answer("Привет, Владелец Магазина!")


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


# Состояния для запроса ID заказа
class ZakazStates(StatesGroup):
	waiting_for_order_id = State()


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


@router.message(AnalyzeState.awaiting_choice)
async def analiz_step_one(message: Message, state: FSMContext):
	"""
	Обрабатываем выбор пользователя.
	"""
	analiz_type = message.text.strip()

	if analiz_type == "1":
		await message.answer("📊 Выполняется анализ заказов...")
		await analyze_orders(message, state)  # ✅ Запускаем анализ заказов
	elif analiz_type == "2":
		await message.answer("📦 Выполняется анализ товаров...")
		await analyze_products(message, state)  # ✅ Запускаем анализ товаров
	else:
		await message.answer("❌ Пожалуйста, выберите 1 или 2.")  # ✅ Исправлено сообщение
		return  # ⬅ Не завершаем процесс, пока не будет корректного ввода

	await state.clear()  # ✅ Сбрасываем состояние после анализа


async def analyze_orders(message: Message, state: FSMContext):
	"""Анализ заказов."""
	orders_data = await sync_to_async(get_analyze_orders)()

	if not orders_data:
		await message.answer("📭 Нет данных для анализа заказов.")
	else:
		report = (
			f"📊 Отчет по заказам:\n"
			f"Всего заказов: {orders_data['total_orders']} на сумму {orders_data['total_amount']} руб.\n"
			f"Ожидает подтверждения: {orders_data['pending_count']} ({orders_data['pending_amount']} руб.)\n"
			f"Обрабатывается: {orders_data['processed_count']} ({orders_data['processed_amount']} руб.)\n"
			f"Доставлен: {orders_data['delivered_count']} ({orders_data['delivered_amount']} руб.)\n"
			f"Отменен: {orders_data['canceled_count']} ({orders_data['canceled_amount']} руб.)"
		)
		await message.answer(report)

	await state.clear()  # ✅ Анализ завершен – состояние сбрасываем


async def analyze_products(message: Message, state: FSMContext):
	"""Анализ товаров."""
	products_data = await sync_to_async(get_analyze_products)()

	if not products_data:
		await message.answer("📭 Нет данных для анализа товаров.")
	else:
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
			await message.answer(f"{product['name']} — {product['sales']} продаж")

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
			await message.answer(f"{product['name']} — {product['sales']} продаж")

	await state.clear()  # ✅ Анализ завершен – состояние сбрасываем

# Команда для завершения процесса
@router.message(Command("cancel"), StatusFilterStates.awaiting_status)
async def cancel_command(message: Message, state: FSMContext):
	await state.clear()
	await message.answer("✅ Вы завершили текущий процесс. Вы можете начать новую команду.")


# Обработчик для необработанных сообщений
@router.message()
async def fallback_handler(message: Message, state: FSMContext):
	current_state = await state.get_state()
	if current_state in [OrderState.entering_address, OrderState.entering_phone, OrderState.confirming_order]:
		return
	if current_state:
		# Пользователь в состоянии, но ввел что-то некорректное
		await message.answer(
			"❌ Некорректный ввод. Используйте текущую команду или завершите процесс с помощью /cancel.")
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
