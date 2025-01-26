from django.urls import path
from .views import ManageOrderListView, ManageOrderUpdateView

urlpatterns = [
    path('', ManageOrderListView.as_view(), name='manage_order_list'),
    path('<int:order_id>/update/', ManageOrderUpdateView.as_view(), name='manage_order_update'),
]
