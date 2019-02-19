from urllib.parse import urlencode, urljoin

import requests


def url_join_with_params(base, url, params):
    params = urlencode(params)
    url_new = urljoin(base, url)
    return '{url}?{params}'.format(url=url_new, params=params)


class PratoAbertoApiClient(object):
    # TODO get os environ
    API_URL = 'http://localhost:8000/'

    def get_escola_by_eol_code(self, cod_eol):
        url = urljoin(self.API_URL, 'escola')
        r = requests.get(urljoin(url, cod_eol))
        return r.json()

    def get_cardapio(self, id_escola, idade, data):
        #TODO o que é data?
        query_args = {'idade': idade}
        url = '{}/escola/{}/cardapios'.format(self.API_URL, id_escola)
        url = url_join_with_params(base=url, url=data, params=query_args)
        r = requests.get(url)
        return r.json()

    def find_escolas_by_name(self, nome):
        query_params = {'nome': nome,
                        'limit': 4}
        url = url_join_with_params(base=self.API_URL, url='escolas', params=query_params)
        r = requests.get(url)
        return r.json()

