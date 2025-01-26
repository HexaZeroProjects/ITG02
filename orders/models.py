from django.db import models

# Create your models here.
# orders/models.py

from django.db import models
from catalog.models import Product
from django.contrib.auth.models import User

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    delivery_address = models.TextField()
    status = models.CharField(max_length=20, choices=(
        ('pending', 'Ожидает подтверждения'),
        ('processed', 'Обрабатывается'),
        ('delivered', 'Доставлен'),
        ('canceled', 'Отменен')
    ), default='pending')

    def __str__(self):
        return f"Заказ {self.id} от {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} шт. продукта {self.product_id} в заказе {self.order.id}"

