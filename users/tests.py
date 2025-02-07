from django.test import TestCase

# Create your tests here.
import pytest
from django.contrib.auth.models import User
from users.models import UserProfile

@pytest.mark.django_db
def test_user_registration(client):
    """Тест регистрации нового пользователя."""
    registration_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password1": "strong_password_123",
        "password2": "strong_password_123",
        "phone": "+7 (495) 123-45-67",
        "address": "Москва, ул. Арбат, д. 12, кв. 34"
    }

    # Отправляем POST-запрос на регистрацию
    response = client.post("/users/register/", data=registration_data)

    # Проверяем, что пользователь был создан
    assert response.status_code == 302  # Перенаправление после успешной регистрации
    user = User.objects.get(username="testuser")
    assert user.email == "testuser@example.com"

    # Проверяем, что профиль был создан
    profile = UserProfile.objects.get(user=user)
    assert profile.phone == "+7 (495) 123-45-67"
    assert profile.address == "Москва, ул. Арбат, д. 12, кв. 34"

@pytest.mark.django_db
def test_profile_creation_signal():
    """Тест создания профиля через сигнал post_save."""
    user = User.objects.create_user(username="signaluser", password="password123")
    profile = UserProfile.objects.get(user=user)
    assert profile is not None  # Профиль должен быть создан автоматически

@pytest.mark.django_db
def test_user_registration_invalid_data(client):
    """Тест регистрации с некорректными данными."""
    invalid_data = {
        "username": "testuser",
        "email": "invalid-email",
        "password1": "password",
        "password2": "password",
        "phone": "+7 (495) 123-45-67",
        "address": "Москва, ул. Арбат, д. 12, кв. 34"
    }

    # Отправляем POST-запрос с некорректными данными
    response = client.post("/users/register/", data=invalid_data)

    # Проверяем, что пользователь не был создан
    assert response.status_code == 200  # Ошибка отображается на той же странице
    assert User.objects.filter(username="testuser").count() == 0

@pytest.mark.django_db
def test_profile_update(client):
    """Тест обновления профиля пользователя."""
    user = User.objects.create_user(username="profileuser", password="password123")
    profile = UserProfile.objects.get(user=user)
    client.force_login(user)

    updated_data = {
        "phone": "+7 (812) 987-65-43",
        "address": "Санкт-Петербург, Невский пр., д. 56, кв. 78",
        "telegram_id": "123456789"
    }

    # Отправляем POST-запрос для обновления профиля
    response = client.post(f"/users/profile/{profile.id}/edit/", data=updated_data)

    # Проверяем, что данные обновились
    profile.refresh_from_db()
    assert profile.phone == "+7 (812) 987-65-43"
    assert profile.address == "Санкт-Петербург, Невский пр., д. 56, кв. 78"
    assert profile.telegram_id == "123456789"
