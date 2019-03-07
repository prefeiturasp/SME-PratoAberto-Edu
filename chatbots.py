import datetime
import json
import logging
import os
import urllib
from enum import Enum

import requests

from api_client import PratoAbertoApiClient
from mongocon import BotDbConnection

log = logging.getLogger(__name__)


class BotFlowEnum(Enum):
    QUAL_CARDAPIO = "Qual o cardápio?"
    AVALIAR_REFEICAO = "Avaliar refeição"
    RECEBER_NOTIFICACAO = 'Receber notificações'
    NENHUM = 'Nenhum'


class BaseBot(object):

    def __init__(self, payload):
        self.payload = payload

    def send_message(self, text, keyboard_opts=None):
        raise NotImplementedError

    def update_flow_data(self, args):
        raise NotImplementedError

    def set_flow(self, flow_name, step):
        raise NotImplementedError

    def get_user_data(self):
        raise NotImplementedError

    def save_notification(self):
        raise NotImplementedError


class TelegramBot(BaseBot):
    """
        Handle data related to telegram.
        It doesnt handle states
    """

    def __init__(self, payload):
        super().__init__(payload)
        TG_URL = 'https://api.telegram.org/bot{}/'.format(os.environ.get('TG_TOKEN'))
        self.TG_BASE_MESSAGE_URL = TG_URL + 'sendMessage?chat_id={}&text={}&parse_mode=Markdown'
        self.chat_id = payload['message']['chat']['id']
        self.text = payload['message']['text'].strip()
        self.chat_name = payload['message']['chat']['first_name']
        self.last_name = payload['message']['chat']['last_name']
        self.username = payload['message']['chat']['username']
        self.user_conn = BotDbConnection(self.chat_id, 'telegram',
                                         name=self.chat_name,
                                         last_name=self.last_name,
                                         platform_alias=self.username)
        self._check_flow()

    def clear_data(self):
        self.user_conn.clean_flow_control_data()

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
        self.user_conn.save_notification()

    def update_flow_data(self, **kwargs):
        self.user_conn.update_flow_control(**kwargs)

    def get_user_data(self):
        return self.user_conn.to_dict()

    def set_flow(self, flow_name, flow_step):
        self.user_conn.update_flow_control(flow_name=flow_name, flow_step=flow_step)

    def concat_evaluation(self):
        self.user_conn.save_evaluation()

    #
    # Private
    #

    def _check_flow(self):
        """if text is equal to initial statuses, them back to begin."""
        if self.text in [BotFlowEnum.QUAL_CARDAPIO.value,
                         BotFlowEnum.AVALIAR_REFEICAO.value,
                         BotFlowEnum.RECEBER_NOTIFICACAO.value]:
            self._reset_flow(self.text)

    def _reset_flow(self, text):
        self.set_flow(flow_name=text, flow_step=EduBot.STEP_INITIAL)

    def _concat_buttons(self, keyboard_opts, url, show_once=True):
        # https://core.telegram.org/bots/api/#keyboardbutton
        if keyboard_opts:
            keyboard_opts = [[text] for text in keyboard_opts]
            reply_markup = {'keyboard': keyboard_opts, 'one_time_keyboard': show_once}
            url += '&reply_markup={}'.format(json.dumps(reply_markup))
        return url


class EduBot(object):
    """Handle states
    Future plan: use a high level state machine
    https://github.com/pytransitions/transitions

    (1) Receives payloads and loads platform related class
    (2) Handle states
    """
    (STEP_SEARCH_SCHOOL,
     STEP_SCHOOL_SELECTED,
     STEP_SEARCH_SCHOOL2,
     STEP_MENU_SHOWN,
     STEP_MENU_SHOWN2,
     STEP_SATISFIED,
     STEP_EVALUATION,
     STEP_HAS_OPINION,
     STEP_OPINION) = range(1, 10)

    STEP_INITIAL = 1

    days_opts = ['Hoje', 'Amanhã', 'Ontem']

    yesno_opts = ['Sim', 'Não']

    evaluation_opts = 'Sem gosto', 'Normal', 'Gostoso', 'Delicioso'

    ages_opts = ['8 a 11 meses  - parcial',
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

    def __init__(self, platform, payload):
        log.debug('{} -> payload: {}'.format(platform, payload))
        self.api_client = PratoAbertoApiClient()
        if platform == 'telegram':
            self.bot = TelegramBot(payload)

    def process_flow(self):
        user_data = self.bot.get_user_data()
        print('user data', user_data)
        if not user_data or not user_data.get('flow_control'):
            return self._main_menu()
        if not user_data['flow_control']['flow_step'] and not user_data['flow_control']['flow_name']:
            return self._main_menu()

        step = user_data['flow_control']['flow_step']
        flow_name = user_data['flow_control']['flow_name']

        print('step, flow', step, flow_name)

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
        self._base_menu_flow(current_flow, step)

    def _base_menu_flow(self, current_flow, step):
        """Search for school and returns menu"""
        if step == self.STEP_SEARCH_SCHOOL:
            self.bot.send_message('Digite o nome da escola')
            self.bot.set_flow(current_flow, self.STEP_SEARCH_SCHOOL2)
        elif step == self.STEP_SEARCH_SCHOOL2:
            self._search_school(current_flow)
        elif step == self.STEP_SCHOOL_SELECTED:
            if self._is_age_option(self.bot.text):
                self._school_selected_parse_age()
            elif self._is_day_option(self.bot.text):
                # last step
                self._school_selected_parse_day(current_flow)
            else:
                self._school_selected_get_ages()

    def _flow_evaluate_meal(self, step):
        current_flow = BotFlowEnum.AVALIAR_REFEICAO.value
        if step == self.STEP_MENU_SHOWN:
            self._show_menu(has_buttons=True)
            self.bot.set_flow(current_flow, self.STEP_MENU_SHOWN2)
        elif step == self.STEP_MENU_SHOWN2:
            self.bot.update_flow_data(meal=self.bot.text)
            self.bot.send_message('Satisfeito com as refeições?', keyboard_opts=self.yesno_opts)
            self.bot.set_flow(current_flow, self.STEP_SATISFIED)
        elif step == self.STEP_SATISFIED:
            # TODO: validator de input y/n
            self.bot.update_flow_data(satisfied=self._from_string_to_boolean(self.bot.text))
            self.bot.send_message('O que achou da refeição?', keyboard_opts=self.evaluation_opts)
            self.bot.set_flow(current_flow, self.STEP_EVALUATION)
        elif step == self.STEP_EVALUATION:
            # TODO: validador de opções
            self.bot.update_flow_data(evaluation=self.bot.text)
            self.bot.send_message('Gostaria de deixar alguma opnião?', keyboard_opts=self.yesno_opts)
            self.bot.set_flow(current_flow, self.STEP_HAS_OPINION)
        elif step == self.STEP_HAS_OPINION:
            # validador y/n
            if self.bot.text == 'Não':
                self.bot.send_message('Obrigado!')
                self._main_menu()
            else:
                self.bot.send_message('Digite abaixo sua opinião...')
                self.bot.set_flow(current_flow, self.STEP_OPINION)
        elif step == self.STEP_OPINION:
            self.bot.update_flow_data(comment=self.bot.text)
            self.bot.concat_evaluation()
            self.bot.send_message('Obrigado!')
            self._main_menu()
        self._base_menu_flow(current_flow, step)

    def _flow_meal_alert(self, step):
        current_flow = BotFlowEnum.RECEBER_NOTIFICACAO.value
        if step == self.STEP_SEARCH_SCHOOL:
            self.bot.send_message('Digite o nome da escola')
            self.bot.set_flow(current_flow, self.STEP_SEARCH_SCHOOL2)
        elif step == self.STEP_SEARCH_SCHOOL2:
            self._search_school(current_flow)
        elif step == self.STEP_SCHOOL_SELECTED:
            if self._is_age_option(self.bot.text):
                self.bot.update_flow_data(age=self.bot.text)
                self.bot.save_notification()
                self.bot.send_message('Sua notificação foi salva!')
                self._main_menu()
            else:
                self._school_selected_get_ages()

    # commons

    def _show_menu(self, has_buttons=False):
        user_data = self.bot.get_user_data()
        flow_control = user_data['flow_control']
        timestamp = str(flow_control['menu_date']['$date'])[:10]
        menu_date = datetime.datetime.utcfromtimestamp(int(timestamp)).strftime('%Y%m%d')
        school_name = flow_control['school']
        school = self.api_client.get_schools_by_name(school_name)[0]
        if school:
            school_detailed = self.api_client.get_school_by_eol_code(school['_id'])
            menu_array = self.api_client.get_menu(age=flow_control['age'],
                                                  menu_date=menu_date,
                                                  school=school_detailed)
            if menu_array:
                if has_buttons:
                    self._print_menu(menu_array, has_buttons)
                else:
                    self._print_menu(menu_array)
            else:
                self.bot.send_message('Não foi encontrado cardápio para o dia pesquisado, desculpe.')

    def _print_menu(self, menu, has_buttons=False):
        menu_str = ''
        buttons = []
        meals = menu[0]['cardapio']
        for meal in meals:
            menu_with_meal = ''
            menu_str += '{}:\n'.format(meal)
            menu_with_meal += '{}:\n'.format(meal)
            for food in meals[meal]:
                menu_str += '- {}\n'.format(food)
                menu_with_meal += '- {}\n'.format(food)
            buttons.append(menu_with_meal)
        if has_buttons:
            self.bot.send_message('Qual refeição?', buttons)
        else:
            self.bot.send_message(menu_str)

    def _main_menu(self):
        self.bot.send_message('Bem vindo ao EduBot! Por favor, escolha uma das opções',
                              [BotFlowEnum.QUAL_CARDAPIO.value,
                               BotFlowEnum.AVALIAR_REFEICAO.value,
                               BotFlowEnum.RECEBER_NOTIFICACAO.value])

    def _is_age_option(self, opt):
        if opt in self.ages_opts:
            return True
        return False

    def _is_day_option(self, opt):
        if opt in self.days_opts:
            return True
        return False

    def _to_datetime(self, date_opt):
        """
        parse specific str to datetime
        """
        today = datetime.datetime.today()
        parse_dict = {'Hoje': today,
                      'Amanhã': today + datetime.timedelta(days=1),
                      'Ontem': today - datetime.timedelta(days=1)}
        return parse_dict.get(date_opt, today)

    def _from_string_to_boolean(self, option):
        retval = {self.yesno_opts[0]: True,
                  self.yesno_opts[1]: False}
        return retval.get(option)

    def _get_schools_by_name(self, name):
        """

        :param name: school name
        :return: array of str
        """
        retval = self.api_client.get_schools_by_name(name)
        if retval:
            retval = [p['nome'] for p in retval]
        return retval

    def _school_selected_parse_age(self):
        self.bot.update_flow_data(age=self.bot.text)
        self.bot.send_message('Escolha o dia', self.days_opts)

    def _school_selected_parse_day(self, current_flow):
        self.bot.update_flow_data(menu_date=self._to_datetime(self.bot.text))
        if current_flow == BotFlowEnum.QUAL_CARDAPIO.value:
            self._show_menu()
            self._main_menu()
        elif current_flow == BotFlowEnum.AVALIAR_REFEICAO.value:
            self.bot.set_flow(current_flow, self.STEP_MENU_SHOWN)
            self._flow_evaluate_meal(self.STEP_MENU_SHOWN)

    def _school_selected_get_ages(self):
        self.bot.update_flow_data(school=self.bot.text)
        ages = self.api_client.get_ages_by_school_nome(self.bot.text)
        if ages:
            self.bot.send_message('Escolha uma idade', ages)

    def _search_school(self, current_flow):
        schools = self._get_schools_by_name(self.bot.text)
        if schools:
            self.bot.set_flow(current_flow, flow_step=self.STEP_SCHOOL_SELECTED)
            self.bot.send_message('Escolha uma escola', schools)
        else:
            self.bot.send_message('Nenhuma escola encontrada')
            self._main_menu()
