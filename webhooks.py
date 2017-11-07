# -*- coding: utf-8 -*-
import json

from flask import Flask, request

from app_config import FB_VERIFY_TOKEN
from workers import process_message


app = Flask(__name__)


@app.route('/telegram', methods=['POST'])
def telegram():
    process_message.delay({'source': 'telegram', 'data': json.loads(request.data.decode())})
    return ('', 204)


@app.route('/facebook', methods=['GET', 'POST'])
def facebook():
    if request.method == 'POST':
        process_message.delay({'source': 'facebook', 'data': json.loads(request.data.decode())})
        return ('', 204)
    elif request.method == 'GET': # Para a verificação inicial
        if request.args.get('hub.verify_token') == FB_VERIFY_TOKEN:
            return request.args.get('hub.challenge')
        return "Wrong Verify Token"


if __name__ == '__main__':
    app.run(debug=True, port=5001)
