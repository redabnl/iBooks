from config import db
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import os

def get_mongo_client():
    client = MongoClient(os.getenv('MONGO_DB_URI'))
    return client


def create_user(pseudo, pwd):
    #check if the user already exists 
    if db.users.find_one({"pseudo" : pseudo}):
        return False
    
    #hash the password for sec reasons 
    hashed_pwd = generate_password_hash(pwd)
    
    user = {
        "pseudo": pseudo,
        "pwd": hashed_pwd,
        "favBooks": []
    }
    #insert the new user into the users collection
    db.users.insert_one(user)
    return True
    
def login_user(pseudo, pwd):
    user = db.users.find_one({
        "pseudo" : pseudo
    })
    if user and check_password_hash(user['pwd'], pwd):
        print(user)
        return True
    else:
        return False
    
def get_user_details(pseudo):
    """
    Fetch the user details from the database based on the pseudo.
    
    :param pseudo: The pseudo of the user.
    :return: The user document or None if the user is not found.
    """
    user_doc = db.users.find_one({"pseudo": pseudo})
    return user_doc


def add_to_favs(pseudo, book):
    client = get_mongo_client()
    db = client['ibooks']
    users_collection = db['users']
    
    result = users_collection.update_one(
        {"pseudo" : pseudo},
        {"$push": {"favBooks" : book}}
    )
    
    client.close()
    return result.modified_count == 1