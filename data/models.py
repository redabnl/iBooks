from bson import ObjectId
from config import db
from pymongo import MongoClient, UpdateOne
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging
import streamlit as st
from datetime import datetime

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



def add_review_to_book(user_pseudo, book_id, review_text, rating): ##takes user_id, book_id, text and rating as input and adds it to the databsae 
    with get_mongo_client() as client:
        db = client['ibooks']
        reviews_collection = db['reviews']
        try:
            review = {
                "user_id": user_pseudo,
                "book_id": book_id,
                "review_text": review_text,
                "rating": rating,
                "timestamp": datetime.datetime.now()
            }
            reviews_collection.insert_one(review)
            return True
        except Exception as e:
            print(f"An error occurred: {e}")
            return False





def logout():
    st.session_state['logged_in'] = False
    st.session_state['current_user'] = None
    st.write("You have been logged out.")

# def add_book_to_user_favs(user_pseudo, book_id):
#     client = get_mongo_client()
#     db = client['ibooks']
#     db.users.update_one({'pseudo': user_pseudo}, {'$addToSet': {'favBooks': book_id}})

# def handle_add_to_favorites(user_pseudo, book_details):
#     client = get_mongo_client()
#     users_collection = client.ibooks.users
#     books_collection = client.ibooks.books
#     isbn = book_details.get('isbn')
    
#     try:
#         query = {
#             'pseudo': user_pseudo,
#             'favBooks.isbn': {'$ne': isbn}  # Ensure the book is not already in the favorites
#         }
#         update = {
#             '$addToSet': {'favBooks': book_details}  # Add the book to favBooks array if it does not already exist
#         }
        
#         result = users_collection.update_one(query, update)
#         if result.modified_count > 0:
#             print("Book added to favorites successfully.")
#             return True
        
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         return False
#     finally:
#         client.close()
        
        
#         # # Check if the book is already in the collection by ISBN
#         # book_in_db = books_collection.find_one({'ISBN': isbn})
#         # print (f"book found  in db : {book_in_db}")
        
#         # if book_in_db:
#         #     book_id = book_in_db['_id']

#         # else:
#         #     print(f"No book details for ISBN : {isbn}")
#         #     return False
            
        
#         # print(f"Book id to add in favorittes : {book_id}") 
#         # #check if the the book is in the favCollection
#         # book_in_favs = users_collection.find_one({'favBooks[]' :book_id })
#         # if book_id:
#         #     update_result = users_collection.update_one(
#         #         {'pseudo': user_pseudo},
#         #         {'$addToSet': {'favBooks': book_id}}
#         #     )       
#         #     return update_result.modified_count > 0
#         # else:
#         #     return False
    
          
        
        
        




# # def add_to_favs(user_pseudo, book_id):
#     # if not book_details.get('isbn'):
#     #     st.error('Book must have an ISBN to be added to favorites.')
#     #     return False

#     with get_mongo_client() as client:
#         db = client['ibooks']
#         users_collection = db['users']
#         books_collection = db['books']

#         try:
#             # isbn_value = book_details['isbn'][0] if isinstance(book_details['isbn'], list) else book_details['isbn']
#             # book_details['isbn'] = isbn_value  

#             book_in_db = books_collection.find_one({'_id': book_id})
#             if not book_in_db:
#                 # If the book is not in the DB, we insert it for data we'll need later
#                 inserted_book = books_collection.insert_one(book_id)
#                 book_id = inserted_book.inserted_id
#             else:
#                 book_id = book_in_db['_id']

#             # Add the book's ID to the user's list of favorites
#             result = users_collection.update_one(
#                 {'pseudo': user_pseudo},
#                 {'$addToSet': {'favBooks': book_id}}
#             )
#             return result.modified_count > 0
#         except Exception as e:
#             st.error(f"Failed to add book to favorites due to: {str(e)}")
#             return False


# def toggle_favorite(isbn, add=True):
#     favorites = st.session_state.get('favorites', [])
#     if add:
#         if isbn not in favorites:
#             favorites.append(isbn)
#     else:
#         if isbn in favorites:
#             favorites.remove(isbn)
#     st.session_state['favorites'] = favorites




        


        
# def is_book_in_favs(user_pseudo, book_id):
#     with get_mongo_client() as client:
#         db = client['ibooks']
#         users_collection = db['users']
        
#         user = users_collection.find_one({'pseudo': user_pseudo})
        
#         if user:
#             fav_books_ids = user.get('favBooks', [])
#             if book_id in fav_books_ids:
#                 return True
#             elif book_id not in fav_books_ids:
#                 return False
#             else :
#                 return("error checking ids")
        
#         return("user error !")

            
            
        
        
# def handle_book_selection(user_pseudo, search_results):
#     user_pseudo = st.session_state['current_user']
#     for book in search_results.get('docs', []):
#         isbn_list = book.get('isbn', [])
#         isbn = isbn_list[0] if isbn_list else None
#         if isbn:
#             book_details = {
#                 'title': book.get('title', 'No Title'),
#                 'author': ', '.join(book.get('author_name', ['Unknown'])),
#                 'published_year': book.get('first_publish_year', 'Not Available'),
#                 'ISBN': isbn
#             }
#             if not any(fav_book['ISBN'] == isbn for fav_book in st.session_state['favorites']):
#                 st.session_state['favorites'].append(book_details)
#                 st.success("Book added to favorites successfully.")
#             else:
#                 st.warning("Book is already in favorites.")
#         else:
#             st.error("This book cannot be added to favorites as it lacks an ISBN.")






    
# def submit_review(user_pseudo, book_id, review_text, rating):
#     client = get_mongo_client()
#     try :
#         db = client['ibooks']
#         review_doc = {
#             "user_pseudo" : user_pseudo,
#             "book_id": book_id,
#             "rating" : rating,  
#             "text" :review_text,
#             "date" : datetime.now()
#         }
        
#         review_id = db.reviews.insert_one(review_doc).inserted_id
#         #updating the user collection with the review left
#         db.users.update_one(
#             {"pseudo" : user_pseudo},
#             {"$push":{"user_reviews" : review_id}}
#         )
#         #updating thebooks collection with the review left
#         db.books.update_one(
#             {"_id": book_id},
#             {"$push": {"reviews": review_id}}
#         )
#         return True
#     except Exception as e:
#         print(f"mission failed vause of : \n {e}")
#         return False
    
    
    
# def add_review_to_book(user_pseudo, isbn, review_text, rating):
#     client = get_mongo_client()
#     users_collection = client.ibooks.users
#     try:
#         user_pseudo = st.session_state['current_user']
#         query = {'pseudo': user_pseudo, 'reviews.isbn': {'$ne': isbn}}
#         update = {
#             '$addToSet': {
#                 'reviews': {
#                     'isbn': isbn,
#                     'review_text': review_text,
#                     'rating': rating
#                 }
#             }
#         }
#         result = users_collection.update_one(query, update)
#         return result.modified_count > 0
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         return False
