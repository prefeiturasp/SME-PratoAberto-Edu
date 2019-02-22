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
    API_URL = 'https://pratoaberto.sme.prefeitura.sp.gov.br/api/'
    headers = {
        'User-Agent':
            'Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
    }

    def _base_request(self, url):
        r = requests.get(url, headers=self.headers)
        print(url)
        return r.json()

    def get_escola_by_eol_code(self, cod_eol):
        url = urljoin(self.API_URL, 'escola/')
        return self._base_request(urljoin(url, str(cod_eol)))

    def get_cardapio(self, age, menu_date, school):
        """
        :param school:
        :param query_args: um dict que vai como parametro de busca nos
        cardapios de uma escola. Ex: query_args = {
                                                'idade': idade,
                                                'data_inicial': '',
                                                'data_final': ''}
        :return:
        """
        query_args = {
            'tipo_unidade': school['tipo_unidade'],
            'tipo_atendimento': school['tipo_atendimento'],
            'agrupamento': school['agrupamento'],
            'idade': age
        }
        url = '{}/cardapios/'.format(self.API_URL)
        url = url_join_with_params(base=url, url=menu_date, params=query_args)
        return self._base_request(url)

    def get_escolas_by_name(self, nome):
        query_params = {'nome': nome,
                        'limit': 5}
        url = url_join_with_params(base=self.API_URL, url='escolas', params=query_params)
        return self._base_request(url)

    def get_idades_by_escola_nome(self, nome):
        """Aqui espera-se receber o nome completo da escola"""
        # XXX: foi necessário fazer isso para receber os "relacionamentos" de dados
        idades = []
        try:
            escola = self.get_escolas_by_name(nome)
            escola = escola[0]
            cod_eol = escola['_id']
            url = '{}/escola/{}'.format(self.API_URL, cod_eol)
            url += '/cardapios'
            retval = self._base_request(url)
            for i in retval:
                if i['idade'] not in idades:
                    idades.append(i['idade'])
        except IndexError as e:
            pass
        return idades
