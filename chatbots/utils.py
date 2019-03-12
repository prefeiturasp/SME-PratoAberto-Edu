import logging
import sys

edu_logger = logging.getLogger('edubot')
edu_logger.setLevel(logging.DEBUG)
log_format = logging.Formatter("[%(asctime)s] - %(name)s - %(levelname)s - %(message)s")

ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(log_format)
edu_logger.addHandler(ch)


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
    elif platform == 'telegram':
        return True
    return False
