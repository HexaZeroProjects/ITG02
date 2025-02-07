import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from django.test import Client
from datetime import datetime, timedelta
from core.services import get_all_orders, update_order_status, update_delivery_address
from orders.models import Order

from django.utils.timezone import now, timedelta

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
def test_manage_order_list_view_admin(client):
    """Тест: админ видит список заказов"""
    admin = User.objects.create_superuser(username="admin", password="password123")
    client.login(username="admin", password="password123")

    response = client.get(reverse('manage_order_list'))

    assert response.status_code == 200
    assert "orders" in response.context


@pytest.mark.django_db
def test_manage_order_list_view_non_admin(client):
    """Тест: обычный пользователь не видит список заказов"""
    user = User.objects.create_user(username="testuser", password="password123")
    client.login(username="testuser", password="password123")

    response = client.get(reverse('manage_order_list'))

    assert response.status_code == 403  # Доступ запрещен

@pytest.mark.django_db
def test_manage_order_list_view_with_filters(client):
    """Тест: фильтрация списка заказов по дате и статусу"""
    admin = User.objects.create_superuser(username="admin", password="password123")
    client.login(username="admin", password="password123")

    order1 = Order.objects.create(user=admin, status="pending", created_at=now().astimezone() - timedelta(days=3))
    order2 = Order.objects.create(user=admin, status="processed", created_at=now().astimezone() - timedelta(days=1))

    response = client.get(reverse('manage_order_list'), {
        'start_date': (now() - timedelta(days=2)).strftime('%Y-%m-%d'),
        'status': ['processed']
    })

    assert response.status_code == 200
    order_ids = [order.id for order in response.context["orders"]]

    assert order1.id not in order_ids  # Должен быть отфильтрован по дате
    assert order2.id in order_ids  # Должен остаться в выборке



@pytest.mark.django_db
def test_manage_order_update_view_admin(client):
    """Тест: админ может изменить статус и адрес доставки заказа"""
    admin = User.objects.create_superuser(username="admin", password="password123")
    client.login(username="admin", password="password123")

    order = Order.objects.create(user=admin, delivery_address="Старый адрес", status="pending")

    new_data = {
        "status": "delivered",
        "delivery_address": "Новый адрес"
    }

    response = client.post(reverse('manage_order_update', kwargs={'order_id': order.id}), data=new_data)

    assert response.status_code == 302  # Должен быть редирект
    order.refresh_from_db()
    assert order.status == "delivered"
    assert order.delivery_address == "Новый адрес"


@pytest.mark.django_db
def test_manage_order_update_view_non_admin(client):
    """Тест: обычный пользователь не может редактировать заказ"""
    user = User.objects.create_user(username="testuser", password="password123")
    client.login(username="testuser", password="password123")

    order = Order.objects.create(user=user, delivery_address="Старый адрес", status="pending")

    new_data = {
        "status": "delivered",
        "delivery_address": "Новый адрес"
    }

    response = client.post(reverse('manage_order_update', kwargs={'order_id': order.id}), data=new_data)

    assert response.status_code == 403  # Доступ запрещен
    order.refresh_from_db()
    assert order.status == "pending"  # Статус не должен измениться
    assert order.delivery_address == "Старый адрес"
