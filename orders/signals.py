import threading
from django.db.models.signals import post_save
from django.dispatch import receiver
from orders.models import Order
from telegram_bot.bot import notify_new_order  # Импортируем функцию уведомления

@receiver(post_save, sender=Order)
def notify_admin_on_new_order(sender, instance, created, **kwargs):
    """
    Уведомляет администратора о новом заказе.
    """
    if created:  # Только если заказ новый
        thread = threading.Thread(target=async_notify, args=(instance,))
        thread.start()

def async_notify(instance):
    """Асинхронный вызов notify_new_order() в отдельном потоке"""
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(notify_new_order(instance))