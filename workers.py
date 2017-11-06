# -*- coding: utf-8 -*-
import calendar
import time

from celery import Celery

import app_config
import message_handlers
import mongocon
import workflow

_get_epoch = lambda: calendar.timegm(time.localtime())

# configura Celery object
app = Celery(app_config.APP_NAME)
app.config_from_object('app_config')

# obtem uma conexao ao banco
db = mongocon.new_client()

@app.task
def process_message(update):
    # menu principal
    botoes = workflow.menu_principal
    # obtem argumentos da mensagem
    source = update['source']
    chat_processor, chat_dispatcher = message_handlers.processors[source], message_handlers.dispatchers[source]
    texto, chat_id = chat_processor(update['data'])

    query = {'chat_id': chat_id, 'status': 'aberto'}
    # carrega estado do chat e define fluxo
    chat = db.interacoes.find_one(query)
    if not chat:
        # novo fluxo
        # import rpdb; rpdb.set_trace()
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
            chat_dispatcher(chat_id, resposta, botoes)
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
            db.interacoes.replace_one(query, chat, upsert=True)
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
            db.interacoes.replace_one(query, chat)

    chat_dispatcher(chat_id, resposta, botoes)
    return {
        'chat_id': chat_id,
        'texto': resposta,
        'botoes': botoes
    }
