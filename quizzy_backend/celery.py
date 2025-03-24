import multiprocessing as mp

try:
    mp.set_start_method("spawn", force=True)
except RuntimeError:
    pass  # Already set

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quizzy_backend.settings")

app = Celery("quizzy_backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
