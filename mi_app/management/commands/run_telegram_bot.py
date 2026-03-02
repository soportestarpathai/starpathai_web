"""
Management command para iniciar el bot de Telegram de Órbita.

Uso:
    python manage.py run_telegram_bot
"""
import asyncio
import logging
import sys

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Inicia el bot de Telegram de Órbita para postulaciones conversacionales."

    def handle(self, *args, **options):
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        from mi_app.telegram_bot import build_application

        self.stdout.write(self.style.SUCCESS("🤖 Iniciando bot de Telegram de Órbita..."))
        logger.info("telegram_bot: starting polling")

        app = build_application()

        self.stdout.write(self.style.SUCCESS(
            "✅ Bot activo. Esperando mensajes...\n"
            "   Presiona Ctrl+C para detener."
        ))
        app.run_polling(drop_pending_updates=True)
