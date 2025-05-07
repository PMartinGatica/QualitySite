from django.apps import AppConfig
import logging
import sys

logger = logging.getLogger(__name__)

class DatosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'QualitySite.datos'

    def ready(self):
        if 'migrate' not in sys.argv and 'makemigrations' not in sys.argv:  # Evitar durante migraciones
            try:
                from QualitySite.jobs import start_scheduler  # Importa desde jobs.py
                logger.info("Iniciando el scheduler desde la aplicación 'datos'...")
                start_scheduler()
            except Exception as e:
                logger.error(f"Error al iniciar el scheduler: {e}")