from __future__ import absolute_import, unicode_literals
# Garante que o Celery é carregado com o Django
from .celery import app as celery_app

__all__ = ('celery_app',)
