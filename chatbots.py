import json
import logging
import os
import urllib
from enum import Enum
import datetime
import requests
from pymongo import MongoClient

from api_client import PratoAbertoApiClient

log = logging.getLogger('chatbots')


class BotFlowEnum(Enum):
    QUAL_CARDAPIO = "Qual o cardápio?"
    AVALIAR_REFEICAO = "Avaliar refeição"
    ASSINAR_NOTIFICACAO = 'Assinar notificação'
    NENHUM = 'Nenhum'


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
        if self.text in [BotFlowEnum.QUAL_CARDAPIO.value, BotFlowEnum.AVALIAR_REFEICAO.value,
                         BotFlowEnum.ASSINAR_NOTIFICACAO.value]:
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

    def update_user_data(self, args):
        """
        Generic method, needs
        :param args: a dict
        """
        query = {'_id': self.chat_id}
        user = self.conn.users.find_one(query)
        if not user:
            self.create_user()
        self.conn.users.update_one(query, {'$set': args}, upsert=True)

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
    """Faz pesquisas em comum entre os dois mensageiros
    Planos futuros: usar maquina de estados para cada conversa
    https://github.com/pytransitions/transitions"""
    STEP_BUSCA_ESCOLA, STEP_ESCOLA_ESCOLHIDA, STEP_RETORNA_CARDAPIO = range(3)
    STEP_STEP_ZERO = 0

    days_options = ['Hoje', 'Amanhã', 'Ontem']

    idades_options = ['8 a 11 meses  - parcial',
                      'EMEI da CEMEI',
                      '6 a 7 meses - parcial',
                      '7 meses',
                      '0 a 5 meses',
                      '6 meses',
                      '4 a 6 anos - parcial',
                      '2 a 3 anos - parcial',
                      'Professor ',
                      'Pro Jovem (filhos)',
                      'Professor (jantar)',
                      '2 a 6 anos',
                      'Toda Idade',
                      '6 a 7 meses',
                      '2 a 3 anos',
                      '0 a 1 mês',
                      '4 a 5 meses',
                      '8 a 11 meses',
                      '1 ano - parcial',
                      '1 a 3 meses',
                      '4 a 6 anos',
                      'Todas as idades',
                      '1 ano']

    def __init__(self, platform, payload, conn):
        self.api_client = PratoAbertoApiClient()
        if platform == 'telegram':
            self.bot = TelegramBot(payload, conn)
        self.current_flow = self.bot.get_current_flow()

    def process_flow(self):
        flow = self.current_flow
        if not flow:
            self._show_flow_options()

        step = flow['step']
        flow_name = flow['flow_name']

        if flow_name == BotFlowEnum.NENHUM.value:
            self._show_flow_options()

        if flow_name == BotFlowEnum.QUAL_CARDAPIO.value:
            self._flow_qual_cardapio(flow, step)

    def _flow_qual_cardapio(self, flow, step):
        if step == self.STEP_BUSCA_ESCOLA:
            self.bot.send_message('Digite o nome da escola')
            escolas = self._get_escolas(self.bot.text)
            if escolas:
                self.bot.set_flow(BotFlowEnum.QUAL_CARDAPIO.value, step=self.STEP_ESCOLA_ESCOLHIDA)
                self.bot.send_message('Escolha uma escola', escolas)
        elif step == self.STEP_ESCOLA_ESCOLHIDA:
            if self._is_age_option(self.bot.text):
                self.bot.update_user_data(args={'age': self.bot.text})
                self.bot.send_message('Escolha o dia', self.days_options)
            elif self._is_day_option(self.bot.text):
                self.bot.update_user_data(args={'menu_date': self._parse_date(self.bot.text)})
                self.bot.set_flow(BotFlowEnum.QUAL_CARDAPIO.value, self.STEP_RETORNA_CARDAPIO)
            else:
                self.bot.update_user_data(args={'school': self.bot.text})
                idades = self.api_client.get_idades_by_escola_nome(self.bot.text)
                if idades:
                    self.bot.send_message('Escolha uma idade', idades)
        elif step == self.STEP_RETORNA_CARDAPIO:
            school_name = flow.get('school')
            school = self.api_client.get_escolas_by_name(school_name)[0]
            menu_date = flow.get('menu_date').strftime('%Y%M%d')
            query_args = {
                'idade': flow.get('age'),
                'data_inicial': menu_date,
                'data_final': menu_date
            }
            cardapio = self.api_client.get_cardapio(cod_eol=school['_id'], query_args=query_args)
            print(cardapio)
            self.bot.set_flow(BotFlowEnum.NENHUM.value, self.STEP_STEP_ZERO)
            self._show_flow_options()

    def _show_flow_options(self):
        self.bot.send_message('Escolha uma das opções',
                              [BotFlowEnum.QUAL_CARDAPIO.value,
                               BotFlowEnum.AVALIAR_REFEICAO.value,
                               BotFlowEnum.ASSINAR_NOTIFICACAO.value])

    def fluxo_qual_cardapio(self):
        self.bot.send_message('Digite o nome da escola que deseja')
        self.bot.set_flow(BotFlowEnum.QUAL_CARDAPIO.value, 0)

    #
    # Private
    #

    def _is_age_option(self, opt):
        if opt in self.idades_options:
            return True
        return False

    def _is_day_option(self, opt):
        if opt in self.days_options:
            return True
        return False

    def _parse_date(self, date_opt):
        """Passa string Hoje, Amanhã ou Ontem para date"""
        today = datetime.datetime.today()
        parse_dict = {'Hoje': today,
                      'Amanhã': today + datetime.timedelta(days=1),
                      'Ontem': today - datetime.timedelta(days=1)}
        return parse_dict.get(date_opt, today)

    def _get_state(self):
        pass

    def _get_escolas(self, name):
        """
        Retorna array de escolas:
        [
        'marcelo maia',
        'EMEI JOAO RUBENS MARCELO (TERC.)'
        ]
        onde vem o id do mongo e o nome da escola, sendo que
        id é a mesma coisa que o codigo eol
        """
        retval = self.api_client.get_escolas_by_name(name)
        if retval:
            retval = [p['nome'] for p in retval]
        return retval

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
