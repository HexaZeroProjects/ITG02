from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect
from core.services import get_all_orders, update_order_status  # Используем сервисный слой
from core.services import get_order_by_id

class ManageOrderListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Список заказов для управления через сервисный слой.
    """
    template_name = 'mngorder/manage_order_list.html'
    context_object_name = 'orders'

    def test_func(self):
        # Ограничиваем доступ только для администраторов
        return self.request.user.is_staff

    def get_queryset(self):
        # Получение всех заказов через сервисный слой
        return get_all_orders()


class ManageOrderUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Изменение статуса заказа через сервисный слой.
    """
    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, order_id):
        # Получение нового статуса из POST-запроса
        new_status = request.POST.get('status')
        update_order_status(order_id, new_status)  # Обновление через сервисный слой
        return redirect('manage_order_list')


    def get(self, request, order_id):
        # Получаем заказ через сервисный слой
        order = get_order_by_id(order_id)
        if not order:
            return redirect('manage_order_list')  # Если заказа нет, возвращаем в список

        return render(request, 'mngorder/manage_order_update.html', {'order': order})


