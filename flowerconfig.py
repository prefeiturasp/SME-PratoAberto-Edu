# flower config file, see docs at
# https://flower.readthedocs.io/en/latest/config.html

# Broker settings
# BROKER_URL = 'amqp://guest:guest@localhost:5672//'

# RabbitMQ management api
broker_api = 'http://localhost:15672/api/'

# flower server configs
# address
port = 5555
url_prefix = 'admin/flower'

# flower settings
# conf = 'flowerconfig.py'
# auto_refresh = True
# max_workers = 5000
# max_tasks = 10000
# natural_time = True
# persistent = False
# db = flower
# enable_events
# format_task
# inspect_timeout
# xheaders = False
# tasks_columns
# unix_socket

# Enable debug logging
# debug = False
logging = 'INFO'

# ssl
# ca_certs
# certfile
# keyfile

# authentication
# auth
# auth_provider
# basic_auth = ['user:password']
# cookie_secret

