# -*- coding: utf-8 -*-
import calendar
import time

from celery import Celery

import chat_handlers
import mongocon
import workflow

from app_config import APP_NAME


# configura Celery object
app = Celery(APP_NAME)
app.config_from_object('app_config')

# obtem uma conexao ao banco
db = mongocon.new_client()


_get_epoch = lambda: calendar.timegm(time.localtime())

@app.task
def process_message(update):
    # menu principal
    botoes = workflow.menu_principal
    # obtem argumentos da mensagem
    source = update['source']
    chat_processor = chat_handlers.processors[source]
    chat_dispatcher = chat_handlers.dispatchers[source]
    chat_username = chat_handlers.usernames[source]
    texto, chat_id = chat_processor(update['data'])

    # atualiza info usuario
    query = { '_id': chat_id }
    user = db.users.find_one(query)
    if not user:
        payload = {
            'nome': chat_username(update['data']),
            'source': source
        }
        user = db.users.update_one(query, { '$set': payload }, upsert=True)

    # carrega estado do chat e define fluxo
    query = {'chat_id': chat_id, 'status': 'aberto'}
    chat = db.chats.find_one(query)
    if not chat:
        # novo fluxo
        _fluxo = workflow.fluxos.get(texto.capitalize(), workflow.fluxos['default'])
        try:
            args = _fluxo['argumentos']
            chat = {
                'chat_id': chat_id,
                'id_fluxo': _fluxo['_id_fluxo'],
                'fluxo': texto.capitalize(),
                'argumentos': args,
                'arg_corrente': args[0],
                'valores': [None]*len(args),
                'status': 'aberto',
                'timestamp': _get_epoch()
            }
        except KeyError:
            # fluxo sem argumentos, basta responder
            resposta = workflow._format(_fluxo['resposta'])
            chat_dispatcher.delay(chat_id, resposta, botoes)
            return {
                'chat_id': chat_id,
                'texto': resposta,
                'botoes': botoes
            }

    # processa texto
    resposta = None
    while not resposta:
        try:
            chat = workflow.process_arguments(chat, texto)
            resposta, botoes = chat['resposta'], chat['botoes']
            # persiste estado do chat
            chat['timestamp'] = _get_epoch()
            db.chats.replace_one(query, chat, upsert=True)
            texto = None
        except ValueError:
            # argumentos estao completos
            _id_fluxo = chat['id_fluxo']
            _fn = workflow.processors[_id_fluxo]
            resposta, botoes = _fn(chat)
            # atualiza interacao com a ultima resposta
            chat = {
                '_id': chat['_id'],
                'chat_id': chat['chat_id'],
                'id_fluxo': chat['id_fluxo'],
                'valores': dict(zip(chat['argumentos'], chat['valores'])),
                'resposta': resposta,
                'timestamp': _get_epoch(),
                'status': 'sucesso'
            }
            db.chats.replace_one(query, chat)

    chat_dispatcher.delay(chat_id, resposta, botoes)
    return {
        'chat_id': chat_id,
        'texto': resposta,
        'botoes': botoes
    }
