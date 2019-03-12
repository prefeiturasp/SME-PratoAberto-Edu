import json
import os
from http import HTTPStatus

from flask import Flask, request

from chatbots.edubot import EduBot
from chatbots.utils import validate_payload

app = Flask(__name__)


def process_message_task(platform, msg_request):
    payload = json.loads(msg_request.data.decode())
    if validate_payload(payload, platform):
        bt = EduBot(payload=payload, platform=platform)
        bt.process_flow()
    else:
        # app.logger.debug('Payload inválido para {}: {}'.format(platform, payload))
        pass


@app.route('/telegram', methods=['POST'])
def telegram():
    process_message_task('telegram', request)
    return '', HTTPStatus.NO_CONTENT


@app.route('/facebook', methods=['GET', 'POST'])
def facebook():
    if request.method == 'POST':
        process_message_task('facebook', request)
        return '', HTTPStatus.NO_CONTENT
    elif request.method == 'GET':  # Para o setup inicial do Facebook
        if request.args.get('hub.verify_token') == os.environ.get('FB_VERIFY_TOKEN'):
            return request.args.get('hub.challenge')
        return "Wrong Verify Token"


if __name__ == '__main__':
    app.run()
