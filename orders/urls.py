from django.urls import path
from .views import *
from .views import MyOrdersView, OrderDetailView

urlpatterns = [
    path('add-to-cart/<int:product_id>/', AddToCartView.as_view(), name='add_to_cart'),

    path('update-cart/<int:product_id>/', UpdateCartView.as_view(), name='update_cart'),
    path('remove-from-cart/<int:product_id>/', RemoveFromCartView.as_view(), name='remove_from_cart'),

    path('create/', OrderCreateView.as_view(), name='order_create'),
    path('', OrderListView.as_view(), name='order_list'),
    path('cart/', CartView.as_view(), name='cart_view'),  # Страница корзины
    path('my-orders/', MyOrdersView.as_view(), name='my_orders'),

    path('order/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),

    path('buy-again-item/<int:item_id>/', BuyAgainItemView.as_view(), name='buy_again_item'),
    path('reorder/<int:order_id>/', ReorderView.as_view(), name='reorder'),
]

