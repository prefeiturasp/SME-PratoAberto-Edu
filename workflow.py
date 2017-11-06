# -*- coding: utf-8 -*-
import calendar
import io
import json
import pprint
import time
from datetime import date

from celery.utils.log import get_task_logger

import api_client as api
import mongocon

logger = get_task_logger(__name__)
db = mongocon.new_client()

# carrega workflows
with io.open('conf/workflowsconfig.json', 'r', encoding='utf-8') as f:
    workflows = json.load(f)
    # constroi dicionario com a mensagem como chave
    fluxos, mensagens = workflows['fluxos'], workflows['mensagens']
    menu_principal = [a for (a, b) in sorted([x for x in fluxos.items() if x[1]['menu']],
                                             key=lambda x: x[1].get('ordem'))]


def _format(text, args=list()):
    return '\n\n'.join(text).format(*args)


# processadores
# @return: resposta, botoes
def process_cardapio(chat):
    escola, idade, data = chat['valores']
    # busca cardapio
    try:
        cardapio = api.get_cardapio(escola['_id'], idade, data)
    except:
        # erro na API
        return _format(mensagens['erro_api']['texto']), menu_principal

    # processa resposta
    if len(cardapio) > 0:
        cardapio = cardapio.pop()
        cardapio_str = ['{}:\n{}'.format(k, ', '.join(v)) for (k, v) in sorted(cardapio['cardapio'].items())]
    else:
        cardapio_str = ['Ops! Não encontramos nenhuma informação de cardápio para este dia.']

    resposta = fluxos[chat['fluxo']]['resposta']
    args = (escola['nome'], idade, _format(cardapio_str))
    return _format(resposta, args), menu_principal

def process_avaliacao(chat):
    return _format(fluxos[chat['fluxo']]['resposta']), menu_principal

def process_notificacao(chat):
    id_escola, idade = chat['valores']

    # salva interacao
    key = { 'id_chat': chat['_id'] }
    registro_interacao = {
        'cod_eol': escola['cod_eol'],
        'idade': escola['idade']
    }
    db.notificoes.update(key, registro_interacao, upsert=True)

    return _format(fluxos[chat['fluxo']]['resposta']), menu_principal


# construtores de argumentos
# @return: chat
def process_arguments(chat, texto):
    logger.debug('in:process_arguments: {}'.format(texto))
    logger.debug(pprint.pformat(chat))

    # import rpdb; rpdb.set_trace()
    _arg_corrente = chat['arg_corrente']

    msg = mensagens.get(_arg_corrente, dict())
    chat.update({
        'resposta': _format(msg.get('texto')),
        'botoes': msg.get('opcoes')
    })

    try:
        _fn = getters[_arg_corrente]
        chat = _fn(chat, texto)
    except KeyError:
        if texto:
            chat = _update_arg(chat, texto)

    logger.debug('out:process_arguments')
    logger.debug(pprint.pformat(chat))
    return chat

def _update_arg(chat, valor):
    # atualiza argumentos
    arg_corrente = chat['arg_corrente']

    args = chat['argumentos']
    valores = chat['valores']
    valores[args.index(arg_corrente)] = valor
    # define proximo argumento
    chat.update({
            'valores': valores,
            'arg_corrente': args[valores.index(None)],
            'resposta': None,
            'sub_status': None
        })
    # quando nao houver mais argumentos a ser preenchidos,
    # args[valores.index(None)] lancara ValueError
    return chat

def _get_escola(chat, texto):
    # procura pela escola
    _arg_status = chat.get('sub_status', 0)
    if not _arg_status or texto == 'Nenhuma das opções':
        chat['sub_status'] = 1
    else:
        resposta, botoes = None, None
        try:
            escolas = api.find_escolas(texto)
        except:
            # erro na API
            chat.update({
                'resposta': _format(mensagens['erro_api']['texto']),
                'botoes': menu_principal,
                'status': 'erro'
            })
            return chat

        if len(escolas) == 0:
            msg = mensagens['escola_invalida']
            chat['resposta'] = _format(msg['texto'])
        else:
            texto = texto.upper()
            botoes = [c['nome'] for c in escolas]
            if texto in botoes:
                escola = escolas[botoes.index(texto)]
                chat = _update_arg(chat, escola)
                # obtem dados da escola para uso futuro
                try:
                    escola = api.get_escola(escola['_id'])
                    chat['escola'] = escola
                except:
                    # erro na API
                    chat.update({
                        'resposta': _format(mensagens['erro_api']['texto']),
                        'botoes': menu_principal,
                        'status': 'erro'
                    })
                    return chat
            else:
                msg = mensagens['escola_confirm']
                chat.update({
                    'resposta': _format(msg['texto']),
                    'botoes': sorted(botoes) + ['Nenhuma das opções']
                })

    return chat

def _get_idade(chat, texto):
    if texto:
        chat = _update_arg(chat, texto.upper())
    else:
        escola = chat['escola']
        botoes = sorted([c for c in escola['idades']])
        if len(botoes) == 1:
            chat = _update_arg(chat, botoes[0])
        else:
            chat['botoes'] = botoes

    return chat

def _get_data(chat, texto):
    if texto:
        _hoje = date.today().strftime('%Y%m%d')
        data = int(_hoje) + 1*(texto=='amanhã') - 1*(texto=='ontem')
        chat = _update_arg(chat, data)
    return chat

def _get_data_cardapio(chat, texto):
    return _get_data(chat, texto)

def _get_data_avaliacao(chat, texto):
    return _get_data(chat, texto)

def _get_refeicao_preferida(chat, texto):
    if texto:
        chat = _update_arg(chat, texto.upper())
    else:
        escola = chat['escola']
        chat['botoes'] = sorted([c for c in escola['refeicoes']])

    return chat

def _get_comentario_confirm(chat, texto):
    # import rpdb; rpdb.set_trace()
    _arg_status = chat.get('sub_status', 0)
    if not _arg_status:
        chat['sub_status'] = 1
    elif texto == 'sim':
        msg = mensagens['comentario']
        chat.update({
            'resposta': _format(msg['texto']),
            'botoes': None
        })
    else:
        chat = _update_arg(chat, texto)
    return chat


processors = {
    name.replace('process_', ''): fn
    for name, fn in locals().items()
    if name.startswith('process_')
}

getters = {
    name.replace('_get_', ''): fn
    for name, fn in locals().items()
    if name.startswith('_get_')
}

if __name__ == '__main__':
    print(processors)
    print(getters)
