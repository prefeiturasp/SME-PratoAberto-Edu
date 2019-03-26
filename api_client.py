import logging
import os
from urllib.parse import urlencode, urljoin

import requests

log = logging.getLogger(__name__)


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
    """
    A facade class to consume api from prato aberto
    """
    headers = {
        'User-Agent':
            'Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
    }

    def __init__(self):
        self.API_URL = os.environ.get('API_URL')

    def get_school_by_eol_code(self, cod_eol):
        url = urljoin(self.API_URL, 'escola/')
        return self._base_request(urljoin(url, str(cod_eol)))

    def get_menu(self, age, menu_date, school):
        """
        :param age: str
        :param menu_date: str YYYYMMDD
        :param school: dict
        :return: array with menu data
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

    def get_schools_by_name(self, nome):
        query_params = {'nome': nome,
                        'limit': 5}
        url = url_join_with_params(base=self.API_URL, url='escolas', params=query_params)
        return self._base_request(url)

    def get_ages_by_school_nome(self, name):
        """
        :param name: school name 
        :return: array of str
        """
        # XXX: because of poor REST API
        ages_list = []
        try:
            schools = self.get_schools_by_name(name)
            schools = schools[0]
            cod_eol = schools['_id']
            url = '{}/escola/{}'.format(self.API_URL, cod_eol)
            url += '/cardapios'
            retval = self._base_request(url)
            for i in retval:
                if i['idade'] not in ages_list:
                    ages_list.append(i['idade'])
        except IndexError as e:
            pass
        return ages_list

    def _base_request(self, url):
        r = requests.get(url, headers=self.headers)
        log.debug('url: {}'.format(url))
        return r.json()
