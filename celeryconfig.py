import os

from celery.schedules import crontab

# flask app

APP_NAME = 'edu'

# http://docs.celeryproject.org/en/latest/userguide/configuration.html
broker_url = os.environ.get('BROKER_URL')
result_backend = 'mongodb'
mongodb_backend_settings = {
    'host': os.environ.get('MONGO_HOST'),
    # 'port': MONGO_PORT,
    # 'database': APP_NAME,
    'taskmeta_collection': 'messages_meta',
}
enable_utc = True
timezone = 'America/Sao_Paulo'
task_default_queue = 'messages'
# task_queue_max_priority = 2

beat_schedule = {
    'subscriptions': {
        'task': 'chatbots.subscriptions.process_subscriptions',
        # 'schedule': 10.0,
        'schedule': crontab(hour=15, minute=26, day_of_week='mon-fri'),
        'options': {
            'priority': 0
        }
    },
}
