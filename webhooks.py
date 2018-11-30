# -*- coding: utf-8 -*-
import json
from http import HTTPStatus
from flask import Flask, request

from app_config import FB_VERIFY_TOKEN
from chat_processor import process_message

app = Flask(__name__)


def process_message_task(source, msg_request):
    process_message.delay(source=source, data=json.loads(msg_request.data.decode()))


@app.route('/telegram', methods=['POST'])
def telegram():
    process_message_task('telegram', request)
    return '', HTTPStatus.NO_CONTENT


@app.route('/facebook', methods=['GET', 'POST'])
def facebook():
    if request.method == 'POST':
        process_message_task('facebook', request)
        return '', HTTPStatus.NO_CONTENT
    elif request.method == 'GET':  # Para a verificação inicial
        if request.args.get('hub.verify_token') == FB_VERIFY_TOKEN:
            return request.args.get('hub.challenge')
        return "Wrong Verify Token"


if __name__ == '__main__':
    app.run(debug=True, port=5001, host="0.0.0.0")
