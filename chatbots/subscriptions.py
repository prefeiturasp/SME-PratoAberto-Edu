from dotenv import load_dotenv
from mongoengine import (connect)


import os
from chatbots.model.bot_model import UserData
load_dotenv('/home/marcelo/git/SME-PratoAberto-Edu/.env')
connect(host=os.environ.get('MONGO_HOST'))

class ProcessSubscriptions(object):
    @classmethod
    def XXX(cls):
        UserData.objects.filter(notification__exists=True)
        pass
connect(host=os.environ.get('MONGO_HOST'))
p = UserData.objects(notification__exists=True)

print(p)
