import asyncio
from telegram_bot.bot import main  # Импорт функции main из bot.py

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Запуск Telegram-бота"

    def handle(self, *args, **options):
        # Запускаем асинхронную функцию main()
        asyncio.run(main())
