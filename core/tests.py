import pytest
from django.urls import reverse
from catalog.models import Product

@pytest.mark.django_db
def test_get_product_data_success(client):
    """Тест: успешное получение данных о продукте"""
    product = Product.objects.create(name="Тестовый продукт", price=500, description="Описание тестового продукта")

    response = client.get(reverse("core_product_data", kwargs={"product_id": product.id}))

    assert response.status_code == 200
    json_data = response.json()
    assert json_data["id"] == product.id
    assert json_data["name"] == product.name
    # assert json_data["price"] == str(product.price)
    assert json_data["price"] == f"{product.price:.2f}"  # Приводим к формату с двумя знаками после запятой
    assert json_data["description"] == product.description


@pytest.mark.django_db
def test_get_product_data_not_found(client):
    """Тест: продукт не найден"""
    response = client.get(reverse("core_product_data", kwargs={"product_id": 999}))

    assert response.status_code == 404
    assert response.json() == {"error": "Product not found"}
