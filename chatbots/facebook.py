import logging
import os

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
        self.FB_URL = 'https://graph.facebook.com/v2.6/me/messages/?access_token={}'.format(os.environ.get('FB_TOKEN'))
        messaging = payload['entry'][0]['messaging'][0]
        self.chat_id = messaging['sender']['id']
        self.text = messaging['message']['text']

        self.user_conn = BotDbConnection(self.chat_id, 'telegram')
        self._check_flow()

    def send_message(self, text, keyboard_opts=None):
        """
        Creates a url with text and buttons

        :param text: text
        :param keyboard_opts: [text, text ...]
        :return:
        """
        payload = {
            'recipient': {'id': self.chat_id},
            'message': {
                'text': text}}
        if keyboard_opts:
            payload['message'] = self._concat_buttons(text, keyboard_opts)
        r = requests.post(self.FB_URL, json=payload)
        log.debug('return: {}-{}'.format(r.status_code, r.text))

        return r.json()

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

    def _concat_buttons(self, text, keyboard_opts):
        """
        https://developers.facebook.com/docs/messenger-platform/reference/webhook-events/messaging_postbacks
        https://developers.facebook.com/docs/messenger-platform/reference/buttons/postback
        """
        buttons = []
        for text_option in keyboard_opts:
            buttons.append({
                "type": "postback",
                "title": text_option,
                "payload": "DEVELOPER_DEFINED_PAYLOAD"
            })
        message = {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": text,
                    "buttons": buttons
                }
            }
        }
        return message

    def _facebook_get_name(self):
        fb_profile_url = 'https://graph.facebook.com/v2.6/{chat_id}?fields=first_name&access_token={token}'.format(
            chat_id=self.chat_id, token=os.environ.get('FB_TOKEN'))
        r = requests.get(fb_profile_url)
        nome = r.json()['first_name']
        return nome
