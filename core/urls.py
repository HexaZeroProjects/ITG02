from django.urls import path
from core.views import ProductDataView

urlpatterns = [
    path('product/<int:product_id>/', ProductDataView.as_view(), name='core_product_data'),
]
