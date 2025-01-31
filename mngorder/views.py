from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect
from core.services import get_all_orders, update_order_status  # Используем сервисный слой
from core.services import get_order_by_id, update_delivery_address
from datetime import datetime


class ManageOrderListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'mngorder/manage_order_list.html'
    context_object_name = 'orders'

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        queryset = get_all_orders()
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        statuses = self.request.GET.getlist('status')

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            queryset = queryset.filter(created_at__lte=end_date)
        if statuses:
            queryset = queryset.filter(status__in=statuses)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = self.get_status_choices()
        context['selected_statuses'] = self.request.GET.getlist('status')
        return context

    def get_status_choices(self):
        # Возвращаем список возможных статусов заказа
        return [
            ('pending', 'В ожидании'),
            ('processed', 'Обрабатывается'),
            ('delivered', 'Доставлен'),
            ('canceled', 'Отменен'),
        ]


class ManageOrderUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Изменение статуса заказа и адреса доставки через сервисный слой.
    """
    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, order_id):
        # Получение данных из POST-запроса
        new_status = request.POST.get('status')
        new_delivery_address = request.POST.get('delivery_address')
        user_id = request.POST.get('user_id')  # Получаем user_id из скрытого поля

        # Обновление статуса и адреса через сервисный слой
        update_order_status(order_id, new_status)
        update_delivery_address(order_id, new_delivery_address)

        return redirect('manage_order_list')

    def get(self, request, order_id):
        # Получаем заказ через сервисный слой
        order = get_order_by_id(order_id)
        if not order:
            return redirect('manage_order_list')  # Если заказа нет, возвращаем в список

        return render(request, 'mngorder/manage_order_update.html', {'order': order})


