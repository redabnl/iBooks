from dotenv import load_dotenv
import os
from pymongo import MongoClient
import logging
import openai

load_dotenv() 

logging.basicConfig(level=logging.INFO)

MONGO_URI = os.getenv('MONGO_DB_URI')
API_K = os.getenv('NYT_API_KEY')
GOOGLE_BOOKS_API_KEY = os.getenv('GOOGLE_BOOKS_k')
OPENAI_API_KEY = os.getenv('OPEN_AI_KEY')

openai.api_key = OPENAI_API_KEY

client = MongoClient(MONGO_URI)
db = client['ibooks'] 
book_collection = db['books']
users_collection = db['users']