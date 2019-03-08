import json
import logging
import os
import urllib

import requests

from chatbots.base import BaseBot
from chatbots.botenum import BotFlowEnum
from chatbots.model.bot_model import BotDbConnection

log = logging.getLogger(__name__)


class FacebookBot(BaseBot):
    """
        Handle data related to facebook.
        It doesnt handle states
    """

    def __init__(self, payload):
        super().__init__(payload)
        # payload:  {'object': 'page', 'entry': [{'id': '367746870624834', 'time': 1552072157835, 'messaging': [{'sender': {'id': '2477887728891261'}, 'recipient': {'id': '367746870624834'}, 'timestamp': 1552071970099, 'message': {'mid': 'V2AlrcRRfw_wX0zmQeWhn3z04TVqc8CauNLcSQOKGC7pBwKd6EcYQ8pG0yXV6QGEQDo-F8liNH4E4Yo-pefncw', 'seq': 98074, 'text': 'asdsadsad'}}]}]}
        TG_URL = 'https://api.telegram.org/bot{}/'.format(os.environ.get('TG_TOKEN'))
        self.TG_BASE_MESSAGE_URL = TG_URL + 'sendMessage?chat_id={}&text={}&parse_mode=Markdown'

        self.chat_id = payload['entry'][0]['messaging'][0]['sender']['id']
        self.text = payload['entry'][0]['messaging'][0]['message']['text']
        self.chat_name = 'fulanomen'
        self.last_name = 'ciclano'
        self.username = 'fulano user'

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
