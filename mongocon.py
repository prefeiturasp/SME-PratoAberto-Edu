import datetime
import os

from dotenv import load_dotenv
from mongoengine import *

load_dotenv('.env')
connect(host=os.environ.get('MONGO_HOST'))


class Evaluations(EmbeddedDocument):
    school = StringField(required=True, max_length=100)
    meal = StringField(required=True, max_length=300)
    age = StringField(required=True, max_length=25)
    comment = StringField(required=False, max_length=300)
    satisfied = BooleanField(required=True)
    menu_date = DateTimeField(default=datetime.datetime.utcnow)


class TmpData(EmbeddedDocument):
    flow_name = StringField(required=True, max_length=15)
    flow_step = IntField(required=True)
    school = StringField(required=True, max_length=100)
    age = StringField(required=True, max_length=25)
    menu_date = DateTimeField(default=datetime.datetime.utcnow)
    satisfied = BooleanField(required=True)
    evaluation = StringField(required=True, max_length=15)  # Bom, normal, muito bom, ruim...
    comment = StringField(required=False, max_length=300)
    meal = StringField(required=True, max_length=300)


class UserData(Document):
    platform = StringField(required=True, max_length=20)  # telegram | facebook
    platform_id = IntField(required=True)
    platform_alias = StringField(required=True, max_length=20)  # ex @fulano no telegram
    name = StringField(required=True, max_length=20)
    last_name = StringField(max_length=20)
    tmp_data = EmbeddedDocumentField(TmpData)
    evaluations = ListField(EmbeddedDocumentField(Evaluations))


e1 = Evaluations(school='saraiva xxx', meal='pao com feijao', age='1 a 2 anos', comment='oie xxx', satisfied=True)

t1 = TmpData(flow_name='xxxx',meal='xxx', flow_step=1, school='xxxx', age='awsd',
             satisfied=False, evaluation='supimpa', comment='xxx')
t2 = UserData(platform='telegram', platform_id=123, platform_alias='@fulano', name='maxx', tmp_data=t1, evaluations=[e1]
              )
t2.save()
