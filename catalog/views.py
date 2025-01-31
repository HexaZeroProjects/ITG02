from django.views.generic import ListView, DetailView
from django.db.models import Q

from core.services import get_average_rating

from .models import Product
from django.http import JsonResponse
from django.views import View
from django.shortcuts import redirect, get_object_or_404
from .models import Product

class ProductListView(ListView):
    model = Product
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = context['products']
        products_with_ratings = [
            (product, get_average_rating(product.id)) for product in products
        ]
        context['products_with_ratings'] = products_with_ratings
        return context

    def get_queryset(self):
        queryset = Product.objects.all()
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')

        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        return queryset

# class ProductDetailView(DetailView):
#     model = Product
#     template_name = 'catalog/product_detail.html'
#     context_object_name = 'product'

class ProductDetailView(DetailView):
    model = Product
    template_name = 'catalog/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        # Получаем контекст от родительского класса
        context = super().get_context_data(**kwargs)

        # Получаем текущий продукт
        product = self.get_object()

        # Получаем среднюю оценку для продукта с помощью сервисной функции
        average_rating = get_average_rating(product.id)

        # Добавляем среднюю оценку в контекст
        context['average_rating'] = average_rating

        return context
