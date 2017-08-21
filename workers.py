from __future__ import absolute_import

import json
import time
import urllib
import requests

from celery import Celery
from pymongo import MongoClient

# import logic_workflow as lw
from botconfig import *
import workflow


# configura Celery object
app = Celery(APP_NAME)
app.config_from_object('celeryconfig')

# configura Mongo client
client = MongoClient(MONGO_URL)
chats = client[APP_NAME][MONGO_CHAT_COLLECTION]


def _tg_payload(payload):
    chat_id = payload['message']['chat']['id']
    text = payload['message']['text']
    return text, chat_id

def _fb_payload(payload):
    sender_id = payload['entry'][0]['messaging'][0]['sender']['id']
    try:
        text = payload['entry'][0]['messaging'][0]['message']['text']
    except KeyError:
        text = payload['entry'][0]['messaging'][0]['postback']['payload']
    return text, sender_id

def _tg_dispatch(chat_id, text, keyboard=None):
    # codifica mensagem para url
    text = urllib.parse.quote_plus(text)
    # constroi url
    url = TG_BASE_MESSAGE_URL.format(chat_id, text)
    if keyboard:
        keyboard = [[item] for item in keyboard]
        reply_markup = {'keyboard': keyboard, 'one_time_keyboard': True}
        url += '&reply_markup={}'.format(json.dumps(reply_markup))
    # envia requisicao para plataforma de chat
    requests.get(url)

def _fb_dispatch(chat_id, text, keyboard=None):
    payload = {
        'recipient': {'id': chat_id},
        'message': {
            'attachment': {
                'type': 'template',
                'payload': {
                    'template_type': 'button',
                    'text': text,
                    'buttons': [{
                        'type': 'postback',
                        'title': item,
                        'payload': item
                    } for item in keyboard] if keyboard else []
                }
            }
        }
    }
    # envia requisicao para plataforma de chat
    requests.post(FB_URL, json=payload)


_payload_processors = {
    'telegram': _tg_payload,
    'facebook': _fb_payload
}

_msg_dispatchers = {
    'telegram': _tg_dispatch,
    'facebook': _fb_dispatch
}


@app.task
def process_message(update):
    # import pudb; pu.db
    keyboard = workflow.default_buttons
    # obtem argumentos da mensagem
    source = update['source']
    processor, dispatcher = _payload_processors[source], _msg_dispatchers[source]
    text, chat_id = processor(update['data'])

    _filter = {'_id': chat_id}
    # carrega estado do chat e define fluxo
    chat = chats.find_one(_filter)
    try:
        _flow = chat['flow_id']
        curr_arg = chat['current_arg']
        args = chat['arguments']
        values = chat['values']
        # salva resposta
        # TO-DO: respostas podem requerer processamento extra, que pode ser delegado para uma fn em workflow
        values[args.index(curr_arg)] = text
    except:
        # novo fluxo
        _flow = workflow.flows[text]
        try:
            args = _flow['arguments']
            values = [None]*len(args)
            chat = {
                '_id': chat_id,
                'flow': text,
                'flow_id': _flow['flow_id'],
                'arguments': args,
                'values': values
            }
        except KeyError:
            # fluxo sem argumentos, basta responder
            reply = workflow._format(_flow['reply'])
            dispatcher(chat_id, reply, keyboard)
            return {
                'chat_id': chat_id,
                'text': reply,
                'keyboard': keyboard
            }

    try:
        # continua construcao de argumentos
        next_arg = args[values.index(None)]
        msg = workflow.messages[next_arg]
        reply, keyboard = workflow._format(msg['text']), msg['options']
        # persiste estado do caht
        chat.update({'current_arg': next_arg})
        chats.replace_one(_filter, chat, upsert=True)
    except ValueError:
        # argumentos estao completos
        chats.delete_one(_filter)
        # delega logica para os processadores de fluxo
        fn = workflow.processors[_flow]
        reply, keyboard = fn(chat)

    dispatcher(chat_id, reply, keyboard)
    return {
        'chat_id': chat_id,
        'text': reply,
        'keyboard': keyboard
    }


if __name__ == '__main__':
    app.start()
