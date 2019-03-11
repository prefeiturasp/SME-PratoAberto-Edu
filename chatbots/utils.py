pls = [{'object': 'page', 'entry': [{'id': '367746870624834', 'time': 1552313627091, 'messaging': [
    {'sender': {'id': '367746870624834'}, 'recipient': {'id': '2477887728891261'}, 'timestamp': 1552313622056,
     'message': {'is_echo': True, 'app_id': 776729969371624,
                 'mid': 'X73ruH_Dhhs8LwcD3UT1w3z04TVqc8CauNLcSQOKGC488zuGU48KIP4gkawjtG6o8hWJWbuw-WFjtiH_YKR0ng',
                 'seq': 98147, 'text': 'Escolha uma idade', 'attachments': [
             {'title': '', 'url': None, 'type': 'template', 'payload': {'template_type': 'button', 'buttons': [
                 {'type': 'postback', 'title': 'Todas as idades', 'payload': 'Todas as idades'},
                 {'type': 'postback', 'title': 'Toda Idade', 'payload': 'Toda Idade'}]}}]}}]}]},
       {'object': 'page', 'entry': [{'id': '367746870624834', 'time': 1552313625447, 'messaging': [
           {'sender': {'id': '367746870624834'}, 'recipient': {'id': '2477887728891261'}, 'timestamp': 1552313622056,
            'message': {'is_echo': True, 'app_id': 776729969371624,
                        'mid': 'X73ruH_Dhhs8LwcD3UT1w3z04TVqc8CauNLcSQOKGC488zuGU48KIP4gkawjtG6o8hWJWbuw-WFjtiH_YKR0ng',
                        'seq': 98147, 'text': 'Escolha uma idade', 'attachments': [
                    {'title': '', 'url': None, 'type': 'template', 'payload': {'template_type': 'button', 'buttons': [
                        {'type': 'postback', 'title': 'Todas as idades', 'payload': 'Todas as idades'},
                        {'type': 'postback', 'title': 'Toda Idade', 'payload': 'Toda Idade'}]}}]}}]}]},
       {'object': 'page', 'entry': [{'id': '367746870624834', 'time': 1552313624123, 'messaging': [
           {'sender': {'id': '2477887728891261'}, 'recipient': {'id': '367746870624834'}, 'timestamp': 1552313624076,
            'delivery': {
                'mids': ['vN4-0Og5-zaxqMwWQ2c_cnz04TVqc8CauNLcSQOKGC7bBSJj2bdNPjy-ZWA3pKn8oXE2Om2Bn3OxPXuYKfS96w',
                         'WW4CRXQQqORgVf3SmQVDT3z04TVqc8CauNLcSQOKGC7i-GIt1QMFa_hpnNa17nwLhQLXGYkulyX-U45Dbwg3-g',
                         'WF6J1ZcphJ06fm9lKMfgfXz04TVqc8CauNLcSQOKGC5ECGUzXlgh5-bQAFuRzbHuIgl5AwlBkCEE4vpTQNVMlA',
                         'X73ruH_Dhhs8LwcD3UT1w3z04TVqc8CauNLcSQOKGC488zuGU48KIP4gkawjtG6o8hWJWbuw-WFjtiH_YKR0ng'],
                'watermark': 1552313622056, 'seq': 0}}]}]},
       {'object': 'page', 'entry': [{'id': '367746870624834', 'time': 1552313624390, 'messaging': [
           {'sender': {'id': '367746870624834'}, 'recipient': {'id': '2477887728891261'}, 'timestamp': 1552313622056,
            'message': {'is_echo': True, 'app_id': 776729969371624,
                        'mid': 'X73ruH_Dhhs8LwcD3UT1w3z04TVqc8CauNLcSQOKGC488zuGU48KIP4gkawjtG6o8hWJWbuw-WFjtiH_YKR0ng',
                        'seq': 98147, 'text': 'Escolha uma idade', 'attachments': [
                    {'title': '', 'url': None, 'type': 'template', 'payload': {'template_type': 'button', 'buttons': [
                        {'type': 'postback', 'title': 'Todas as idades', 'payload': 'Todas as idades'},
                        {'type': 'postback', 'title': 'Toda Idade', 'payload': 'Toda Idade'}]}}]}}]}]}

       ]


def validate_payload(payload, platform):
    # TODO: improve this validator
    if platform == 'facebook':
        messaging = payload['entry'][0]['messaging'][0]
        if messaging.get('message'):
            if messaging['message'].get('is_echo'):
                return False
            return True
        if messaging.get('postback'):
            return True
    return False

