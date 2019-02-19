# -*- coding: utf-8 -*-
import json
import requests
from urllib.parse import urlencode

from celeryconfig import API_URL, ENDPOINT_ESCOLAS, ENDPOINT_ESCOLA, ENDPOINT_CARDAPIOS

def api_call(endpoint, kwargs=dict()):
    url = '{}{}?{}'.format(API_URL, endpoint, urlencode(kwargs))
    response = requests.get(url)
    content = response.content.decode('utf8')
    return json.loads(content)

def find_escolas(query):
    query_args = {
        'nome': query,
        'limit': 4
    }
    endpoint = ENDPOINT_ESCOLAS
    return api_call(endpoint, query_args)

def get_escola(id_escola):
    endpoint = ENDPOINT_ESCOLA.format(id_escola)
    return api_call(endpoint)

def get_cardapio(id_escola, idade, data):
    query_args = {
        'idade': idade
    }
    endpoint = ENDPOINT_CARDAPIOS.format(id_escola, data)
    return api_call(endpoint, query_args)
