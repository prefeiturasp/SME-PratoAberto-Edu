import datetime
import unittest

from chatbots.botenum import BotFlowEnum
from chatbots.model.bot_model import BotDbConnection


class DummyTest(unittest.TestCase):

    def setUp(self):
        # TODO load test database
        self.platform_id = 123456987987
        self.platform = 'telegram'
        self.conn = BotDbConnection(self.platform_id, self.platform,
                                    name='Marcelo',
                                    last_name='Maia',
                                    platform_alias='@marcelomaiaa')

    def test_user_platform_alias(self):
        self.assertEqual(self.conn.user_data.platform_alias, '@marcelomaiaa')

    def test_to_dict(self):
        self.conn.update_flow_control(flow_name=BotFlowEnum.QUAL_CARDAPIO.value,
                                      flow_step=1,
                                      school='JOSE SAMAMAGO',
                                      age='5 a 6 meses',
                                      comment='Sem comentarios',
                                      menu_date=datetime.datetime(2019, 1, 1, 1, 1, 1),
                                      satisfied=True,
                                      evaluation='MARA',
                                      meal='Sanduba de frango com catu')

        test_dict = {'platform': 'telegram', 'platform_id': 123456987987,
                     'platform_alias': '@marcelomaiaa', 'name': 'Marcelo', 'last_name': 'Maia',
                     'flow_control': {'flow_name': 'Qual o cardápio?', 'flow_step': 1, 'school': 'JOSE SAMAMAGO',
                                      'age': '5 a 6 meses', 'menu_date': {'$date': 1546304461000}, 'satisfied': True,
                                      'evaluation': 'MARA', 'comment': 'Sem comentarios',
                                      'meal': 'Sanduba de frango com catu'},
                     'evaluations': []}
        user_data_dict = self.conn.to_dict()
        user_data_dict.pop('_id')
        user_data_dict.pop('notification')
        self.assertDictEqual(user_data_dict, test_dict)

    def test_review(self):
        self.conn.save_notification()
        notification_test_dict = {'school': 'JOSE SAMAMAGO',
                                  'age': '5 a 6 meses'}
        self.assertDictEqual(self.conn.to_dict()['notification'], notification_test_dict)
