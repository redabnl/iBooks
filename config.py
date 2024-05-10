from dotenv import load_dotenv
import os
from pymongo import MongoClient
import logging

load_dotenv() 

MONGO_URI = os.getenv('MONGO_DB_URI')

logging.basicConfig(level=logging.INFO)

client = MongoClient(MONGO_URI)


db = client['ibooks'] 

users_collection = db['users']