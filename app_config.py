# -*- coding: utf-8 -*-
# workers app configuration file
import configparser

# arquivo properties
config = configparser.ConfigParser()
config.read('conf/bot.conf')

# flask app
APP_NAME = 'educassis'

# mongo conf
MONGO_URL = 'mongodb://{}:{}'.format(config.get('ENDPOINTS', 'MONGO_HOST'),
									 config.get('ENDPOINTS', 'MONGO_PORT'))

# celery conf
# http://docs.celeryproject.org/en/latest/userguide/configuration.html
BROKER_URL = config.get('ENDPOINTS', 'BROKER_URL')
CELERY_RESULT_BACKEND = 'mongodb'
CELERY_MONGODB_BACKEND_SETTINGS = {
    'host': config.get('ENDPOINTS', 'MONGO_HOST'),
    'port': config.getint('ENDPOINTS', 'MONGO_PORT'),
    'database': APP_NAME,
    'taskmeta_collection': 'messages_meta',
}
CELERY_ENABLE_UTC = False
CELERY_TIMEZONE = 'America/Sao_Paulo'


# tokens
TG_TOKEN = config.get('TOKENS', 'TG_TOKEN')
FB_VERIFY_TOKEN = config.get('TOKENS', 'FB_VERIFY_TOKEN')
FB_TOKEN = config.get('TOKENS', 'FB_TOKEN')

# chat platforms urls
TG_URL = 'https://api.telegram.org/bot{}/'.format(TG_TOKEN)
TG_BASE_MESSAGE_URL = TG_URL + 'sendMessage?chat_id={}&text={}&parse_mode=Markdown'
FB_URL = 'https://graph.facebook.com/v2.6/me/messages/?access_token={}'.format(FB_TOKEN)


# pratoaberto api urls
API_URL = config.get('ENDPOINTS', 'API_URL')
URI_ESCOLAS = 'escolas'
URI_ESCOLA = 'escola/{}'
URI_CARDAPIOS = 'cardapios/{}'


# flower configs, see docs at
# https://flower.readthedocs.io/en/latest/config.html
broker_api = config.get('FLOWER', 'BROKER_API')
url_prefix = config.get('FLOWER', 'URL_PREFIX')
basic_auth = [config.get('FLOWER', 'BASIC_AUTH')]
