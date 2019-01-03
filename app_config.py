# -*- coding: utf-8 -*-
import configparser

from celery.schedules import crontab

# arquivo propriedades
config = configparser.ConfigParser()
config.read('conf/bot.conf')

# flask app
APP_NAME = 'edu'

# tokens
TG_TOKEN = config.get('TOKENS', 'TG_TOKEN')
FB_VERIFY_TOKEN = config.get('TOKENS', 'FB_VERIFY_TOKEN')
FB_TOKEN = config.get('TOKENS', 'FB_TOKEN')

# URLs plataforma de chat
TG_URL = 'https://api.telegram.org/bot{}/'.format(TG_TOKEN)
TG_BASE_MESSAGE_URL = TG_URL + 'sendMessage?chat_id={}&text={}&parse_mode=Markdown'
FB_URL = 'https://graph.facebook.com/v2.6/me/messages/?access_token={}'.format(FB_TOKEN)
FB_PROFILE_URL = 'https://graph.facebook.com/v2.6/%s?fields=first_name&access_token={}'.format(FB_TOKEN)

# pratoaberto api
API_URL = config.get('ENDPOINTS', 'API_URL')
ENDPOINT_ESCOLAS = 'escolas'
ENDPOINT_ESCOLA = 'escola/{}'
ENDPOINT_CARDAPIOS = 'escola/{}/cardapios/{}'

# mongo
MONGO_HOST = config.get('ENDPOINTS', 'MONGO_HOST')
MONGO_PORT = config.get('ENDPOINTS', 'MONGO_PORT')
MONGO_URL = 'mongodb://{}:{}'.format(MONGO_HOST, MONGO_PORT)

# celery
# http://docs.celeryproject.org/en/latest/userguide/configuration.html
broker_url = config.get('ENDPOINTS', 'broker_url')
result_backend = 'mongodb'
mongodb_backend_settings = {
    'host': MONGO_HOST,
    'port': MONGO_PORT,
    'database': APP_NAME,
    'taskmeta_collection': 'messages_meta',
}
enable_utc = True
timezone = 'America/Sao_Paulo'
task_default_queue = 'messages'
# task_queue_max_priority = 2
task_routes = {
    'chat_processor.process_message': {'queue': 'messages', 'priority': 1, 'x-max-priority': 2},
    'chat_platforms._telegram_dispatch': {'queue': 'telegram', 'retry_backoff': True, 'priority': 1,
                                          'x-max-priority': 2},
    'chat_platforms._facebook_dispatch': {'queue': 'facebook', 'retry_backoff': True, 'priority': 1,
                                          'x-max-priority': 2}
}
task_annotations = {
    'chat_platforms._telegram_dispatch': {'rate_limit': '30/s'},
}
beat_schedule = {
    'subscriptions': {
        'task': 'chat_processor.process_subscriptions',
        # 'schedule': 10.0,
        'schedule': crontab(hour=7, minute=0, day_of_week='mon-fri'),
        'options': {
            'priority': 0
        }
    },
}

# flower
# https://flower.readthedocs.io/en/latest/config.html
broker_api = config.get('FLOWER', 'BROKER_API')
url_prefix = config.get('FLOWER', 'URL_PREFIX')
basic_auth = [config.get('FLOWER', 'BASIC_AUTH')]
