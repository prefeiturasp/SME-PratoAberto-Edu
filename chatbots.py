import json
import logging
import os
import urllib
from enum import Enum

import requests
from pymongo import MongoClient

from api_client import PratoAbertoApiClient

log = logging.getLogger('chatbots')


class BotActionsEnum(Enum):
    QUAL_CARDAPIO = "Qual o cardápio?"
    AVALIAR_REFEICAO = "Avaliar refeição"
    ASSINAR_NOTIFICACAO = 'Assinar notificação'


class BaseBot(object):

    def __init__(self, payload, conn):
        self.payload = payload
        self.conn = conn

    def send_message(self, text, keyboard_opts=None):
        raise NotImplementedError

    def update_user_info(self):
        raise NotImplementedError

    def set_flow(self, flow_name, step):
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

    def __init__(self, payload, conn):
        super().__init__(payload, conn)
        self.chat_id = payload['message']['chat']['id']
        self.text = payload['message']['text'].strip()
        self.chat_name = payload['message']['chat']['first_name']
        self.check_flow()

    def check_flow(self):
        """Caso o txt recebido seja um dos status iniciais, volta para o começo"""
        if self.text in [BotActionsEnum.QUAL_CARDAPIO.value, BotActionsEnum.AVALIAR_REFEICAO.value, BotActionsEnum.ASSINAR_NOTIFICACAO.value]:
            self.reset_flow(self.text)

    def reset_flow(self, text):
            self.set_flow(flow_name=text, step=0)

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

    def create_user(self):
        # XXX chat id do telegram é conflitante com o do facebook?
        query = {'_id': self.chat_id}
        user = self.conn.users.find_one(query)
        if not user:
            user_info = {
                'nome': self.chat_name,
                'source': 'telegram'
            }
            self.conn.users.update_one(query, {'$set': user_info}, upsert=True)

    def get_current_flow(self):
        "Retorna um dict com os dados do usuário ou nada"
        query = {'_id': self.chat_id}
        user = self.conn.users.find_one(query)
        return user

    def set_flow(self, flow_name, step):
        query = {'_id': self.chat_id}
        user = self.conn.users.find_one(query)
        if not user:
            self.create_user()
        flow_info = {
            'flow_name': flow_name,
            'step': step
        }
        self.conn.users.update_one(query, {'$set': flow_info}, upsert=True)

    #
    # Private
    #

    def _concat_buttons(self, keyboard_opts, url, show_once=True):
        # https://core.telegram.org/bots/api/#keyboardbutton
        if keyboard_opts:
            keyboard_opts = [[text] for text in keyboard_opts]
            reply_markup = {'keyboard': keyboard_opts, 'one_time_keyboard': show_once}
            url += '&reply_markup={}'.format(json.dumps(reply_markup))
        return url


class EduBot(object):
    """Faz pesquisas em comum entre os dois mensageiros"""

    def __init__(self, platform, payload, conn):
        self.api_client = PratoAbertoApiClient()
        if platform == 'telegram':
            self.bot = TelegramBot(payload, conn)
        current_flow = self.bot.get_current_flow()
        self.parse_flow(current_flow)

    def parse_flow(self, current_flow):
        if not current_flow:    # usuario nao cadastrado ainda, seta o fluxo inicial
            self.bot.send_message('Escolha uma das opções',
                                  [BotActionsEnum.QUAL_CARDAPIO.value,
                                   BotActionsEnum.AVALIAR_REFEICAO.value,
                                   BotActionsEnum.ASSINAR_NOTIFICACAO.value])
        if current_flow['flow_name'] == BotActionsEnum.QUAL_CARDAPIO.value:
            self._get_escolas()


    def fluxo_qual_cardapio(self):
        self.bot.send_message('Digite o nome da escola que deseja')
        self.bot.set_flow(BotActionsEnum.QUAL_CARDAPIO.value, 0)

    def fluxo_conversa(self):
        return self._step1()

    #
    # Private
    #

    def _get_state(self):
        pass

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


payload = {'update_id': 458880384, 'message': {'message_id': 6, 'from':
    {'id': 105113137, 'is_bot': False, 'first_name': 'Marcelo', 'last_name': 'Maia', 'username': 'MarceloMaiaa',
     'language_code': 'pt-br'}, 'chat': {'id': 105113137, 'first_name': 'Marcelo', 'last_name': 'Maia',
                                         'username': 'MarceloMaiaa', 'type': 'private'}, 'date': 1550693882,
                                               'text': BotActionsEnum.ASSINAR_NOTIFICACAO.value}}

client = MongoClient('mongodb://localhost:27017/')
conn = client['MarceloBotTest']

bt = EduBot('telegram', payload, conn)
