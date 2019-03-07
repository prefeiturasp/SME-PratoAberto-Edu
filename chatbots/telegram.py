import json
import logging
import os
import urllib

import requests

from chatbots.base import BaseBot
from chatbots.botenum import BotFlowEnum
from mongocon import BotDbConnection

log = logging.getLogger(__name__)


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
        # para buscar os dados mais atualizados
        user_conn = BotDbConnection(self.chat_id, 'telegram')
        return user_conn.to_dict()

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
        self.set_flow(flow_name=text, flow_step=BotFlowEnum.STEP_INITIAL.value)

    def _concat_buttons(self, keyboard_opts, url, show_once=True):
        # https://core.telegram.org/bots/api/#keyboardbutton
        if keyboard_opts:
            keyboard_opts = [[text] for text in keyboard_opts]
            reply_markup = {'keyboard': keyboard_opts, 'one_time_keyboard': show_once}
            url += '&reply_markup={}'.format(json.dumps(reply_markup))
        return url
