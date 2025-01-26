from django.urls import path
from .views import *

urlpatterns = [
    path('add-to-cart/<int:product_id>/', AddToCartView.as_view(), name='add_to_cart'),
    path('create/', OrderCreateView.as_view(), name='order_create'),
    path('', OrderListView.as_view(), name='order_list'),
    path('cart/', CartView.as_view(), name='cart_view'),  # Страница корзины
]
