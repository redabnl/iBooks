from bson import ObjectId
from config import db
from pymongo import MongoClient, UpdateOne
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging
import streamlit as st
from datetime import datetime, timezone

def get_mongo_client():
    return MongoClient(os.getenv('MONGO_DB_URI'))

def initialize_database():
    client = get_mongo_client()
    
    
    db = client['ibooks']
    
    
    if 'users' not in db.list_collection_names():
        db.create_collection('users')
        db['users'].create_index([('pseudo', 1)], unique=True)
    
    # book collection with unique index 'ISBN'
    if 'books' not in db.list_collection_names():
        db.create_collection('books')
        db['books'].create_index([('ISBN', 1)], unique=True)
    
    # And the 'reviews' collection doesn't need a unique index since it can have dupllicated fields
    if 'reviews' not in db.list_collection_names():
        db.create_collection('reviews')
        
    if 'interactions' not in db.list_collection_names():
        db.create_collection('interactions')
        
    

    print("Database and collections are initialized.")

    client.close()

initialize_database()




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
        "email" : f'{pseudo}@ibook.com',
        "role": 'user',  # Default role fro now, maybe we can add some administrator
        "isPrivate": False,  
        "account_creation_date": datetime.now(), 
        "already_read": [],  
        "borrowedBooks": [],  # Empty array as placeholder
        "reading_goals":{
            "goal": 0,
            "books_read": 0,
        },
        "reviews": [],
        "wishlist" : []
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




def logout():
    st.session_state['logged_in'] = False
    st.session_state['current_user'] = None
    st.session_state['searched_books'] = None
    st.write("You have been logged out.")
    
    
    
# client = get_mongo_client()
# db = client['ibooks']
# user_collection = db['users']
# review_collection = db['reviews']
# interaction_collection = db['interactions']

