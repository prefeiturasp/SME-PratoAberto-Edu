import json
import logging
import os
import urllib

import requests

from chatbots.base import BaseBot
from chatbots.botenum import BotFlowEnum
from chatbots.model.bot_model import BotDbConnection

log = logging.getLogger(__name__)


# FB_TOKEN="EAALCbonpKegBAEa9ZA1bnodDqJ1O2rfgM1Qhs9Q5rdr8ZBf1hh4jxDNqVnZArzsYMZBPHZAonGIyBg1fOcGTJXmnfCtZAo48VRGxzgrQVsNpqyHnGZA0F6baV8ahd9fEYfV68To3Rilzk9la6Qth65p08TEFsGgupBXqMYWxBMj1AZDZD"
# FB_URL = 'https://graph.facebook.com/v2.6/me/messages/?access_token={}'.format(FB_TOKEN)
#
# FB_PROFILE_URL = 'https://graph.facebook.com/v2.6/%s?fields=first_name&access_token={}'.format(FB_TOKEN)
#
#

#
# r = requests.get(FB_PROFILE_URL % (chat_id))
# r = requests.post(FB_URL, json=payload)


class FacebookBot(BaseBot):
    """
        Handle data related to facebook.
        It doesnt handle states
    """

    def __init__(self, payload):
        super().__init__(payload)
        # payload:  {'object': 'page', 'entry': [{'id': '367746870624834', 'time': 1552072157835, 'messaging': [{'sender': {'id': '2477887728891261'}, 'recipient': {'id': '367746870624834'}, 'timestamp': 1552071970099, 'message': {'mid': 'V2AlrcRRfw_wX0zmQeWhn3z04TVqc8CauNLcSQOKGC7pBwKd6EcYQ8pG0yXV6QGEQDo-F8liNH4E4Yo-pefncw', 'seq': 98074, 'text': 'asdsadsad'}}]}]}
        self.FB_URL = 'https://graph.facebook.com/v2.6/me/messages/?access_token={}'.format(os.environ.get('FB_TOKEN'))
        messaging = payload['entry'][0]['messaging'][0]
        self.chat_id = messaging['sender']['id']
        self.text = messaging['message']['text']

        self.user_conn = BotDbConnection(self.chat_id, 'telegram')
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
        payload = {
                'recipient': {'id': self.chat_id},
                'message': {
                    'text': text}
        }
        r = requests.post(self.FB_URL, json=payload)
        log.debug('return: {}-{}'.format(r.status_code, r.text))

        return r.json()

    def save_notification(self):
        self.user_conn.save_notification()

    def update_flow_data(self, **kwargs):
        self.user_conn.update_flow_control(**kwargs)

    def get_user_data(self):
        # para buscar os dados mais atualizados
        user_conn = BotDbConnection(self.chat_id, 'facebook')
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

    def _facebook_get_name(self):
        fb_profile_url = 'https://graph.facebook.com/v2.6/{chat_id}?fields=first_name&access_token={token}'.format(
            chat_id=self.chat_id, token=os.environ.get('FB_TOKEN'))
        r = requests.get(fb_profile_url)
        nome = r.json()['first_name']
        return nome
