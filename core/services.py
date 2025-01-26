# core/services.py

from catalog.models import Product

def get_product_details(product_id):
    """
    Получает детали товара по его ID.
    """
    try:
        product = Product.objects.get(id=product_id)
        return {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'image_url': product.image.url if product.image else None
        }
    except Product.DoesNotExist:
        return None

def get_product_data(product_id):
    """
    Получает данные о продукте для других модулей.
    """
    try:
        product = Product.objects.get(id=product_id)
        return {
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'description': product.description
        }
    except Product.DoesNotExist:
        return None
