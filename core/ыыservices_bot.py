from django.contrib.auth import get_user_model

User = get_user_model()

def bind_telegram_service(email, telegram_id):
    """
    Привязывает Telegram ID к профилю пользователя.
    """
    user = User.objects.filter(email=email).first()
    if user and hasattr(user, 'profile'):
        user.profile.telegram_id = telegram_id
        user.profile.save()
        return {"status": "success", "message": "Telegram ID привязан"}
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

# def get_admin_orders():
#     """
#     Возвращает список заказов для администратора, включая названия товаров.
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
#
#         # Получаем товар по ID и добавляем его в список с названием и ID
#         item = Product.objects.filter(id=order["items"]).first()
#         if item:
#             grouped_orders[order_id]["items"].append(f"{item.name} (ид{item.id})")
#
#     return {"status": "success", "orders": list(grouped_orders.values())}

from orders.models import Order, OrderItem
from catalog.models import Product

def get_admin_orders():
    """
    Возвращает список заказов для администратора, включая названия товаров.
    """
    orders = Order.objects.all()
    result = []

    for order in orders:
        # Получаем товары заказа
        items = OrderItem.objects.filter(order=order)
        product_list = []

        for item in items:
            product = Product.objects.filter(id=item.product_id).first()
            if product:
                product_list.append(f"{product.name} (x{item.quantity})")

        # Формируем данные о заказе
        order_data = {
            "id": order.id,
            "created_at": order.created_at,
            "delivery_address": order.delivery_address,
            "status": order.status,
            "items": product_list if product_list else ["Нет товаров"],
        }
        result.append(order_data)

    return {"status": "success", "orders": result}