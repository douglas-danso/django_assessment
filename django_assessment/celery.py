from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_assessment.settings')

app = Celery('django_assessment')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


