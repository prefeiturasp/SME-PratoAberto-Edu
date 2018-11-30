# -*- coding: utf-8 -*-
import json
import pprint
import urllib

import requests
from celery import Celery
from celery.utils.log import get_task_logger

from app_config import TG_BASE_MESSAGE_URL, FB_URL, FB_PROFILE_URL

# configura Celery object
app = Celery(__name__)
app.config_from_object('app_config')

logger = get_task_logger(__name__)


# Telegram
def _telegram_payload(payload):
    logger.debug('telegram payload:')
    logger.debug(pprint.pformat(payload))

    chat_id = payload['message']['chat']['id']

    text = payload['message']['text']
    return text.strip(), chat_id


def _telegram_get_name(payload):
    return payload['message']['chat']['first_name']


@app.task(bind=True, name='telegram_dispatch')
def _telegram_dispatch(self, chat_id, text, keyboard=None):
    logger.debug('telegram dispatch self: {}'.format(self))
    # codifica mensagem para url
    text = urllib.parse.quote_plus(text)
    # constroi url
    url = TG_BASE_MESSAGE_URL.format(chat_id, text)
    if keyboard:
        keyboard = [[item] for item in keyboard]
        reply_markup = {'keyboard': keyboard, 'one_time_keyboard': True}
        url += '&reply_markup={}'.format(json.dumps(reply_markup))
    # envia requisicao para plataforma de chat
    r = requests.get(url)

    logger.debug('telegram dispatch:')
    logger.debug(url)
    logger.debug('return: {}-{}'.format(r.status_code, r.text))

    if not r.ok:
        raise self.retry(exc=r.json())

    return r.json()


# Facebook
def _facebook_payload(payload):
    logger.debug('facebook payload:')
    logger.debug(pprint.pformat(payload))

    message = payload['entry'][0]['messaging'][0]

    chat_id = message['sender']['id']

    try:
        _message = message['message']
        try:
            text = _message['quick_reply']['payload']
        except:
            text = _message['text']
    except:
        text = message['postback']['payload']
    return text.strip(), chat_id


def _facebook_get_name(payload):
    message = payload['entry'][0]['messaging'][0]
    chat_id = message['sender']['id']
    try:
        r = requests.get(FB_PROFILE_URL % (chat_id))
        nome = r.json()['first_name']
    except:
        nome = None
    return nome


@app.task(bind=True, name='facebook_dispatch')
def _facebook_dispatch(self, chat_id, text, keyboard=None):
    payload = {
        'recipient': {'id': chat_id},
        'message': {
            'text': text,
        }
    }

    if keyboard:
        max_length = max(map(len, keyboard))
        if max_length >= 20:
            # dada a limitacao de 20 caracteres para botoes
            # enviar uma nova mensagem só com texto, e outra com as opções
            _facebook_dispatch(chat_id, text)
            # constroi a lista com 4 elementos, e o resto como botões secundários
            buttons = keyboard[4:7]
            keyboard = keyboard[:4]
            # constroi payload
            payload['message'] = {
                'attachment': {
                    'type': 'template',
                    'payload': {
                        'template_type': 'list',
                        'top_element_style': 'compact',
                        'elements': [{
                            'title': item,
                            'buttons': [{
                                'type': 'postback',
                                'title': item,
                                'payload': item,
                            }]
                        } for item in keyboard]
                    }
                }
            }
            if buttons:
                payload['message']['attachment']['payload']['buttons'] = [{
                    'type': 'postback',
                    'title': item,
                    'payload': item,
                } for item in buttons]
        else:
            payload['message'] = {
                'text': text,
                'quick_replies': [{
                    'content_type': 'text',
                    'title': item,
                    'payload': item
                } for item in keyboard]
            }

    # envia requisicao para plataforma de chat
    r = requests.post(FB_URL, json=payload)

    logger.debug('facebook dispatch:')
    logger.debug(pprint.pformat(payload))
    logger.debug('return: {}-{}'.format(r.status_code, r.text))

    response = r.json()
    if 'error' in response:
        error = response['error']
        if error['code'] in [1200, 613]:
            exc_msg = '{}: {}'.format(error['code'], error['message'])
            raise self.retry(exc=exc_msg)

    return r.json()


# dicts
services = ['telegram', 'facebook']
processors = {k: globals()['_{}_payload'.format(k)] for k in services}
dispatchers = {k: globals()['_{}_dispatch'.format(k)] for k in services}
usernames = {k: globals()['_{}_get_name'.format(k)] for k in services}
