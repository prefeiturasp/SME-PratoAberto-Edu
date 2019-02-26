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
        Handles data related to telegram.
        It doesnt handle states
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
        Creates a url with text and buttons

        :param text: text
        :param keyboard_opts: array of string
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
        """
        :return: dict
        """
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

    def _check_flow(self):
        """if text is equal to initial statuses, them back to begin."""
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
    """Handles states
    Future plan: use a high level state machine
    https://github.com/pytransitions/transitions

    (1) Receives payloads and loads platform related class
    (2) Handles states
    """
    (STEP_SEARCH_SCHOOL,
     STEP_SCHOOL_SELECTED,
     STEP_SEARCH_SCHOOL2,
     STEP_MENU_SHOWN) = range(4)

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
            return self._flow_search_menu(step)
        elif flow_name == BotFlowEnum.AVALIAR_REFEICAO.value:
            return self._flow_evaluate_meal(step)
        elif flow_name == BotFlowEnum.RECEBER_NOTIFICACAO.value:
            return self._flow_meal_alert(step)

    #
    # Private
    #

    # flows

    def _flow_search_menu(self, step):
        current_flow = BotFlowEnum.QUAL_CARDAPIO.value
        self._base_cardapio_flow(current_flow, step)

    def _base_cardapio_flow(self, current_flow, step):
        if step == self.STEP_SEARCH_SCHOOL:
            self.bot.send_message('Digite o nome da escola')
            self.bot.set_flow(current_flow, self.STEP_SEARCH_SCHOOL2)
        elif step == self.STEP_SEARCH_SCHOOL2:
            self._search_school(current_flow)
        elif step == self.STEP_SCHOOL_SELECTED:
            if self._is_age_option(self.bot.text):
                self.bot.update_user_data(args={'age': self.bot.text})
                self.bot.send_message('Escolha o dia', self.days_options)
            elif self._is_day_option(self.bot.text):
                self.bot.update_user_data(args={'menu_date': self._parse_date(self.bot.text)})
                self._show_menu(self.bot.get_user_data())
                if current_flow == BotFlowEnum.QUAL_CARDAPIO.value:
                    self._main_menu()
                elif current_flow == BotFlowEnum.AVALIAR_REFEICAO.value:
                    self.bot.set_flow(current_flow, self.STEP_MENU_SHOWN)
                    self._flow_evaluate_meal(self.STEP_MENU_SHOWN)
            else:
                self.bot.update_user_data(args={'school': self.bot.text})
                idades = self.api_client.get_ages_by_school_nome(self.bot.text)
                if idades:
                    self.bot.send_message('Escolha uma idade', idades)

    def _flow_evaluate_meal(self, step):
        current_flow = BotFlowEnum.AVALIAR_REFEICAO.value
        if step == self.STEP_MENU_SHOWN:
            print('cardapio mostrado! agora deve começar a avaliação...')
            self._main_menu()

        self._base_cardapio_flow(current_flow, step)

    def _search_school(self, current_flow):
        schools = self._get_schools_by_name(self.bot.text)
        if schools:
            self.bot.set_flow(current_flow, step=self.STEP_SCHOOL_SELECTED)
            self.bot.send_message('Escolha uma escola', schools)
        else:
            self.bot.send_message('Nenhuma escola encontrada')
            self._main_menu()

    def _flow_meal_alert(self, step):
        current_flow = BotFlowEnum.RECEBER_NOTIFICACAO.value
        if step == self.STEP_SEARCH_SCHOOL:
            self.bot.send_message('Digite o nome da escola')
            self.bot.set_flow(current_flow, self.STEP_SEARCH_SCHOOL2)
        elif step == self.STEP_SEARCH_SCHOOL2:
            self._search_school(current_flow)
        elif step == self.STEP_SCHOOL_SELECTED:
            if self._is_age_option(self.bot.text):
                self.bot.update_user_data(args={'age': self.bot.text})
                self.bot.save_notification()
                self.bot.send_message('Sua notificação foi salva!')
                self._main_menu()
            else:
                self.bot.update_user_data(args={'school': self.bot.text})
                idades = self.api_client.get_ages_by_school_nome(self.bot.text)
                if idades:
                    self.bot.send_message('Escolha uma idade', idades)

    # commons

    def _show_menu(self, user_data):
        menu_date = user_data.get('menu_date').strftime('%Y%m%d')
        school_name = user_data.get('school')
        school = self.api_client.get_schools_by_name(school_name)[0]
        if school:
            school_detailed = self.api_client.get_school_by_eol_code(school['_id'])
            menu = self.api_client.get_menu(age=user_data.get('age'),
                                            menu_date=menu_date,
                                            school=school_detailed)
            if menu:
                self._print_menu(menu)
            else:
                self.bot.send_message('Não foi encontrado cardápio para o dia pesquisado, desculpe.')

    def _print_menu(self, cardapio):
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
        """
        parse specific str to datetime
        """
        today = datetime.datetime.today()
        parse_dict = {'Hoje': today,
                      'Amanhã': today + datetime.timedelta(days=1),
                      'Ontem': today - datetime.timedelta(days=1)}
        return parse_dict.get(date_opt, today)

    def _get_schools_by_name(self, name):
        """

        :param name: school name
        :return: array of str
        """
        retval = self.api_client.get_schools_by_name(name)
        if retval:
            retval = [p['nome'] for p in retval]
        return retval
