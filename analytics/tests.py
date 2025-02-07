import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.timezone import now, timedelta
from orders.models import Order
from core.services import get_order_sales_data

import pytest
from django.db.models.signals import post_save
from orders.models import Order
from orders.signals import notify_admin_on_new_order

@pytest.fixture(autouse=True)
def disable_telegram_signal():
    """Отключает отправку сообщений в Telegram во время тестов"""
    post_save.disconnect(notify_admin_on_new_order, sender=Order)
    yield
    post_save.connect(notify_admin_on_new_order, sender=Order)  # Включаем обратно после тестов


@pytest.mark.django_db
def test_analytics_dashboard_view(client):
    """Тест: аналитическая панель загружается корректно"""
    admin = User.objects.create_superuser(username="admin", password="password123")
    client.login(username="admin", password="password123")

    response = client.get(reverse('analytics_dashboard'))

    assert response.status_code == 200
    assert "total_orders" in response.context
    assert "total_profit" in response.context
    assert "orders_by_status" in response.context
    assert "status_chart" in response.context
    assert "time_period_chart" in response.context
    assert "monthly_orders_chart" in response.context
    assert "cancel_orders_chart" in response.context


@pytest.mark.django_db
def test_analytics_total_orders_and_profit(client, mocker):
    """Тест: проверяем подсчёт общего количества заказов и прибыли"""
    admin = User.objects.create_superuser(username="admin", password="password123")
    client.login(username="admin", password="password123")

    # Создаём тестовые заказы
    order1 = Order.objects.create(user=admin, status="delivered", created_at=now() - timedelta(days=5))
    order2 = Order.objects.create(user=admin, status="delivered", created_at=now() - timedelta(days=2))

    # Мокируем функцию get_order_sales_data, чтобы возвращать фиксированные суммы
    # mocker.patch("core.services.get_order_sales_data", side_effect=lambda order_id: {"total_amount": 100.0})
    mocker.patch("analytics.views.get_order_sales_data", side_effect=lambda order_id: {"total_amount": 100.0})

    response = client.get(reverse('analytics_dashboard'))

    assert response.status_code == 200
    assert response.context["total_orders"] == 2
    assert response.context["total_profit"] == 200.0  # 100 * 2


@pytest.mark.django_db
def test_analytics_orders_by_status(client):
    """Тест: проверяем корректность статистики заказов по статусам"""
    admin = User.objects.create_superuser(username="admin", password="password123")
    client.login(username="admin", password="password123")

    # Создаём тестовые заказы с разными статусами
    Order.objects.create(user=admin, status="pending", created_at=now() - timedelta(days=3))
    Order.objects.create(user=admin, status="processed", created_at=now() - timedelta(days=2))
    Order.objects.create(user=admin, status="delivered", created_at=now() - timedelta(days=1))
    Order.objects.create(user=admin, status="canceled", created_at=now() - timedelta(days=4))

    response = client.get(reverse('analytics_dashboard'))

    assert response.status_code == 200
    assert response.context["orders_by_status"]["pending"] == 1
    assert response.context["orders_by_status"]["processed"] == 1
    assert response.context["orders_by_status"]["delivered"] == 1
    assert response.context["orders_by_status"]["canceled"] == 1


@pytest.mark.django_db
def test_analytics_graphs(client):
    """Тест: проверяем, что графики генерируются без ошибок"""
    admin = User.objects.create_superuser(username="admin", password="password123")
    client.login(username="admin", password="password123")

    response = client.get(reverse('analytics_dashboard'))

    assert response.status_code == 200
    assert "<div" in response.context["status_chart"]  # Проверяем, что это HTML-код графика
    assert "<div" in response.context["time_period_chart"]
    assert "<div" in response.context["monthly_orders_chart"]
    assert "<div" in response.context["cancel_orders_chart"]
