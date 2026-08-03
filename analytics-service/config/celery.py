import os
from infrastructure.jobs.celery_app import app as celery_app

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.set")

__all__ = ("celery_app",)