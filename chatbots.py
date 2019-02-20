import logging
import os
import pprint
import urllib
import json

import requests

from api_client import PratoAbertoApiClient

log = logging.getLogger('chatbots')


class BaseBot(object):
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


class TelegramBot(object):
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
    os.environ['TG_TOKEN'] = '780759709:AAGP1IigPhGtBqiIKK-dBaageSSOjq68mvM'    # @edu_marcelo_test_bot

    TG_URL = 'https://api.telegram.org/bot{}/'.format(os.environ.get('TG_TOKEN'))
    TG_BASE_MESSAGE_URL = TG_URL + 'sendMessage?chat_id={}&text={}&parse_mode=Markdown'

    def _telegram_payload(self, payload):
        log.debug('telegram payload:')
        log.debug(pprint.pformat(payload))

        chat_id = payload['message']['chat']['id']

        text = payload['message']['text']
        return text.strip(), chat_id

    def _telegram_get_name(self, payload):
        return payload['message']['chat']['first_name']

    def _telegram_dispatch(self, chat_id, text, keyboard_opts=None):
        """

        :param chat_id:
        :param text:
        :param keyboard_opts: array of txt
        :return:
        """
        text = urllib.parse.quote_plus(text)

        url = self.TG_BASE_MESSAGE_URL.format(chat_id, text)
        if keyboard_opts:
            # https://core.telegram.org/bots/api/#keyboardbutton
            keyboard_opts = [[text] for text in keyboard_opts]
            reply_markup = {'keyboard': keyboard_opts, 'one_time_keyboard': True}
            url += '&reply_markup={}'.format(json.dumps(reply_markup))

        r = requests.get(url)

        log.debug('telegram dispatch:')
        log.debug(url)
        log.debug('return: {}-{}'.format(r.status_code, r.text))

        return r.json()


t = TelegramBot()
t._telegram_dispatch(chat_id='105113137', text='text', keyboard_opts=['mas credo', 'teste'])