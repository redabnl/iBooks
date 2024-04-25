from datetime import datetime 
from config import db
from pymongo import MongoClient, UpdateOne
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging

def get_mongo_client():
    client = MongoClient(os.getenv('MONGO_DB_URI'))
    return client



def add_new_user_fields():
    client = get_mongo_client()
    db = client['ibooks'] 
    users_collection = db['users']

    # Here you should define how you'll obtain or generate the new fields for existing users.
    # For example, 'email' can be user input, 'role' could be assigned as 'user' by default, etc.

    # You can iterate over your users and create a bulk operation for efficiency.
    # This example will just add placeholders for new fields.
    updates = []
    for user in users_collection.find():
        updates.append(UpdateOne(
            {'_id': user['_id']},
            {
                '$set': {
                    'email': f'{user["pseudo"]}@ibooks.com',  
                    'role': 'user',  # Default role
                    'isPrivate': False,  # Default privacy setting
                    'account_creation_date': datetime.now(),  # Use the current time as placeholder
                    'favBooks': [],  # Empty array as placeholder
                    'borrowedBooks': []  # Empty array as placeholder
                }
            }
        ))

    if updates:
        result = users_collection.bulk_write(updates)
        print(f"{result.modified_count} documents updated.")
    else:
        print("No updates to perform.")

# Call the function to perform the update
add_new_user_fields()


#############################################################
def create_user(pseudo, pwd):
    #check if the user already exists 
    if db.users.find_one({"pseudo" : pseudo}):
        return False
    
    #hash the password for sec reasons 
    hashed_pwd = generate_password_hash(pwd)
    
    user = {
        "pseudo": pseudo,
        "pwd": hashed_pwd,
        "email" : f'{["pseudo"]}@ibook.com',#  default mail for the user, we'll use it later 
        "role": 'user',  # Default role
        "isPrivate": False,  # Default privacy setting
        "account_creation_date": datetime.now(),  # Use the current time as placeholder
        "favBooks": [],  # Empty array as placeholder
        "borrowedBooks": []  # Empty array as placeholder
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


def add_to_favs(user_pseudo, book_details):
    with get_mongo_client() as client :    
        db = client['ibooks']
        users_collection = db['users']
        
        if is_book_in_favs(user_pseudo, book_details):
            print(f"Book {book_details['title']} is already in favorites for user {user_pseudo}.")
            return False
        
        result = users_collection.update_one(
                {"pseudo" : user_pseudo},
                {"$push": {"favBooks" : book_details}}
            )
        
        if result.modified_count > 0 :
            print(f"Book {book_details['title']} added to favorites for user {user_pseudo}.")
        
        else :
            print(f"Failed to add book {book_details['title']} to favorites for user {user_pseudo}.")
            return False
def is_book_in_favs(user_pseudo, book_details):
   
    with get_mongo_client() as client:
        db = client['ibooks']
        users_collection = db['users']
        user = users_collection.find_one({'pseudo': user_pseudo})
        if user:
            return any(book['title'] == book_details['title'] for book in user.get('favBooks', []))
        return False


def remove_for_favs(user_pseudo, book_details):
    with get_mongo_client() as client :
        db = client['ibooks']
    users_collection = db['users']
        
    result = users_collection.update_one(
        {'pseudo' : user_pseudo},
        {'$pull' : {'favBooks' : { 'title' : book_details['title']}}}
    )
    return result.modified_count > 0

    