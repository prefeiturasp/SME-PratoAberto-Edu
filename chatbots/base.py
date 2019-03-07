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
