from django.views.generic import TemplateView
from core.services import get_all_orders, get_order_sales_data


class AnalyticsDashboardView(TemplateView):
    """
    Представление для аналитики и отчетов.
    """
    template_name = 'analytics/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем данные всех заказов через сервисный слой
        orders = get_all_orders()
        total_orders = orders.count()
        total_profit = sum(get_order_sales_data(order.id).get('total_amount', 0) for order in orders)

        context['total_orders'] = total_orders
        context['total_profit'] = total_profit
        return context
