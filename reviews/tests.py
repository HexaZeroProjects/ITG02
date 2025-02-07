import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from catalog.models import Product
from reviews.models import Review

@pytest.mark.django_db
def test_add_review_authenticated(client):
    """Тест добавления отзыва авторизованным пользователем"""
    user = User.objects.create_user(username="testuser", password="password123")
    product = Product.objects.create(name="Тестовый товар", price=100.00, description="Описание", image="image.jpg")

    client.login(username="testuser", password="password123")

    review_data = {
        "review_text": "Отличный товар!",
        "rating": 5
    }

    response = client.post(reverse('add_review', kwargs={'product_id': product.id}), data=review_data)

    assert response.status_code == 302  # Проверяем редирект
    assert Review.objects.filter(user=user, product=product).exists()  # Отзыв создан

@pytest.mark.django_db
def test_add_review_unauthenticated(client):
    """Тест: неавторизованный пользователь не может оставить отзыв"""
    product = Product.objects.create(name="Тестовый товар", price=100.00, description="Описание", image="image.jpg")

    review_data = {
        "review_text": "Классный товар!",
        "rating": 4
    }

    response = client.post(reverse('add_review', kwargs={'product_id': product.id}), data=review_data)

    assert response.status_code == 302  # Должен быть редирект на страницу входа
    assert not Review.objects.filter(product=product).exists()  # Отзыв не должен создаться
