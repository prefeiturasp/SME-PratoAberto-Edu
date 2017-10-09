# -*- coding: utf-8 -*-
import json
import requests

from urllib.parse import urlencode
from app_config import API_URL, URI_ESCOLAS, URI_ESCOLA, URI_CARDAPIOS


def get_url(uri, kwargs=dict()):
    url = '{}{}?{}'.format(API_URL, uri, urlencode(kwargs))
    print(url)
    response = requests.get(url)
    content = response.content.decode("utf8")
    return json.loads(content)

def find_escolas(query):
    query_args = {
        'nome': query,
        'limit': 4
    }
    return get_url(URI_ESCOLAS, query_args)

def get_escola(query):
    url = URI_ESCOLA.format(query)
    return get_url(url)

def get_cardapio(escola, idade, data):
    query = {
        # 'status': 'PUBLICADO',
        # 'idade': idade,
        # 'agrupamento': escola['agrupamento'],
        # 'tipo_unidade': escola['tipo_unidade'],
        # 'tipo_atendimento': escola['tipo_atendimento']
    }
    url = URI_CARDAPIOS.format(data)
    return get_url(url, query)
