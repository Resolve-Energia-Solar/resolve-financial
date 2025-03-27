from celery import shared_task
import requests
import logging

logger = logging.getLogger(__name__)