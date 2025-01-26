from django.views.generic import ListView, DetailView
from django.db.models import Q
from .models import Product
from django.http import JsonResponse
from django.views import View
from django.shortcuts import redirect, get_object_or_404
from .models import Product

class ProductListView(ListView):
    model = Product
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'


    def get_queryset(self):
        queryset = Product.objects.all()
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')

        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        return queryset

class ProductDetailView(DetailView):
    model = Product
    template_name = 'catalog/product_detail.html'
    context_object_name = 'product'


