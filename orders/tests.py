import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from catalog.models import Product
from orders.models import Order, OrderItem

from django.db.models.signals import post_save
from orders.signals import notify_admin_on_new_order

@pytest.fixture(autouse=True)
def disable_telegram_signal():
    """Отключает сигнал Telegram перед каждым тестом"""
    post_save.disconnect(notify_admin_on_new_order, sender=Order)
    yield
    post_save.connect(notify_admin_on_new_order, sender=Order)  # Включаем обратно после тестов


@pytest.mark.django_db
def test_add_to_cart(client):
    """Тест добавления товара в корзину"""
    product = Product.objects.create(name="Тестовый товар", price=100.00, description="Описание", image="image.jpg")

    response = client.post(reverse('add_to_cart', kwargs={'product_id': product.id}))

    assert response.status_code == 302  # Должен быть редирект
    cart = client.session.get('cart', {})
    assert str(product.id) in cart  # Товар должен быть в корзине

@pytest.mark.django_db
def test_update_cart(client):
    """Тест обновления количества товара в корзине"""
    product = Product.objects.create(name="Тестовый товар", price=100.00, description="Описание", image="image.jpg")

    client.post(reverse('add_to_cart', kwargs={'product_id': product.id}))
    response = client.post(reverse('update_cart', kwargs={'product_id': product.id}), data={'quantity': 3})

    assert response.status_code == 302  # Должен быть редирект
    cart = client.session.get('cart', {})
    assert cart[str(product.id)]['quantity'] == 3  # Количество должно обновиться

@pytest.mark.django_db
def test_remove_from_cart(client):
    """Тест удаления товара из корзины"""
    product = Product.objects.create(name="Тестовый товар", price=100.00, description="Описание", image="image.jpg")

    client.post(reverse('add_to_cart', kwargs={'product_id': product.id}))
    response = client.get(reverse('remove_from_cart', kwargs={'product_id': product.id}))

    assert response.status_code == 302  # Должен быть редирект
    cart = client.session.get('cart', {})
    assert str(product.id) not in cart  # Товара не должно быть в корзине

@pytest.mark.django_db
def test_create_order(client):
    """Тест создания заказа"""
    user = User.objects.create_user(username="testuser", password="password123")
    client.login(username="testuser", password="password123")

    product = Product.objects.create(name="Тестовый товар", price=100.00, description="Описание", image="image.jpg")
    client.post(reverse('add_to_cart', kwargs={'product_id': product.id}))

    response = client.post(reverse('order_create'), data={'delivery_address': 'Москва, Красная площадь'})

    assert response.status_code == 302  # Должен быть редирект
    assert Order.objects.filter(user=user).exists()  # Заказ должен быть создан
    assert OrderItem.objects.filter(order__user=user, product=product).exists()  # Товар в заказе

@pytest.mark.django_db
def test_order_list_view(client):
    """Тест просмотра списка заказов"""
    user = User.objects.create_user(username="testuser", password="password123")
    client.login(username="testuser", password="password123")

    Order.objects.create(user=user, delivery_address="Москва", status="pending")

    response = client.get(reverse('order_list'))
    assert response.status_code == 200
    assert "Москва" in response.content.decode()  # Адрес должен быть в ответе

@pytest.mark.django_db
def test_order_detail_view(client):
    """Тест просмотра деталей заказа"""
    user = User.objects.create_user(username="testuser", password="password123")
    client.login(username="testuser", password="password123")

    order = Order.objects.create(user=user, delivery_address="Москва", status="pending")

    response = client.get(reverse('order_detail', kwargs={'pk': order.id}))
    assert response.status_code == 200
    assert "Москва" in response.content.decode()

@pytest.mark.django_db
def test_reorder(client):
    """Тест повторного заказа"""
    user = User.objects.create_user(username="testuser", password="password123")
    client.login(username="testuser", password="password123")

    product = Product.objects.create(name="Тестовый товар", price=100.00, description="Описание", image="image.jpg")
    order = Order.objects.create(user=user, delivery_address="Москва", status="delivered")
    OrderItem.objects.create(order=order, product=product, quantity=2)

    response = client.get(reverse('reorder', kwargs={'order_id': order.id}))

    assert response.status_code == 302  # Должен быть редирект
    cart = client.session.get('cart', {})
    assert str(product.id) in cart  # Товар должен снова попасть в корзину
    assert cart[str(product.id)]['quantity'] == 2  # Количество должно совпадать с заказом
