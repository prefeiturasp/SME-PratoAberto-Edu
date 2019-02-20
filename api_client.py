from urllib.parse import urlencode, urljoin

import requests


def url_join_with_params(base, url, params):
    """
    :param base:  http://foo.bar
    :param url:   borbor
    :param params: dict like {limit: 1, name: 'foo'}
    :return:

    http://foo.bar/borbor/?limit=30&name=foo
    """
    params = urlencode(params)
    url_new = urljoin(base, url)
    return '{url}?{params}'.format(url=url_new, params=params)


class PratoAbertoApiClient(object):
    # TODO get os environ
    API_URL = 'http://localhost:8000/'
    headers = {
        'User-Agent':
            'Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
    }

    def _base_request(self, url):
        r = requests.get(url, headers=self.headers)
        return r.json()

    def get_escola_by_eol_code(self, cod_eol):
        url = urljoin(self.API_URL, 'escola')
        return self._base_request(urljoin(url, cod_eol))

    def get_cardapio(self, id_escola, idade, data):
        # TODO o que é data?
        query_args = {'idade': idade}
        url = '{}/escola/{}/cardapios'.format(self.API_URL, id_escola)
        # /escola/<int:id_escola>/cardapios/<data>
        url = url_join_with_params(base=url, url=data, params=query_args)
        return self._base_request(url)

    def get_escolas_by_name(self, nome):
        query_params = {'nome': nome,
                        'limit': 5}
        url = url_join_with_params(base=self.API_URL, url='escolas', params=query_params)
        r = requests.get(url)
        return self._base_request(url)
