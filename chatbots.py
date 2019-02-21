import json
import logging
import os
import urllib

import requests

from api_client import PratoAbertoApiClient

log = logging.getLogger('chatbots')


class EduBot(object):
    """Faz pesquisas em comum entre os dois mensageiros"""

    def __init__(self, conn):
        self.conn = conn
        self.api_client = PratoAbertoApiClient()

    def fluxo_conversa(self):
        return self._step1()

    def _step1(self):
        name = input('digite o nome da escola\n')
        escolas = self._get_escolas(name)
        if not escolas:
            return 'não temos escolas para a descrição {}'.format(name)
        escola = self._escolhe_escola(escolas)
        if not escola:
            return 'voce voltou'
        return escola

    #
    # Private
    #

    def _get_escolas(self, name):
        """
        Retorna array parecido com este:
        [
        {'_id': 108, 'nome': 'marcelo maia'},
        {'_id': 19089, 'nome': 'EMEI JOAO RUBENS MARCELO (TERC.)'}
        ]
        onde vem o id do mongo e o nome da escola, sendo que
        id é a mesma coisa que o codigo eol
        """
        return self.api_client.get_escolas_by_name(name)

    def _escolhe_escola(self, escolas):
        print('Escolha uma das escolas pela numeração\n')
        for escola in escolas:
            print('{} - {}'.format(escola['_id'], escola['nome']))
        eol = input('Escolha uma escola\n')
        retval = None
        for escola in escolas:
            if eol == str(escola['_id']):
                retval = escola
        return retval


class BaseBot(object):

    def __init__(self, payload):
        self.payload = payload

    def send_message(self, text, keyboard_opts=None):
        raise NotImplementedError

    def get_chat_name(self):
        raise NotImplementedError

    def get_text_and_chat_id(self):
        raise NotImplementedError


class TelegramBot(BaseBot):
    """
        https://api.telegram.org/bot<YOURTOKEN>/setWebhook  (para gerar webhook)
        https://api.telegram.org/bot780759709:AAGP1IigPhGtBqiIKK-dBaageSSOjq68mvM/setWebhook
        > ativar webhook
        curl -F "url=https://lepidus.serveo.net/telegram" https://api.telegram.org/bot780759709:AAGP1IigPhGtBqiIKK-dBaageSSOjq68mvM/setWebhook

        {'update_id': 458880384,
        'message': {'message_id': 6, 'from': {'id': 105113137, 'is_bot': False,'first_name': 'Marcelo', 'last_name': 'Maia', 'username': 'MarceloMaiaa', 'language_code': 'pt-br'},
        'chat': {'id': 105113137, 'first_name': 'Marcelo', 'last_name': 'Maia', 'username': 'MarceloMaiaa', 'type': 'private'},
        'date': 1550693882, 'text': 'marcelus'}
        }
    """
    # TODO so receber um payload de um wehhook e desenrolar daqui pra frente?
    os.environ['TG_TOKEN'] = '780759709:AAGP1IigPhGtBqiIKK-dBaageSSOjq68mvM'  # @edu_marcelo_test_bot

    TG_URL = 'https://api.telegram.org/bot{}/'.format(os.environ.get('TG_TOKEN'))
    TG_BASE_MESSAGE_URL = TG_URL + 'sendMessage?chat_id={}&text={}&parse_mode=Markdown'

    def __init__(self, payload):
        super().__init__(payload)
        self.payload = payload
        self.chat_id = payload['message']['chat']['id']
        self.text = payload['message']['text']
        self.chat_name = payload['message']['chat']['first_name']

    def send_message(self, text, keyboard_opts=None):
        """

        :param chat_id:
        :param text:
        :param keyboard_opts: array of txt
        :return:
        """
        text = urllib.parse.quote_plus(text)

        url = self.TG_BASE_MESSAGE_URL.format(self.chat_id, text)
        url = self._concat_buttons(keyboard_opts, url)

        r = requests.get(url)

        log.debug('telegram dispatch:')
        log.debug(url)
        log.debug('return: {}-{}'.format(r.status_code, r.text))

        return r.json()

    #
    # Private
    #

    def _concat_buttons(self, keyboard_opts, url, show_once=True):
        if keyboard_opts:
            # https://core.telegram.org/bots/api/#keyboardbutton
            keyboard_opts = [[text] for text in keyboard_opts]
            reply_markup = {'keyboard': keyboard_opts, 'one_time_keyboard': show_once}
            url += '&reply_markup={}'.format(json.dumps(reply_markup))
        return url


payload = {'update_id': 458880384, 'message': {'message_id': 6, 'from':
    {'id': 105113137, 'is_bot': False, 'first_name': 'Marcelo', 'last_name': 'Maia', 'username': 'MarceloMaiaa',
     'language_code': 'pt-br'}, 'chat': {'id': 105113137, 'first_name': 'Marcelo', 'last_name': 'Maia',
                                         'username': 'MarceloMaiaa', 'type': 'private'}, 'date': 1550693882,
                                               'text': 'marcelus'}}

t = TelegramBot(payload)
t.send_message(text='fala cristão, escolhe um desses', keyboard_opts=['opção 1', 'opção 2'])
