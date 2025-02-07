from django.test import TestCase

# Create your tests here.
import pytest
from django.urls import reverse
from catalog.models import Product


@pytest.mark.django_db
def test_product_list_view(client):
	"""Тест списка товаров"""
	# Создаём тестовые товары
	product1 = Product.objects.create(name="Товар 1", price=100.00, description="Описание 1", image="image1.jpg")
	product2 = Product.objects.create(name="Товар 2", price=200.00, description="Описание 2", image="image2.jpg")

	response = client.get(reverse('product_list'))

	assert response.status_code == 200
	assert "Товар 1" in response.content.decode()
	assert "Товар 2" in response.content.decode()


@pytest.mark.django_db
def test_product_list_view_with_filters(client):
	"""Тест списка товаров с фильтрацией по цене"""
	Product.objects.create(name="Дешёвый товар", price=50.00, description="Описание", image="image.jpg")
	Product.objects.create(name="Дорогой товар", price=300.00, description="Описание", image="image.jpg")

	response = client.get(reverse('product_list'), {'min_price': 100, 'max_price': 250})

	assert response.status_code == 200
	assert "Дешёвый товар" not in response.content.decode()
	assert "Дорогой товар" not in response.content.decode()


@pytest.mark.django_db
def test_product_detail_view(client):
	"""Тест страницы с деталями товара"""
	product = Product.objects.create(name="Тестовый товар", price=150.00, description="Тестовое описание",
	                                 image="test.jpg")

	response = client.get(reverse('product_detail', kwargs={'pk': product.id}))

	assert response.status_code == 200
	assert "Тестовый товар" in response.content.decode()
	assert "Тестовое описание" in response.content.decode()
	assert "150.00" in response.content.decode()
