# from django.views.generic import TemplateView
# from core.services import get_all_orders, get_order_sales_data
#
#
# class AnalyticsDashboardView(TemplateView):
#     """
#     Представление для аналитики и отчетов.
#     """
#     template_name = 'analytics/dashboard.html'
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#
#         # Получаем данные всех заказов через сервисный слой
#         orders = get_all_orders()
#         total_orders = orders.count()
#         total_profit = sum(get_order_sales_data(order.id).get('total_amount', 0) for order in orders)
#
#         context['total_orders'] = total_orders
#         context['total_profit'] = total_profit
#         return context


from django.utils import timezone
from datetime import timedelta
from django.views.generic import TemplateView
from core.services import get_all_orders, get_order_sales_data
import plotly.graph_objs as go
import plotly.offline as opy

class AnalyticsDashboardView(TemplateView):
    """
    Представление для аналитики и отчетов.
    """
    template_name = 'analytics/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем данные всех заказов через сервисный слой
        orders = get_all_orders()

        # Общее количество заказов и прибыль
        total_orders = orders.count()
        total_profit = sum(get_order_sales_data(order.id).get('total_amount', 0) for order in orders)

        # Данные для графиков
        context['total_orders'] = total_orders
        context['total_profit'] = total_profit
        context['orders_by_status'] = self.get_orders_by_status(orders)
        context['orders_last_week'] = self.get_orders_last_week(orders)
        context['orders_last_month'] = self.get_orders_last_month(orders)
        context['orders_last_year'] = self.get_orders_last_year(orders)

        # График: Заказы по статусам
        context['status_chart'] = self.create_status_chart(context['orders_by_status'])

        # График: Заказы за последнюю неделю, месяц, год
        context['time_period_chart'] = self.create_time_period_chart(
            context['orders_last_week'],
            context['orders_last_month'],
            context['orders_last_year']
        )

        # График: Заказы за последние 12 месяцев
        context['monthly_orders_chart'] = self.create_monthly_orders_chart(orders)
        context['cancel_orders_chart'] = self.create_cancel_orders_chart(orders)

        return context

    def get_orders_by_status(self, orders):
        """
        Возвращает количество заказов по статусам.
        """
        status_counts = {
            'pending': 0,
            'processed': 0,
            'delivered': 0,
            'canceled': 0,
        }
        for order in orders:
            status = order.status
            if status == 'in_process':  # Преобразуем in_process в processed
                status = 'processed'
            if status in status_counts:  # Проверяем, что статус корректен
                status_counts[status] += 1
        return status_counts

    def get_orders_last_week(self, orders):
        """
        Возвращает количество заказов за последнюю неделю.
        """
        last_week = timezone.now() - timedelta(days=7)
        return orders.filter(created_at__gte=last_week).count()

    def get_orders_last_month(self, orders):
        """
        Возвращает количество заказов за последний месяц.
        """
        last_month = timezone.now() - timedelta(days=30)
        return orders.filter(created_at__gte=last_month).count()

    def get_orders_last_year(self, orders):
        """
        Возвращает количество заказов за последний год.
        """
        last_year = timezone.now() - timedelta(days=365)
        return orders.filter(created_at__gte=last_year).count()

    def create_status_chart(self, orders_by_status):
        """
        Создает круговую диаграмму для заказов по статусам.
        """
        labels = list(orders_by_status.keys())
        values = list(orders_by_status.values())

        trace = go.Pie(labels=labels, values=values)
        layout = go.Layout(title="Заказы по статусам")
        figure = go.Figure(data=[trace], layout=layout)

        return opy.plot(figure, auto_open=False, output_type='div')

    def create_time_period_chart(self, last_week, last_month, last_year):
        """
        Создает столбчатую диаграмму для заказов за разные периоды.
        """
        periods = ['За последнюю неделю', 'За последний месяц', 'За последний год']
        values = [last_week, last_month, last_year]

        trace = go.Bar(x=periods, y=values)
        layout = go.Layout(title="Заказы за разные периоды")
        figure = go.Figure(data=[trace], layout=layout)

        return opy.plot(figure, auto_open=False, output_type='div')

    def create_monthly_orders_chart(self, orders):
        """
        Создает график заказов за последние 12 месяцев.
        """
        # Получаем текущую дату
        now = timezone.now()

        # Создаем список для хранения данных за каждый месяц
        monthly_data = []
        for i in range(12):
            # Вычисляем начало и конец месяца
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30 * i)
            end_of_month = start_of_month + timedelta(days=30)

            # Фильтруем заказы за текущий месяц
            monthly_orders = orders.filter(created_at__gte=start_of_month, created_at__lt=end_of_month).count()
            monthly_data.append((start_of_month.strftime('%Y-%m'), monthly_orders))

        # Разделяем данные на метки и значения
        months = [data[0] for data in reversed(monthly_data)]
        orders_count = [data[1] for data in reversed(monthly_data)]

        # Создаем график
        trace = go.Bar(x=months, y=orders_count, marker_color='green'  )
        layout = go.Layout(title="Завершенные заказы за последние 12 месяцев", xaxis_title="Месяц", yaxis_title="Количество заказов")
        figure = go.Figure(data=[trace], layout=layout)

        return opy.plot(figure, auto_open=False, output_type='div')

    def create_cancel_orders_chart(self, orders):
        """
        Создает график отменённых заказов за последние 12 месяцев.
        """
        # Получаем текущую дату
        now = timezone.now()

        # Создаем список для хранения данных за каждый месяц
        monthly_data = []
        for i in range(12):
            # Вычисляем начало и конец месяца
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30 * i)
            end_of_month = start_of_month + timedelta(days=30)

            # Фильтруем отменённые заказы за текущий месяц
            canceled_orders = orders.filter(
                created_at__gte=start_of_month,
                created_at__lt=end_of_month,
                status='canceled'  # Фильтруем только отменённые заказы
            ).count()

            # Добавляем данные в список
            monthly_data.append((start_of_month.strftime('%Y-%m'), canceled_orders))

        # Разделяем данные на метки и значения
        months = [data[0] for data in reversed(monthly_data)]
        canceled_orders_count = [data[1] for data in reversed(monthly_data)]

        # Создаем график
        trace = go.Bar(
            x=months,
            y=canceled_orders_count,
            marker_color='red'  # Цвет столбцов для отменённых заказов
        )
        layout = go.Layout(
            title="Отменённые заказы за последние 12 месяцев",
            xaxis_title="Месяц",
            yaxis_title="Количество отменённых заказов"
        )
        figure = go.Figure(data=[trace], layout=layout)

        return opy.plot(figure, auto_open=False, output_type='div')