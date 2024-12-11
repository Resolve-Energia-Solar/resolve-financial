from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Configuração do Django para o Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resolve_erp.settings')
app = Celery('resolve_erp')

# Carrega as configurações do Celery a partir do settings do Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descobre tasks automaticamente em apps registradas
app.autodiscover_tasks()

"""
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
"""