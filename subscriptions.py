import datetime
import os

from mongoengine import connect

from api_client import PratoAbertoApiClient
from chatbots.facebook import FacebookNotification
from chatbots.model.bot_model import UserData
from chatbots.telegram import TelegramNotification

connect(host=os.environ.get('MONGO_HOST'))


class ProcessSubscriptions(object):
    """
    1 - Reads pratoaberto database for subscriptions.
    2 - Sends to user the desired subscription.
    """

    def __init__(self):
        self.users_with_notification = UserData.objects.filter(notification__exists=True)
        self.api_client = PratoAbertoApiClient()

    def send_notifications(self):
        for user_data in self.users_with_notification:
            if self._validate_user_notification(user_data):
                notification = user_data.notification
                today_api_format = datetime.datetime.today().strftime('%Y%m%d')
                school_detailed = self._get_school_detailed(notification)
                menu_array = self.api_client.get_menu(age=notification.age,
                                                      school=school_detailed,
                                                      menu_date=today_api_format)
                if menu_array:
                    self._print_menu(menu_array, user_data=user_data)

    def _get_school_detailed(self, notification):
        school = self.api_client.get_schools_by_name(notification.school)[0]
        school_detailed = self.api_client.get_school_by_eol_code(school['_id'])
        return school_detailed

    def _print_menu(self, menu, user_data):
        menu_str = 'Bom dia! Segue sua notificação diária da escola\n {}\n' \
                   ''.format(user_data.notification.school)
        buttons = []
        meals = menu[0]['cardapio']
        for meal in meals:
            menu_with_meal = ''
            menu_str += '{}:\n'.format(meal)
            menu_with_meal += '{}:\n'.format(meal)
            for food in meals[meal]:
                menu_str += '- {}\n'.format(food)
                menu_with_meal += '- {}\n'.format(food)
            buttons.append(menu_with_meal)
        assert user_data.platform in ['facebook', 'telegram']
        if user_data.platform == 'facebook':
            bot = FacebookNotification(user_data)
        elif user_data.platform == 'telegram':
            bot = TelegramNotification(user_data)
        bot.send_notification_message(menu_str)

    def _validate_user_notification(self, user):
        """
        :param user: UserData object
        :return: bool
        """
        assert user.notification
        return user.notification.school is not None and user.notification.age is not None


if __name__ == '__main__':
    sub = ProcessSubscriptions()
    sub.send_notifications()
