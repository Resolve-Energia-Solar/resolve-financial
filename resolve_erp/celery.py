from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resolve_erp.settings')
app = Celery("resolve_erp", broker='pyamqp://guest:guest@rabbitmq//')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

shared_task = app.task