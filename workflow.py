# -*- coding: utf-8 -*-
import io
import json

# carrega workflows
with io.open('workflowsconfig.json', 'r', encoding='utf-8') as f:
    workflows = json.load(f)
    # constroi dicionario com a mensagem como chave
    # for platform, fl in workflows['flows'].items()
    flows, messages = workflows['flows'], workflows['messages']
    cardapio = workflows['cardapio']
    default_buttons = [a for a, b in sorted([x for x in flows.items() if x[1]['button']], key=lambda x: x[1].get('order'))]


def _format(text, *args):
    return '\n\n'.join(text).format(*(args or []))

# processadores
# @return: text_mask, text_args, keyboard
def process_cardapio(chat):
    id_escola, idade, data = chat['values']
    return _format(flows[chat['flow']]['reply'], id_escola, _format(cardapio[id_escola][idade])), default_buttons

def process_avaliacao(chat):
    id_escola, idade, data, nota, comentario = chat['values']
    return _format(flows[chat['flow']]['reply']), default_buttons

def process_notificacao(chat):
    id_escola, idade = chat['values']
    return _format(flows[chat['flow']]['reply']), default_buttons

processors = {
    name.replace('process_', ''): fn
    for name, fn in locals().items()
    if name.startswith('process_')
}


# construtores de argumentos
def get_id_escola(chat):
    pass

def get_idade(chat):
    pass

def get_data(chat):
    pass

def get_nota(chat):
    pass

def get_comentario(chat):
    pass


if __name__ == '__main__':
    print(fns)

