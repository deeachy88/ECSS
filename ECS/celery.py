# ECS/ECS/celery.py

import os
from celery import Celery

# ✅ Point to your Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ECS.settings')

app = Celery('ECS')

# ✅ Load celery config from Django settings (keys starting with CELERY_)
app.config_from_object('django.conf:settings', namespace='CELERY')

# ✅ Auto-discover tasks from all INSTALLED_APPS
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
