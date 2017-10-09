# -*- coding: utf-8 -*-
import io
import json
import pprint

from datetime import date
from celery.utils.log import get_task_logger

import api_client as api
from mongocon import db

logger = get_task_logger(__name__)

# carrega workflows
with io.open('conf/workflowsconfig.json', 'r', encoding='utf-8') as f:
    workflows = json.load(f)
    # constroi dicionario com a mensagem como chave
    # for platform, fl in workflows['flows'].items()
    fluxos, mensagens = workflows['fluxos'], workflows['mensagens']
    main_menu = [a for a, b in sorted([x for x in fluxos.items() if x[1]['menu']],
                                        key=lambda x: x[1].get('ordem'))]


def _format(text, args=list()):
    return '\n\n'.join(text).format(*args)


# processadores
# @return: text_mask, text_args, keyboard
def process_cardapio(chat):
    escola, idade, data = chat['valores']
    # converte opcoes de data
    _hoje = date.today().strftime('%Y%m%d')
    data = int(_hoje) + 1*(data=='Amanhã') - 1*(data=='Ontem')
    # busca cardapio
    cardapio = api.get_cardapio(escola, idade, data)
    # processa resposta
    if len(cardapio) > 0:
        cardapio = cardapio.pop()
        cardapio_str = ['{}:\n{}'.format(k, ', '.join(v)) for (k, v) in sorted(cardapio['cardapio'].items())]
    else:
        cardapio_str = ['Ops! Não encontramos nenhuma informação de cardápio para este dia.']

    resposta = fluxos[chat['fluxo']]['resposta']
    args = (escola['nome'], idade, _format(cardapio_str))
    return _format(resposta, args), main_menu

def process_avaliacao(chat):
    id_escola, idade, data, nota, comentario = chat['valores']
    return _format(fluxos[chat['fluxo']]['resposta']), main_menu

def process_notificacao(chat):
    id_escola, idade = chat['valores']
    return _format(fluxos[chat['fluxo']]['resposta']), main_menu

def process_votacao(chat):
    voto = chat['valores']
    resposta = fluxos[chat['fluxo']]['resposta']
    return _format(resposta, voto), main_menu


# construtores de argumentos
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

    logger.debug(pprint.pformat(chat))
    logger.debug('out:process_arguments')
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
        escolas = api.find_escolas(texto)
        if len(escolas) == 0:
            msg = mensagens['escola_nenhuma_opcao']
            chat['resposta'] = _format(msg['texto'])
        else:
            botoes = [c['nome'] for c in escolas]
            if texto in botoes:
                _id = escolas[botoes.index(texto)]['_id']
                escola = api.get_escola(_id)
                chat = _update_arg(chat, escola)
            else:
                msg = mensagens['escola_confirm']
                chat.update({
                    'resposta': _format(msg['texto']),
                    'botoes': sorted(botoes) + ['Nenhuma das opções']
                })

    return chat

def _get_idade(chat, texto):
    escola = chat['valores'][0]
    botoes = sorted([c for c in escola['idades']])
    if texto or len(botoes) == 1:
        chat = _update_arg(chat, texto or botoes[0])
    else:
        chat['botoes'] = botoes

    return chat

def _get_comentario_confirm(chat, texto):
    # import rpdb; rpdb.set_trace()
    _arg_status = chat.get('sub_status', 0)
    if not _arg_status:
        chat['sub_status'] = 1
    elif texto == 'Sim':
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
    print(fns)
