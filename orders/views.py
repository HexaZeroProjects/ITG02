from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView

from .models import Order, OrderItem
from core.services import get_product_data, get_order_items, get_order_by_id  # Запросы через сервисный слой
from core.services import get_cart_items  # Импортируем сервис
from core.services import get_user_orders
from django.http import JsonResponse
from core.services_bot import get_admin_orders  # Импортируем функцию из services_bot

class OrderCreateView(LoginRequiredMixin, View):
    def post(self, request):
        cart = request.session.get('cart', {})
        if not cart:
            return redirect('product_list')

        # Добавляем отладочный вывод
        print(f"Пользователь: {request.user} (ID: {request.user.id})")
        print(f"Корзина: {cart}")

        # Получаем адрес из профиля пользователя
        user_profile = request.user.profile
        default_delivery_address = user_profile.address if user_profile.address else 'Не указано'

        # Создаем заказ
        order = Order.objects.create(
            user=request.user,
            delivery_address=request.POST.get('delivery_address', default_delivery_address)
        )

        # Добавляем товары из корзины в заказ
        for product_id, item in cart.items():
            product_data = get_product_data(product_id)
            if product_data:
                OrderItem.objects.create(
                    order=order,
                    product_id=product_data['id'],
                    quantity=item['quantity']
                )

        # Очищаем корзину
        request.session['cart'] = {}
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
    # def get(self, request):
    #     cart = request.session.get('cart', {})
    #     cart_items = []
    #     for product_id, item in cart.items():
    #         cart_items.append({
    #             'product_id': product_id,
    #             '': product_id,
    #             'quantity': item['quantity']
    #         })
    #     return render(request, 'orders/cart.html', {'cart_items': cart_items})
    def get(self, request):
        cart = request.session.get('cart', {})
        cart_items = get_cart_items(cart)  # Используем сервис
        return render(request, 'orders/cart.html', {'cart_items': cart_items})

class MyOrdersView(LoginRequiredMixin, ListView):
    template_name = 'users/my_orders.html'
    context_object_name = 'orders'

    def get_queryset(self):
        # Используем сервисный слой для получения заказов
        return get_user_orders(self.request.user)

class OrderDetailView(LoginRequiredMixin, DetailView):
    template_name = 'users/order_detail.html'
    context_object_name = 'order'

    def get_object(self):
        order_id = self.kwargs.get('pk')
        # Используем сервисный слой для получения заказа
        order = get_order_by_id(order_id, self.request.user)
        if not order:
            raise Http404("Заказ не найден")
        return order

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Используем сервисный слой для получения товаров в заказе
        context['items'] = get_order_items(self.object)
        return context

class BuyAgainItemView(View):
    def get(self, request, item_id):
        item = get_object_or_404(OrderItem, id=item_id)
        cart = request.session.get('cart', {})
        product_id = str(item.product_id)

        if product_id in cart:
            cart[product_id]['quantity'] += item.quantity
        else:
            cart[product_id] = {
                'quantity': item.quantity
            }

        request.session['cart'] = cart
        return redirect('cart_view')

class ReorderView(View):
    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        cart = request.session.get('cart', {})

        for item in order.items.all():
            product_id = str(item.product_id)
            if product_id in cart:
                cart[product_id]['quantity'] += item.quantity
            else:
                cart[product_id] = {
                    'quantity': item.quantity
                }

        request.session['cart'] = cart
        return redirect('cart_view')

class UpdateCartView(View):
    def post(self, request, product_id):
        cart = request.session.get('cart', {})
        quantity = int(request.POST.get('quantity', 1))

        if quantity > 0:
            cart[str(product_id)] = {'quantity': quantity}
        else:
            cart.pop(str(product_id), None)

        request.session['cart'] = cart
        return redirect('cart_view')

class RemoveFromCartView(View):
    def get(self, request, product_id):
        cart = request.session.get('cart', {})
        cart.pop(str(product_id), None)
        request.session['cart'] = cart
        return redirect('cart_view')

def admin_get_orders(request):
    # if not request.user.is_staff:  # Проверка роли администратора
    #     return JsonResponse({"status": "error", "message": "Доступ запрещен"}, status=403)

    # Получаем заказы через слой core
    response = get_admin_orders()
    return JsonResponse(response)

