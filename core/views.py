from django.http import JsonResponse
from django.views import View
from catalog.models import Product

class ProductDataView(View):
    """
    Возвращает данные о продукте для других модулей.
    """
    def get(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
            return JsonResponse({
                'id': product.id,
                'name': product.name,
                'price': str(product.price),
                'description': product.description,
            })
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)
