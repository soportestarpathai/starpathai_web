import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class MiAppConfig(AppConfig):
    name = "mi_app"

    def ready(self):
        logger.info("mi_app ready: aplicación cargada")
