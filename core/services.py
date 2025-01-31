# core/services.py
from catalog.models import Product
from reviews.models import Review
from django.db.models import Avg
from orders.models import Order

def get_product_details(product_id):
    """
    Получает детали товара по его ID.
    """
    try:
        product = Product.objects.get(id=product_id)
        return {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'image_url': product.image.url if product.image else None
        }
    except Product.DoesNotExist:
        return None

def get_product_data(product_id):
    """
    Получает данные о продукте для других модулей.
    """
    try:
        product = Product.objects.get(id=product_id)
        return {
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'description': product.description
        }
    except Product.DoesNotExist:
        return None



def create_review(user, product_id, review_text, rating):
    """
    Создаёт новый отзыв для продукта.
    """
    product = Product.objects.get(id=product_id)
    Review.objects.create(
        user=user,
        product=product,
        review_text=review_text,
        rating=rating
    )

def get_average_rating(product_id):
    """
    Возвращает среднюю оценку для указанного продукта.
    """
    avg_rating = Review.objects.filter(product_id=product_id).aggregate(Avg('rating'))['rating__avg']
    return round(avg_rating, 1) if avg_rating else None

def get_all_orders():
    """
    Возвращает все заказы из модуля orders.
    """
    return Order.objects.all()

def update_order_status(order_id, new_status):
    """
    Обновляет статус заказа по его ID.
    """
    try:
        order = Order.objects.get(id=order_id)
        order.status = new_status
        order.save()
    except Order.DoesNotExist:
        pass

def get_order_by_id(order_id):
    """
    Получает заказ по ID.
    """
    try:
        return Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return None



from orders.models import Order

def get_order_sales_data(order_id):
    """
    Получает данные по продажам для указанного заказа.
    Возвращает количество товаров и общую сумму заказа.
    """
    try:
        order = Order.objects.get(id=order_id)
        total_items = sum(item.quantity for item in order.items.all())
        total_amount = sum(
            item.quantity * item.product.price for item in order.items.all()
        )
        return {
            'total_items': total_items,
            'total_amount': total_amount
        }
    except Order.DoesNotExist:
        return {
            'total_items': 0,
            'total_amount': 0
        }


def update_delivery_address(order_id, new_delivery_address):
    """
    Обновляет адрес доставки для указанного заказа.
    """
    try:
        order = Order.objects.get(id=order_id)
        order.delivery_address = new_delivery_address
        order.save()
    except Order.DoesNotExist:
        pass  # Если заказ не найден, ничего не делаем


def get_user_orders(user):
    """
    Получает все заказы пользователя.
    """
    return Order.objects.filter(user=user).order_by('-created_at')

def get_order_items(order):
    """
    Получает все товары в заказе.
    """
    return order.items.all()

from catalog.models import Product

def get_cart_items(cart):
    """
    Получает данные о товарах в корзине.
    Возвращает список словарей с информацией о товарах.
    """
    cart_items = []
    for product_id, item in cart.items():
        product = Product.objects.get(id=product_id)
        cart_items.append({
            'product_id': product_id,
            'product': product,  # Объект товара
            'quantity': item['quantity']
        })
    return cart_items