from chatbots.botenum import BotFlowEnum


class BaseBot(object):

    def __init__(self, payload):
        self.payload = payload
        self.user_conn = None

    def send_message(self, text, keyboard_opts=None):
        raise NotImplementedError

    def set_flow(self, flow_name, flow_step):
        self.user_conn.update_flow_control(flow_name=flow_name, flow_step=flow_step)

    def save_notification(self):
        self.user_conn.save_notification()

    def cancel_notification(self):
        self.user_conn.cancel_notification()

    def update_flow_data(self, **kwargs):
        self.user_conn.update_flow_control(**kwargs)

    def clear_data(self):
        self.user_conn.clean_flow_control_data()

    def get_user_data(self):
        return self.user_conn.to_dict()

    def concat_evaluation(self):
        self.user_conn.save_evaluation()

    def _check_flow(self):
        """if text is equal to initial statuses, them back to begin."""
        if self.text in [BotFlowEnum.QUAL_CARDAPIO.value,
                         BotFlowEnum.AVALIAR_REFEICAO.value,
                         BotFlowEnum.RECEBER_NOTIFICACAO.value]:
            self._reset_flow(self.text)

    def _reset_flow(self, text):
        self.set_flow(flow_name=text, flow_step=BotFlowEnum.STEP_INITIAL.value)
