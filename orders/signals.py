from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from asgiref.sync import async_to_sync
from telegram_bot.bot import notify_new_order  # Импортируем функцию уведомления

@receiver(post_save, sender=Order)
def notify_admin_on_new_order(sender, instance, created, **kwargs):
    """
    Уведомляет администратора о новом заказе.
    """
    if created:  # Только если заказ новый
        async_to_sync(notify_new_order)(instance)
    # if created:  # Только для новых заказов
    #     async_to_sync(notify_new_order)(instance.id)  # Передаем ID заказа
