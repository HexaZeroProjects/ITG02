import asyncio
from django.core.management.base import BaseCommand
from telegram_bot.bot import main  # Функция запуска бота

class Command(BaseCommand):
    help = "Запускает Telegram-бота"

    def handle(self, *args, **options):
        """Запуск бота без проблем с потоками"""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())  # ✅ Работает без ошибок
