from datetime import datetime 
from config import db
from pymongo import MongoClient, UpdateOne
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging
import streamlit as st

def get_mongo_client():
    return MongoClient(os.getenv('MONGO_DB_URI'))

def initialize_database():
    client = get_mongo_client()
    
    # This will create a new database called 'ibooks' if it doesn't already exist.
    db = client['ibooks']
    
    # This will create new collections 'users', 'books', and 'reviews' if they don't already exist.
    # Collections are created automatically upon insertion of the first document, but you can also create indexes here.
    
    # For example, let's create the 'users' collection with a unique index on the 'pseudo' field.
    if 'users' not in db.list_collection_names():
        db.create_collection('users')
        db['users'].create_index([('pseudo', 1)], unique=True)
    
    # Now for the 'books' collection with a unique index on the 'ISBN' field.
    if 'books' not in db.list_collection_names():
        db.create_collection('books')
        db['books'].create_index([('ISBN', 1)], unique=True)
    
    # And the 'reviews' collection doesn't need a unique index as reviews can have duplicate fields.
    if 'reviews' not in db.list_collection_names():
        db.create_collection('reviews')

    print("Database and collections are initialized.")

    client.close()

initialize_database()

# def insert_new_user(pseudo, email, password, role='user'):
#     client = get_mongo_client()
#     db = client['ibooks']
#     users_collection = db['users']

#     # Create the user document
#     user_document = {
#         'pseudo': pseudo,
#         'email': email,
#         'pwd': generate_password_hash(password),  # Hash the password before storing it
#         'role': role,
#         'isPrivate': False,
#         'account_creation_date': datetime.now(),
#         'favBooks': [],
#         'borrowedBooks': []
#     }

#     # Insert the new user document into the users collection
#     result = users_collection.insert_one(user_document)
#     print(f"New user {pseudo} created with ID: {result.inserted_id}")

# # Example usage:
# insert_new_user('newUser', 'newUser@ibooks.com', 'password123')


# def insert_new_book(title, authors, ISBN, published_date, summary):
#     client = get_mongo_client()
#     db = client['ibooks']
#     books_collection = db['books']

#     # Create the book document
#     book_document = {
#         'title': title,
#         'authors': authors,  # This should be a list of author names
#         'ISBN': ISBN,
#         'published_date': published_date,
#         'summary': summary
#     }

#     # Insert the new book document into the books collection
#     result = books_collection.insert_one(book_document)
#     print(f"New book {title} created with ID: {result.inserted_id}")

# # Example usage:
# insert_new_book(
#     'The Adventures of Sherlock Holmes',
#     ['Arthur Conan Doyle'],
#     '9783161484100',
#     datetime(1892, 10, 14),  # Use the correct published date
#     'A collection of twelve short stories featuring Conan Doyle’s legendary detective'
# )


# def add_new_user_fields():
#     client = get_mongo_client()
#     db = client['ibooks'] 
#     users_collection = db['users']

#     # Here you should define how you'll obtain or generate the new fields for existing users.
#     # For example, 'email' can be user input, 'role' could be assigned as 'user' by default, etc.

#     # You can iterate over your users and create a bulk operation for efficiency.
#     # This example will just add placeholders for new fields.
#     updates = []
#     for user in users_collection.find():
#         updates.append(UpdateOne(
#             {'_id': user['_id']},
#             {
#                 '$set': {
#                     'email': f'{user["pseudo"]}@ibooks.com',  
#                     'role': 'user',  # Default role
#                     'isPrivate': False,  # Default privacy setting
#                     'account_creation_date': datetime.now(),  # Use the current time as placeholder
#                     'favBooks': [],  # Empty array as placeholder
#                     'borrowedBooks': []  # Empty array as placeholder
#                 }
#             }
#         ))

#     if updates:
#         result = users_collection.bulk_write(updates)
#         print(f"{result.modified_count} documents updated.")
#     else:
#         print("No updates to perform.")

# # Call the function to perform the update
# add_new_user_fields()


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


def check_or_add_book_to_db(book):
    client = get_mongo_client()
    try:
        db = client['ibooks']
        isbn = book.get('isbn', [])[0]
        if isbn:
            isbn_value = isbn if isinstance(isbn, list) else isbn  # Ensure ISBN is a single value
            book_in_db = db.books.find_one({'ISBN': isbn_value})
            if not book_in_db:
                # Normalize book data for ISBN before insertion
                book['ISBN'] = isbn_value
                book_id = db.books.insert_one(book).inserted_id
                book['_id'] = book_id
            else:
                book['_id'] = book_in_db['_id']
        else:
            raise ValueError("Book does not have a valid ISBN")
    except Exception as e:
        print(f"An error occurred: {e}")
        return None  # Return None if there's an error
    finally:
        client.close()  # Ensure the client is closed properly
    return book


def add_book_to_user_favs(user_pseudo, book_id):
    client = get_mongo_client()
    db = client['ibooks']
    db.users.update_one({'pseudo': user_pseudo}, {'$addToSet': {'favBooks': book_id}})

def handle_add_to_favorites(user_pseudo, isbn):
    client = get_mongo_client()
    try :
        db = client['ibooks']
        users_collection = db['users']
        books_collection = db['books']
        
        # if not book_details:
        #     print(f"No book details provided for ISBN : {isbn}")
        #     return False
        
        
        # Check if the book is already in the collection by ISBN
        book_in_db = books_collection.find_one({'ISBN': isbn})
        print (f"book found  in db : {book_in_db}")
        
        if book_in_db:
            book_id = book_in_db['_id']

        else:
            print(f"No book details for ISBN : {isbn}")
            return False
            
            # if book_details is not None:
            #     book_id = books_collection.insert_one(book_details).inserted_id
            # else:
        
        print(f"Book id to add in favorittes : {book_id}") 
        if book_id:
            update_result = users_collection.update_one(
                {'pseudo': user_pseudo},
                {'$addToSet': {'favBooks': book_id}}
            )       
            return update_result.modified_count > 0
        else:
            return False
    
    except Exception as e :
        print(f"errror : {e}")
    
    finally :
        client.close()        
        
        
        



# This function should be in your models.py file
def add_to_favs(user_pseudo, book_details):
    if not book_details.get('isbn'):
        st.error('Book must have an ISBN to be added to favorites.')
        return False

    with get_mongo_client() as client:
        db = client['ibooks']
        users_collection = db['users']
        books_collection = db['books']

        try:
            isbn_value = book_details['isbn'][0] if isinstance(book_details['isbn'], list) else book_details['isbn']
            book_details['isbn'] = isbn_value  # Normalize ISBN to a single value

            book_in_db = books_collection.find_one({'isbn': isbn_value})
            if not book_in_db:
                # If the book is not in the DB, insert it
                inserted_book = books_collection.insert_one(book_details)
                book_id = inserted_book.inserted_id
            else:
                book_id = book_in_db['_id']

            # Add the book's ID to the user's list of favorites
            result = users_collection.update_one(
                {'pseudo': user_pseudo},
                {'$addToSet': {'favBooks': book_id}}
            )
            return result.modified_count > 0
        except Exception as e:
            st.error(f"Failed to add book to favorites due to: {str(e)}")
            return False




        


        
def is_book_in_favs(user_pseudo, isbn):
    with get_mongo_client() as client:
        db = client['ibooks']
        users_collection = db['users']
        books_collection = db['books']

        user = users_collection.find_one({'pseudo': user_pseudo})
        if user:
            fav_books_ids = user.get('favBooks', [])
            fav_books = books_collection.find({'_id': {'$in': fav_books_ids}})
            for book in fav_books:
                book_isbn = book.get('ISBN')
                if isinstance(book_isbn, list):
                    if isbn in book_isbn:
                        return True
                elif book_isbn == isbn:
                    return True
        return False

            
            
        
        
def handle_book_selection(user_pseudo, search_results):
    for book in search_results.get('docs', []):
        isbn_list = book.get('isbn', [])
        isbn = isbn_list[0] if isbn_list else None
        if isbn:  # Ensure there is an ISBN before proceeding
            book_details = {
                'title': book.get('title', 'No Title'),
                'author': ', '.join(book.get('author_name', ['Unknown'])),
                'published_year': book.get('first_publish_year', 'Not Available'),
                'ISBN': isbn
            }
            if not is_book_in_favs(user_pseudo, isbn):  # Check if already a favorite
                success = add_to_favs(user_pseudo, book_details)
                if success:
                    st.success("Book added to favorites successfully.")
                else:
                    st.error("Failed to add book to favorites.")
            else:
                st.warning("Book is already in favorites.")
        else:
            st.error("This book cannot be added to favorites as it lacks an ISBN.")



def remove_for_favs(user_pseudo, isbn):
    with get_mongo_client() as client:
        db = client['ibooks']
        users_collection = db['users']
        books_collection = db['books']

        # Get the ObjectId of the book to be removed
        book_to_remove = books_collection.find_one({'ISBN': isbn})
        if not book_to_remove:
            return False

        book_id = book_to_remove['_id']
        
        result = users_collection.update_one(
            {'pseudo': user_pseudo},
            {'$pull': {'favBooks': book_id}}
        )
        return result.modified_count > 0


    