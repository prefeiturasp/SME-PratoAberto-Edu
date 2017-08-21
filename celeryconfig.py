# celery config file, see docs at
# http://docs.celeryproject.org/en/latest/userguide/configuration.html

BROKER_URL = 'pyamqp://localhost//'

CELERY_RESULT_BACKEND = "mongodb"
CELERY_MONGODB_BACKEND_SETTINGS = {
    "host": "127.0.0.1",
    "port": 27017,
    "database": "educassis",
    "taskmeta_collection": "messages_meta",
}

CELERY_ENABLE_UTC = False
CELERY_TIMEZONE = 'Americas/Sao_Paulo'
