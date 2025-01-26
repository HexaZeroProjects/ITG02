from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Order, OrderItem
from core.services import get_product_data  # Запросы через сервисный слой

class OrderCreateView(LoginRequiredMixin, View):
    def post(self, request):
        """
        Создание нового заказа из корзины через сервисный слой.
        """
        cart = request.session.get('cart', {})
        if not cart:
            return redirect('product_list')  # Если корзина пуста, возвращаем в каталог

        order = Order.objects.create(
            user=request.user,
            delivery_address=request.POST.get('delivery_address', '')
        )

        for product_id, item in cart.items():
            product_data = get_product_data(product_id)  # Данные о продукте из `core`
            if product_data:
                OrderItem.objects.create(
                    order=order,
                    product_id=product_data['id'],  # Храним ID продукта
                    quantity=item['quantity']
                )
            else:
                # Если продукт не найден, игнорируем его
                continue

        request.session['cart'] = {}  # Очищаем корзину после создания заказа
        return redirect('order_list')


class AddToCartView(View):
    def post(self, request, product_id):
        """
        Добавление товара в корзину через сессию.
        """
        cart = request.session.get('cart', {})
        if str(product_id) in cart:
            cart[str(product_id)]['quantity'] += 1
        else:
            cart[str(product_id)] = {
                'quantity': 1
            }
        request.session['cart'] = cart
        return redirect('product_list')


class OrderListView(LoginRequiredMixin, View):
    """
    Отображение списка заказов для текущего пользователя.
    """
    def get(self, request):
        orders = Order.objects.filter(user=request.user).prefetch_related('items')
        return render(request, 'orders/order_list.html', {'orders': orders})


class CartView(View):
    """
    Отображение корзины пользователя.
    """
    def get(self, request):
        cart = request.session.get('cart', {})
        cart_items = []
        for product_id, item in cart.items():
            cart_items.append({
                'product_id': product_id,
                'quantity': item['quantity']
            })
        return render(request, 'orders/cart.html', {'cart_items': cart_items})