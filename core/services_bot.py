from django.contrib.auth import get_user_model

from FlowerDelivery import settings

User = get_user_model()

def bind_telegram_service(email, telegram_id):
    """
    Привязывает Telegram ID к профилю пользователя.
    """
    user = User.objects.filter(email=email).first()
    if user and hasattr(user, 'profile'):
        user.profile.telegram_id = telegram_id
        user.profile.save()

        # Проверяем, действительно ли ID записался
        saved_user = User.objects.filter(profile__telegram_id=telegram_id).exists()
        if saved_user:
            return {"status": "success", "message": "Telegram ID привязан"}
        else:
            return {"status": "error", "message": "Ошибка сохранения Telegram ID"}

    return {"status": "error", "message": "Пользователь не найден или профиль отсутствует"}




from orders.models import Order

# def get_admin_orders():
#     """
#     Возвращает список заказов для администратора, сгруппированных по ID.
#     """
#     orders = Order.objects.all().values("id", "created_at", "delivery_address", "status", "items")
#     grouped_orders = {}
#
#     for order in orders:
#         order_id = order["id"]
#         if order_id not in grouped_orders:
#             grouped_orders[order_id] = {
#                 "id": order["id"],
#                 "created_at": order["created_at"],
#                 "delivery_address": order["delivery_address"],
#                 "status": order["status"],
#                 "items": [],
#             }
#         grouped_orders[order_id]["items"].append(order["items"])
#
#     return {"status": "success", "orders": list(grouped_orders.values())}

from orders.models import Order
from catalog.models import Product  # Убедитесь, что модель Item импортирована

from datetime import datetime

def format_date(date_value):
    try:
        # Если значение уже является объектом datetime
        if isinstance(date_value, datetime):
            return date_value.strftime('%d.%m.%Y %H:%M')
        # Если это строка, преобразуем в datetime
        elif isinstance(date_value, str):
            parsed_date = datetime.fromisoformat(date_value)
            return parsed_date.strftime('%d.%m.%Y %H:%M')
    except Exception:
        # Если дата некорректна, возвращаем дефолтное значение
        return "Некорректная дата"




def get_admin_orders():
    """
    Возвращает список заказов для администратора, включая названия товаров.
    """
    from orders.models import Order, OrderItem
    from catalog.models import Product

    # Получаем все заказы
    orders = Order.objects.all()
    grouped_orders = []

    # Проходим по каждому заказу
    for order in orders:
        # Получаем все OrderItem, связанные с текущим заказом
        order_items = OrderItem.objects.filter(order=order)

        # Формируем список товаров
        products = []
        for item in order_items:
            # Проверяем, есть ли продукт, связанный с OrderItem
            product = Product.objects.filter(id=item.product_id).first()
            if product:
                products.append(f"{product.name} (ид{product.id}) — {item.quantity} шт.")
            else:
                products.append("Неизвестный товар")

        # Добавляем данные о заказе
        grouped_orders.append({
            "id": order.id,
            # "created_at": order.created_at,
            "created_at": order.created_at.strftime("%d.%m.%Y %H:%M"),
            "delivery_address": order.delivery_address,
            "status": order.status,
            "items": products if products else ["Нет товаров"],
        })

    return {"status": "success", "orders": grouped_orders}

def get_order_details(order_id):
    """
    Возвращает детали одного заказа, включая названия товаров.
    """
    from orders.models import Order, OrderItem
    from catalog.models import Product

    # Получаем заказ по ID
    order = Order.objects.filter(id=order_id).first()

    if not order:
        return {"status": "error", "message": "Заказ не найден"}

    # Получаем все OrderItem, связанные с текущим заказом
    order_items = OrderItem.objects.filter(order=order)

    # Формируем список товаров
    products = []
    for item in order_items:
        # Проверяем, есть ли продукт, связанный с OrderItem
        product = Product.objects.filter(id=item.product_id).first()
        if product:
            products.append(f"{product.name} (ид{product.id}) — {item.quantity} шт.")
        else:
            products.append("Неизвестный товар")

    # Формируем данные о заказе
    order_details = {
        "id": order.id,
        "created_at": order.created_at.strftime("%d.%m.%Y %H:%M"),
        "delivery_address": order.delivery_address,
        "status": order.status,
        "items": products if products else ["Нет товаров"],
    }

    return {"status": "success", "order": order_details}


def get_orders_by_status(status_name):
    """
    Получает список заказов по указанному статусу.
    """
    from orders.models import Order

    # Допустимые статусы
    valid_statuses = ["pending", "processed", "delivered", "canceled"]

    # Проверяем, является ли статус корректным
    if status_name not in valid_statuses:
        return {"status": "error", "message": "Некорректный статус."}

    # Получаем заказы с указанным статусом
    orders = Order.objects.filter(status=status_name).values("id")
    order_ids = [order["id"] for order in orders]

    return {"status": "success", "order_ids": order_ids}


from orders.models import Order, OrderItem
from catalog.models import Product
from django.db.models import Sum, Count

from django.db.models import Sum, F

from django.db.models import Sum, F

def get_analyze_orders():
    """
    Анализирует заказы, возвращая общую сумму и детали по статусам.
    """
    # Общая информация
    total_orders = Order.objects.count()
    total_amount = (
        Order.objects.annotate(
            order_total=Sum(F("items__quantity") * F("items__product__price"))
        )
        .aggregate(total_sum=Sum("order_total"))["total_sum"] or 0
    )

    # Детали по статусам
    statuses = ["pending", "processed", "delivered", "canceled"]
    status_details = {
        "pending_count": 0,
        "pending_amount": 0,
        "processed_count": 0,
        "processed_amount": 0,
        "delivered_count": 0,
        "delivered_amount": 0,
        "canceled_count": 0,
        "canceled_amount": 0,
    }

    for status in statuses:
        status_orders = Order.objects.filter(status=status).annotate(
            order_total=Sum(F("items__quantity") * F("items__product__price"))
        )
        count = status_orders.count()
        amount = status_orders.aggregate(total_sum=Sum("order_total"))["total_sum"] or 0
        status_details[f"{status}_count"] = count
        status_details[f"{status}_amount"] = amount

    # Формируем результат
    result = {
        "total_orders": total_orders,
        "total_amount": total_amount,
        **status_details,
    }
    return result

def get_image_url(image_path):
    """
    Возвращает полный URL для изображения.
    """

    base_url = getattr(settings, "DJANGO_API_URL", "http://127.0.0.1:8000")
    print(f"{base_url}/media/{image_path}")
    return f"{base_url}/media/{image_path}"


def get_analyze_products():
    """
    Анализ товаров (топ-3 и антитоп-3 продаваемых товаров).
    """
    # Получаем данные о продажах товаров
    products_summary = (
        OrderItem.objects.values("product_id")
        .annotate(
            total_quantity=Sum("quantity"),
        )
        .order_by("-total_quantity")  # Сортируем по количеству продаж
    )

    top_products = []
    worst_products = []

    # Формируем топ-3 и антитоп-3
    for idx, entry in enumerate(products_summary):
        product = Product.objects.filter(id=entry["product_id"]).first()
        if not product:
            continue
        print(f"URL изображения: {product.image}")
        product_data = {
            "name": product.name,
            "sales": entry["total_quantity"],
            # "image": get_image_url(product.image) if product.image else None,  # Используем get_image_url
            "image": product.image if product.image else None,  # Используем get_image_url
        }

        if idx < 3:
            top_products.append(product_data)
        elif idx >= len(products_summary) - 3:
            worst_products.append(product_data)

    return {"top_products": top_products, "worst_products": worst_products}



# from orders.models import Order, OrderItem
# from catalog.models import Product
#
# def get_admin_orders():
#     """
#     Возвращает список заказов для администратора, включая названия товаров.
#     """
#     orders = Order.objects.all()
#     result = []
#
#     for order in orders:
#         # Получаем товары заказа
#         items = OrderItem.objects.filter(order=order)
#         product_list = []
#
#         for item in items:
#             product = Product.objects.filter(id=item.product_id).first()
#             if product:
#                 product_list.append(f"{product.name} (x{item.quantity})")
#
#         # Формируем данные о заказе
#         order_data = {
#             "id": order.id,
#             "created_at": order.created_at,
#             "delivery_address": order.delivery_address,
#             "status": order.status,
#             "items": product_list if product_list else ["Нет товаров"],
#         }
#         result.append(order_data)
#
#     return {"status": "success", "orders": result}