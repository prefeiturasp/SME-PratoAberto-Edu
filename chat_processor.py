# -*- coding: utf-8 -*-
import calendar
import pprint
import time

from datetime import date

from celery import Celery
from celery.utils.log import get_task_logger
from celery.signals import worker_process_init, worker_process_shutdown

import chat_platforms
import mongocon
import workflow

from app_config import APP_NAME


_get_epoch = lambda: calendar.timegm(time.localtime())

# configura Celery object
app = Celery(APP_NAME)
app.config_from_object('app_config')

logger = get_task_logger(__name__)

db = None


@worker_process_init.connect
def init_worker(**kwargs):
    global db
    print('Initializing database connection for worker.')
    db = mongocon.new_client()
    # testa conexão
    try:
        db.status
        print('Connection successful')
    except:
        print('mongo seems to be down!')

@worker_process_shutdown.connect
def shutdown_worker(**kwargs):
    global db
    if db:
        print('Closing database connectionn for worker.')
        db.client.close()


@app.task
def process_subscriptions():
    # obtem usuarios cadastrados para notificacao
    cursor = db.users.find({'subscription': {'$exists': True}})
    for c in cursor:
        chat_id = c['_id']
        source = c['source']
        # constroi argumentos
        ecola, idade = c['subscription']
        valores = c['subscription'] + [int(date.today().strftime('%Y%m%d')), ]

        # carrega fluxo e gera chat
        _fluxo_cardapio = 'Qual o cardápio?'
        fluxo = workflow.fluxos[_fluxo_cardapio]
        # gera mensagem
        chat = {
            'chat_id': chat_id,
            'id_fluxo': fluxo['_id_fluxo'],
            'fluxo': _fluxo_cardapio,
            'argumentos': fluxo['argumentos'],
            'valores': valores
        }
        _fn = workflow.processors[fluxo['_id_fluxo']]
        resposta, _ = _fn(chat, db)
        # salva notificacao
        chat = {
            'chat_id': chat_id,
            'id_fluxo': 'notificao',
            'valores': dict(zip(fluxo['argumentos'], valores)),
            'resposta': resposta,
            'timestamp': _get_epoch(),
            'status': 'sucesso'
        }
        db.chats.insert_one(chat)

        resposta = workflow._format(workflow.mensagens['notificacao']['texto'],
                                    (c['nome'], resposta))

        _dispatch_message(source, chat_id, resposta, workflow.menu_subscritos, priority=0)

    return {
        'notificacoes': cursor.count()
    }


@app.task()
def process_message(**kwargs):
    # configura handlers da plataforma
    source = kwargs['source']
    chat_processor = chat_platforms.processors[source]
    chat_username = chat_platforms.usernames[source]

    # obtem argumentos da mensagem
    texto, chat_id = chat_processor(kwargs['data'])

    # atualiza info usuario
    query = { '_id': chat_id }
    user = db.users.find_one(query)
    if not user:
        user_info = {
            'nome': chat_username(kwargs['data']),
            'source': source
        }
        db.users.update_one(query, { '$set': user_info }, upsert=True)
        user = query
        user.update(user_info)

    # carrega estado do chat e define fluxo
    query = {'chat_id': chat_id, 'status': 'aberto'}
    chat = db.chats.find_one(query)
    if not chat:
        _fluxo = workflow.fluxos.get(texto, workflow.fluxos['default'])
        chat = dict(query)
        # novo fluxo
        try:
            _id_fluxo = _fluxo['_id_fluxo']
            args = _fluxo['argumentos']
            chat.update({
                'id_fluxo': _id_fluxo,
                'fluxo': texto,
                'argumentos': args,
                'arg_corrente': args[0],
                'valores': [None]*len(args),
                'timestamp': _get_epoch()
            })
        except KeyError:
            # fluxo sem argumentos, basta responder
            return _finally_process_message(user, _fluxo, chat)

    # processa texto
    _fluxo = workflow.fluxos.get(chat['fluxo'])
    resposta, botoes = None, None
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
            logger.debug('args completed:')
            logger.debug(pprint.pformat(chat))
            return _finally_process_message(user, _fluxo, chat)

    return _dispatch_message(source, chat_id, resposta, botoes)


def _finally_process_message(user, fluxo, chat):
    # perfil usuario
    source = user['source']
    chat_id = user['_id']
    # menu principal padrão
    if 'subscription' in user:
        menu_padrao = workflow.menu_subscritos
    else:
        menu_padrao = workflow.menu_principal

    resposta, botoes = None, None
    try:
        _fn = workflow.processors[fluxo['_id_fluxo']]
        resposta, botoes = _fn(chat, db)
    except:
        # função não existe
        pass

    botoes = botoes or menu_padrao
    resposta = resposta or workflow._format(fluxo['resposta'])

    try:
        # atualiza interacao com a ultima resposta
        chat = {
            'chat_id': chat['chat_id'],
            'id_fluxo': chat['id_fluxo'],
            'valores': dict(zip(chat['argumentos'], chat['valores'])),
            'resposta': resposta,
            'timestamp': _get_epoch(),
            'status': 'sucesso'
        }
        query = {'chat_id': chat_id, 'status': 'aberto'}
        db.chats.replace_one(query, chat)
    except Exception as e:
        # chat é incompleto, desconsiderar
        logger.debug(e)
        pass

    return _dispatch_message(source, chat_id, resposta, botoes)


def _dispatch_message(source, chat_id, resposta, botoes, priority=1):
    dispatcher_args = (chat_id, resposta, botoes)

    chat_dispatcher = chat_platforms.dispatchers[source]
    chat_dispatcher.apply_async(args=dispatcher_args, priority=priority)

    return {
        'chat_id': chat_id,
        'texto': resposta,
        'botoes': botoes
    }
