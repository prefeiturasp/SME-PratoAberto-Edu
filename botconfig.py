# workers app configuration file

APP_NAME = 'educassis'

MONGO_URL = 'mongodb://localhost:27017'
MONGO_CHAT_COLLECTION = 'chats'

TG_TOKEN = ''
TG_URL = 'https://api.telegram.org/bot{}/'.format(TG_TOKEN)
TG_BASE_MESSAGE_URL = TG_URL + 'sendMessage?chat_id={}&text={}&parse_mode=Markdown'

FB_VERIFY_TOKEN = ''
FB_TOKEN = ''
FB_URL = 'https://graph.facebook.com/v2.6/me/messages/?access_token={}'.format(FB_TOKEN)
