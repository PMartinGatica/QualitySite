import logging
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.interval import IntervalTrigger
from django_apscheduler.jobstores import register_events
from django.core.management import call_command

logger = logging.getLogger(__name__)

def start_scheduler():
    """
    Inicializa el scheduler y registra los jobs.
    """
    try:
        # Configuración del scheduler
        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore(), "default")
        scheduler.add_executor(ThreadPoolExecutor(10))
        register_events(scheduler)

        # Registrar los jobs
        scheduler.add_job(
            import_mes_job,
            trigger=IntervalTrigger(minutes=10),
            id="import_mes_job",
            replace_existing=True,
        )
        logger.info("Job 'import_mes_job' registrado para ejecutarse cada 10 minutos.")

        scheduler.add_job(
            import_mqs_job,
            trigger=IntervalTrigger(minutes=10),
            id="import_mqs_job",
            replace_existing=True,
        )
        logger.info("Job 'import_mqs_job' registrado para ejecutarse cada 10 minutos.")

        scheduler.add_job(
            import_yield_job,
            trigger=IntervalTrigger(minutes=10),
            id="import_yield_job",
            replace_existing=True,
        )
        logger.info("Job 'import_yield_job' registrado para ejecutarse cada 10 minutos.")

        # Iniciar el scheduler
        scheduler.start()
        logger.info("Scheduler iniciado correctamente.")
    except Exception as e:
        logger.error(f"Error al iniciar el scheduler: {e}")

def import_mes_job():
    """
    Ejecuta el comando para importar datos de MES desde el CSV.
    """
    try:
        logger.info("Ejecutando job 'import_mes_job'...")
        call_command('import_mes')
        logger.info("Job 'import_mes_job' ejecutado correctamente.")
    except Exception as e:
        logger.error(f"Error en el job 'import_mes_job': {e}")

def import_mqs_job():
    """
    Ejecuta el comando para importar datos de MQS desde el CSV.
    """
    try:
        logger.info("Ejecutando job 'import_mqs_job'...")
        call_command('import_mqs_csv')
        logger.info("Job 'import_mqs_job' ejecutado correctamente.")
    except Exception as e:
        logger.error(f"Error en el job 'import_mqs_job': {e}")

def import_yield_job():
    """
    Ejecuta el comando para importar datos de YieldTurno desde el CSV.
    """
    try:
        logger.info("Ejecutando job 'import_yield_job'...")
        call_command('import_yield_csv')
        logger.info("Job 'import_yield_job' ejecutado correctamente.")
    except Exception as e:
        logger.error(f"Error en el job 'import_yield_job': {e}")