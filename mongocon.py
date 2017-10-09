# -*- coding: utf-8 -*-
from pymongo import MongoClient

from app_config import MONGO_URL

db = MongoClient(MONGO_URL)