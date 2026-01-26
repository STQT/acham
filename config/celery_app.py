import os

from celery import Celery
from celery.schedules import crontab
from celery.signals import setup_logging

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("acham")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")


@setup_logging.connect
def config_loggers(*args, **kwargs):
    from logging.config import dictConfig  # noqa: PLC0415

    from django.conf import settings  # noqa: PLC0415

    dictConfig(settings.LOGGING)


# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    "update-currency-rates": {
        "task": "acham.orders.tasks.update_currency_rates",
        "schedule": crontab(hour=9, minute=0),  # Run daily at 9:00 AM Tashkent time
    },
    "check-pending-orders": {
        "task": "acham.orders.tasks.check_pending_orders",
        "schedule": crontab(minute="*/30"),  # Run every 30 minutes
    },
}
