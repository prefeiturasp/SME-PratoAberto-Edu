# -*- coding: utf-8 -*-
from celery import Celery

import message_handlers
import workflow

import app_config
from mongocon import db


# configura Celery object
app = Celery(app_config.APP_NAME)
app.config_from_object('app_config')


@app.task
def process_message(update):
    # main menu
    botoes = workflow.main_menu
    # obtem argumentos da mensagem
    source = update['source']
    chat_processor, chat_dispatcher = message_handlers.processors[source], message_handlers.dispatchers[source]
    texto, chat_id = chat_processor(update['data'])

    query = {'_id': chat_id}
    # carrega estado do chat e define fluxo
    chat = db.educassis.chats.find_one(query)
    if not chat:
        # novo fluxo
        # import rpdb; rpdb.set_trace()
        _fluxo = workflow.fluxos.get(texto, workflow.fluxos['default'])
        try:
            args = _fluxo['argumentos']
            chat = {
                '_id': chat_id,
                '_id_fluxo': _fluxo['_id_fluxo'],
                'fluxo': texto,
                'argumentos': args,
                'arg_corrente': args[0],
                'valores': [None]*len(args)
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
            # persiste estado do caht
            db.educassis.chats.replace_one(query, chat, upsert=True)
            texto = None
        except ValueError:
            # argumentos estao completos
            db.educassis.chats.delete_one(query)
            # delega logica para os processadores de fluxo
            _id_fluxo = chat['_id_fluxo']
            _fn = workflow.processors[_id_fluxo]
            resposta, botoes = _fn(chat)

    chat_dispatcher(chat_id, resposta, botoes)
    return {
        'chat_id': chat_id,
        'texto': resposta,
        'botoes': botoes
    }


if __name__ == '__main__':
    app.start()
