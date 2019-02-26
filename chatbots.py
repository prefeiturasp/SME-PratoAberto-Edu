import datetime
import json
import logging
import os
import urllib
from enum import Enum

import requests

from api_client import PratoAbertoApiClient

log = logging.getLogger(__name__)


class BotFlowEnum(Enum):
    QUAL_CARDAPIO = "Qual o cardápio?"
    AVALIAR_REFEICAO = "Avaliar refeição"
    RECEBER_NOTIFICACAO = 'Receber notificações'
    NENHUM = 'Nenhum'


class BaseBot(object):

    def __init__(self, payload, conn):
        self.payload = payload
        self.conn = conn

    def send_message(self, text, keyboard_opts=None):
        raise NotImplementedError

    def update_user_data(self, args):
        raise NotImplementedError

    def set_flow(self, flow_name, step):
        raise NotImplementedError

    def get_user_data(self):
        raise NotImplementedError

    def save_notification(self):
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

    def __init__(self, payload, conn):
        super().__init__(payload, conn)
        TG_URL = 'https://api.telegram.org/bot{}/'.format(os.environ.get('TG_TOKEN'))
        self.TG_BASE_MESSAGE_URL = TG_URL + 'sendMessage?chat_id={}&text={}&parse_mode=Markdown'
        self.chat_id = payload['message']['chat']['id']
        self.text = payload['message']['text'].strip()
        self.chat_name = payload['message']['chat']['first_name']
        self._check_flow()

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

    def save_notification(self):
        user_data = self.get_user_data()
        if user_data:
            self._create_notification(user_data)

    def _create_notification(self, user_data):
        query = {'_id': self.chat_id}
        age = user_data['age']
        school = user_data['school']
        flow_name = user_data['flow_name']
        args = {'age': age,
                'school': school,
                'source': 'telegram'}
        assert flow_name == BotFlowEnum.RECEBER_NOTIFICACAO.value
        self.conn.notifications.update_one(query, {'$set': args}, upsert=True)

    def update_user_data(self, args):
        """
        Generic method, to update or create fields in user collection
        :param args: a dict
        """
        query = {'_id': self.chat_id}
        user = self.conn.users.find_one(query)
        if not user:
            self._create_user()
        self.conn.users.update_one(query, {'$set': args}, upsert=True)

    def get_user_data(self):
        """Retorna um dict com os dados do usuário ou nada"""
        query = {'_id': self.chat_id}
        user = self.conn.users.find_one(query)
        return user

    def set_flow(self, flow_name, step):
        query = {'_id': self.chat_id}
        user = self.conn.users.find_one(query)
        if not user:
            self._create_user()
        flow_info = {
            'flow_name': flow_name,
            'step': step
        }
        self.conn.users.update_one(query, {'$set': flow_info}, upsert=True)

    #
    # Private
    #

    def _check_flow(self):
        """Caso o txt recebido seja um dos status iniciais, volta para o começo,
        Serve também como uma inicialização para uma nova conversa."""
        if self.text in [BotFlowEnum.QUAL_CARDAPIO.value,
                         BotFlowEnum.AVALIAR_REFEICAO.value,
                         BotFlowEnum.RECEBER_NOTIFICACAO.value]:
            self._reset_flow(self.text)

    def _reset_flow(self, text):
        self.set_flow(flow_name=text, step=0)

    def _create_user(self):
        query = {'_id': self.chat_id}
        user = self.conn.users.find_one(query)
        if not user:
            user_info = {
                'name': self.chat_name,
                'source': 'telegram'
            }
            self.conn.users.update_one(query, {'$set': user_info}, upsert=True)

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
    https://github.com/pytransitions/transitions

    (1) Recebe payloads e instancia o bot adequado de acordo com a plataforma
    (2) Trata fluxo
    (3) Pergunta pro objeto específico os dados da sua respectiva plataforma
    """
    STEP_BUSCA_ESCOLA, STEP_ESCOLA_ESCOLHIDA, STEP_RETORNA_CARDAPIO = range(3)
    STEP_ZERO = 0

    days_options = ['Hoje', 'Amanhã', 'Ontem']

    ages_options = ['8 a 11 meses  - parcial',
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
        log.debug('{} -> payload: {}'.format(platform, payload))
        self.api_client = PratoAbertoApiClient()
        if platform == 'telegram':
            self.bot = TelegramBot(payload, conn)

    def process_flow(self):
        user_data = self.bot.get_user_data()
        if not user_data:
            return self._main_menu()
        if not user_data.get('step', None) and not user_data.get('flow_name', None):
            return self._main_menu()

        step = user_data['step']
        flow_name = user_data['flow_name']

        if flow_name == BotFlowEnum.NENHUM.value:
            return self._main_menu()
        elif flow_name == BotFlowEnum.QUAL_CARDAPIO.value:
            return self._flow_qual_cardapio(step)
        elif flow_name == BotFlowEnum.AVALIAR_REFEICAO.value:
            return self._flow_avaliar_refeicao(step)
        elif flow_name == BotFlowEnum.RECEBER_NOTIFICACAO.value:
            return self._flow_assina_notificacao(step)

    #
    # Private
    #

    # flows

    def _flow_qual_cardapio(self, step):
        current_flow = BotFlowEnum.QUAL_CARDAPIO.value
        self._base_cardapio_flow(current_flow, step)

    def _base_cardapio_flow(self, current_flow, step):
        if step == self.STEP_BUSCA_ESCOLA:
            self._busca_escola(current_flow)
        elif step == self.STEP_ESCOLA_ESCOLHIDA:
            if self._is_age_option(self.bot.text):
                self.bot.update_user_data(args={'age': self.bot.text})
                self.bot.send_message('Escolha o dia', self.days_options)
            elif self._is_day_option(self.bot.text):
                self.bot.update_user_data(args={'menu_date': self._parse_date(self.bot.text)})
                self._show_cardapio(self.bot.get_user_data())
                if current_flow == BotFlowEnum.QUAL_CARDAPIO.value:
                    self._main_menu()
            else:
                self.bot.update_user_data(args={'school': self.bot.text})
                idades = self.api_client.get_idades_by_escola_nome(self.bot.text)
                if idades:
                    self.bot.send_message('Escolha uma idade', idades)

    def _flow_avaliar_refeicao(self, step):
        current_flow = BotFlowEnum.AVALIAR_REFEICAO.value
        self._base_cardapio_flow(current_flow, step)
        print('checkpoint da avaliação do robo')
        self._main_menu()

    def _busca_escola(self, current_flow):
        self.bot.send_message('Digite o nome da escola')
        escolas = self._get_escolas(self.bot.text)
        if escolas:
            self.bot.set_flow(current_flow, step=self.STEP_ESCOLA_ESCOLHIDA)
            self.bot.send_message('Escolha uma escola', escolas)

    def _flow_assina_notificacao(self, step):
        current_flow = BotFlowEnum.RECEBER_NOTIFICACAO.value
        if step == self.STEP_BUSCA_ESCOLA:
            self._busca_escola(current_flow)
        elif step == self.STEP_ESCOLA_ESCOLHIDA:
            if self._is_age_option(self.bot.text):
                self.bot.update_user_data(args={'age': self.bot.text})
                self.bot.save_notification()
                self._main_menu()
            else:
                self.bot.update_user_data(args={'school': self.bot.text})
                idades = self.api_client.get_idades_by_escola_nome(self.bot.text)
                if idades:
                    self.bot.send_message('Escolha uma idade', idades)

    # commons

    def _show_cardapio(self, flow):
        """No final do fluxo, exibe o cardapio correspondente às opções escolhidas"""
        menu_date = flow.get('menu_date').strftime('%Y%m%d')
        school_name = flow.get('school')
        school = self.api_client.get_escolas_by_name(school_name)[0]
        if school:
            school_detailed = self.api_client.get_escola_by_eol_code(school['_id'])
            cardapio = self.api_client.get_cardapio(age=flow.get('age'),
                                                    menu_date=menu_date,
                                                    school=school_detailed)
            if cardapio:
                self._print_cardapio(cardapio)
            else:
                self.bot.send_message('Não foi encontrado cardápio para o dia pesquisado, desculpe.')

    def _print_cardapio(self, cardapio):
        cardapio_str = ''
        refeicoes = cardapio[0]['cardapio']
        for refeicao in refeicoes:
            cardapio_str += '{}:\n'.format(refeicao)
            for comida in refeicoes[refeicao]:
                cardapio_str += '- {}\n'.format(comida)

        self.bot.send_message(cardapio_str)
        self.bot.send_message('Obrigado por consultar!')

    def _main_menu(self):
        self.bot.send_message('Bem vindo ao EduBot! Por favor, escolha uma das opções',
                              [BotFlowEnum.QUAL_CARDAPIO.value,
                               BotFlowEnum.AVALIAR_REFEICAO.value,
                               BotFlowEnum.RECEBER_NOTIFICACAO.value])

    def _is_age_option(self, opt):
        if opt in self.ages_options:
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

    def _get_escolas(self, name):
        """
        Retorna array de nomes de escolas
        """
        retval = self.api_client.get_escolas_by_name(name)
        if retval:
            retval = [p['nome'] for p in retval]
        return retval
