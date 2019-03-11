import os

from mongoengine import (connect)

from chatbots.model.bot_model import UserData

connect(host=os.environ.get('MONGO_HOST'))


class ProcessSubscriptions(object):
    @classmethod
    def XXX(cls):
        UserData.objects.filter(notification__exists=True)
        pass


connect(host=os.environ.get('MONGO_HOST'))
p = UserData.objects(notification__exists=True)

print(p)
