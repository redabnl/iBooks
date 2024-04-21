from dotenv import load_dotenv
import os
from pymongo import MongoClient

load_dotenv() 

MONGO_URI = os.getenv('MONGO_DB_URI')

client = MongoClient(MONGO_URI)

db = client['ibooks'] #ibook database in MongoDb 

users_collection = db['users']