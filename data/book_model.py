import streamlit as st
from pymongo import MongoClient
import os
from bson.objectid import ObjectId
from config import API_K, OPENAI_API_KEY, GOOGLE_BOOKS_API_KEY
import requests
import datetime
import logging
import openai
import hashlib
import pymongo

from recommendations_serv.app.data_preparation import get_sentiment_score


# Establish MongoDB connection
def get_mongo_client():
    return MongoClient(os.getenv('MONGO_DB_URI'))

# Initialize global variables
client = get_mongo_client()
db = client['ibooks']
books_collection = db['books']
users_collection = db['users']
reviews_collection = db['reviews']

openai.api_key = OPENAI_API_KEY



def check_book_exists(book):
    # Create a filter based on title and author
    filter = {
        'title': book.get('title'),
        'authors': book.get('authors', 'N/A')
    }
    # Check if the book exists in the database
    return books_collection.find_one(filter)



def check_or_add_book_db(book):
    existing_book = books_collection.find_one({"title": book["title"], "authors": book["authors"]})
    if not existing_book:
        book['_id'] = ObjectId()  # Assign an ObjectId
        books_collection.insert_one(book)
        logging.info(f"Book inserted with ID: {book['_id']}")
    else:
        logging.info(f"Book already exists in the database: {existing_book['_id']}")
    return existing_book or book





def fetch_book_subjects(subject, limit=10, page=1):
    search_url = f"https://openlibrary.org/subjects/{subject}.json?limit={limit}&page={page}"
    try:
        response = requests.get(search_url)
        response.raise_for_status()
        books = response.json().get('works', [])

        # Add cover URLs and ensure book_id is set
        for book in books:
            cover_id = book.get('cover_id')
            if cover_id:
                book['cover_url'] = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
            else:
                book['cover_url'] = r"frontE/styles/defaultimg.png"
            
            # Ensure book_id is set for consistency
            if 'key' in book:
                book['book_id'] = book['key'].split('/')[-1]
            else:
                # Generate a unique id using title and author
                unique_string = book['title'] + '_'.join(book.get('author_name', []))
                book['book_id'] = hashlib.md5(unique_string.encode()).hexdigest()
        
        return books
    except Exception as e:
        logging.error(f"An error occurred while fetching books by subject: {e}")
        return []

def fetch_books_by_title(title):
    search_url = f"https://openlibrary.org/search.json?title={title.replace(' ', '+')}"
    try:
        response = requests.get(search_url)
        response.raise_for_status()
        books = response.json().get('docs', [])

        # Process the books to include cover URLs
        for book in books:
            cover_id = book.get('cover_i')
            if cover_id:
                book['cover_url'] = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
            else:
                book['cover_url'] = r"frontE/styles/defaultimg.png"

        return books
    except Exception as e:
        logging.error(f"An error occurred while fetching books by title: {e}")
        return []


# Fetch most popular articles from NYT
def fetch_most_popular_articles(api_key, time_period=7):
    url = f"https://api.nytimes.com/svc/mostpopular/v2/viewed/{time_period}.json"
    params = {'api-key': api_key}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get('results', [])
    except Exception as e:
        logging.error(f"An error occurred while fetching popular articles: {e}")
        return []


def fetch_book_details(query, max_results=30):
    open_library_url = f"https://openlibrary.org/search.json?q={query}&limit={max_results}"
    response = requests.get(open_library_url)
    if response.status_code != 200:
        logging.error(f"Error fetching book details from Open Library for query {query}: {response.status_code}")
        return []

    books = response.json().get('docs', [])
    book_details = []

    for book in books:
        # Filter books without ratings
        if book.get('ratings_average', 0) == 0:
            continue

        book_in_db = books_collection.find_one({'title': book.get('title', ''), 'authors': {'$in': book.get('author_name', [])}})
        
        if book_in_db:
            book_details.append(book_in_db)
        else:
            details = {
                'title': book.get('title', 'N/A'),
                'authors': ', '.join(book.get('author_name', ['Unknown Author'])),
                'published_year': book.get('first_publish_year', 'Unknown Year'),
                'publisher': ', '.join(book.get('publisher', ['Unknown Publisher'])[:3]),
                'isbn': ', '.join(book.get('isbn', ['N/A'])[:3]),
                'cover_url': f"https://covers.openlibrary.org/b/id/{book.get('cover_i')}-L.jpg",
                'ratings_average': book.get('ratings_average', 0.0),
                'ratings_count': book.get('ratings_count', 0),
                'already_read_count': book.get('already_read_count', 0),
                'summary': book.get('summary', 'No summary available'),
                'categories': book.get('subjects', ['None'])
            }
            
            details = fetch_additional_book_details(details)
            inserted_id = books_collection.insert_one(details).inserted_id
            details['_id'] = inserted_id
            book_details.append(details)

    return book_details

def fetch_additional_book_details(book):
    if book['isbn'] != 'N/A':
        isbn_list = book['isbn'].split(', ')
        for isbn in isbn_list:
            google_books_url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
            response = requests.get(google_books_url)
            if response.status_code == 200:
                items = response.json().get('items', [])
                if items:
                    volume_info = items[0].get('volumeInfo', {})
                    book['summary'] = volume_info.get('description', book['summary'])
                    book['categories'] = volume_info.get('categories', book['categories'])
                    return book
    return book
    # if book['summary'] == 'None':
    #     book['summary'] = generate_summary(book['title'], book['authors'])




# Fetch book by ID
def fetch_book_by_id(book_id):
    try:
        book = books_collection.find_one({'_id': ObjectId(book_id)})
        if book:
            return book
        else : 
            return print("no book found in the search  ")
    except Exception as e:
        logging.error(f"Error fetching book by ID: {e}")
        return {}
    
    
# Check if book is in "already read" collection
def is_book_in_AR(user_pseudo, book_id):
    user = users_collection.find_one({'pseudo': user_pseudo})
    if user:
        fav_books_ids = user.get('already_read', [])
        return book_id in fav_books_ids
    logging.error(f"User {user_pseudo} not found")
    return False


# Add book to "already read" collection
def add_book_to_already_read(user_pseudo, book_id):
    try:
        with get_mongo_client() as client:
            db = client['ibooks']
            users_collection = db['users']
            books_collection = db['books']

            user = users_collection.find_one({'pseudo': user_pseudo})
            book = books_collection.find_one({'_id': ObjectId(book_id)})

            if user and book:
                users_collection.update_one(
                    {'pseudo': user_pseudo},
                    {'$addToSet': {'already_read': book_id}}
                )
                # log_interaction(user_pseudo, book_id,'read' )
                return True
            return False
    except Exception as e:
        logging.error(f"An error occurred while adding the book to already read: {e}")
        return False
    
def add_review_and_update(user_pseudo, book_id, review_text, rating):
     with get_mongo_client() as client:
        db = client['ibooks']
        reviews_collection = db['reviews']
        
        sentiment_score = get_sentiment_score(review_text)
        reviews_collection.insert_one({
            'user_pseudo': user_pseudo,
            'book_id': book_id,
            'review_text': review_text,
            'sentiment_score': sentiment_score,
            'rating' : rating,
            'review_date': datetime.datetime.now(datetime.timezone.utc)
        })
        # log_interaction(user_pseudo, book_id, 'review')
        # update_model()



# Add book to wishlist
def add_book_to_wishlist(user_pseudo, book_id):
    try:
        users_collection.update_one(
            {'pseudo': user_pseudo},
            {'$addToSet': {'wishlist': book_id}}
        )
        # log_interaction(user_pseudo, book_id, 'wishlist')
        st.success(f"Book added to your wishlist.")
        return True
    except Exception as e:
        logging.error(f"Error adding book to wishlist: {e}")
        return False

# Fetch wishlist books
def fetch_wishlist_books(user_pseudo):
    try:
        user = users_collection.find_one({'pseudo': user_pseudo})
        if user:
            wishlist = user.get('wishlist', [])
            return [fetch_book_by_id(book_id) for book_id in wishlist]
        return []
    except Exception as e:
        logging.error(f"Error fetching wishlist books: {e}")
        return []


# Update reading goal
def update_reading_goal(user_pseudo, new_goal):
    try:
        users_collection.update_one(
            {'pseudo': user_pseudo},
            {'$set': {'reading_goals.goal': new_goal}}
        )
    except Exception as e:
        logging.error(f"Error updating reading goal: {e}")





# def check_or_add_book_db(book):
#     try:
#         with get_mongo_client() as client:
#             db = client['ibooks']
#             books_collection = db['books']

#             # Check if book is already in the database by matching specific book details (e.g., title and author)
#             book_in_db = books_collection.find_one({
#                 'title': book.get('title', ''),
#                 'authors': {'$in': book.get('author_name', ['N/A'])}
#             })

            # if not book_in_db:
                # # Fetch additional book details from Google Books API if ISBN is available
                # isbn = book.get('isbn', [])[0] if isinstance(book.get('isbn'), list) else book.get('isbn', '')
                # google_books_api_url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
                # response = requests.get(google_books_api_url)
                # google_book_data = response.json().get('items', [])[0].get('volumeInfo', {}) if response.status_code == 200 else {}

                # book_data = {
                #     '_id': ObjectId(),  # Generate a new ObjectId
                #     'isbn': isbn,
                #     'title': book.get('title', ''),
                #     'authors': ', '.join(book.get('author_name', ['N/A'])[:3]),  # Take the first 3 authors
                #     'published_year': book.get('first_publish_year', 'N/A'),
                #     'publisher': ', '.join(book.get('publisher', ['N/A'])[:3]),  # Take the first 3 publishers
                #     'cover_url': f"https://covers.openlibrary.org/b/id/{book.get('cover_i')}-L.jpg" if book.get('cover_i') else r"frontE\styles\defaultimg.png",
                    # 'ratings_average': book.get('ratings_average', 0),
                    # 'ratings_count': book.get('ratings_count', 0),
                    # 'already_read_count': book.get('already_read_count', 0),
                #     'summary': google_book_data.get('description', ''),
                # }

                # # Insert new book into the database
                # books_collection.insert_one(book_data)
                # logging.info(f"Inserted book: {book_data['title']} with ID: {book_data['_id']}")
                # return book_data['_id']
#             else:
#                 logging.info(f"Book already exists in the database: {book_in_db['title']}")
#                 return book_in_db['_id']
#     except Exception as e:
#         logging.error(f"An error occurred while doing the check or add func to the database: {e}")
#         return None

############################################################################
###########################################################################
## -------- BOOK SUBJECT SEARCH ---------------------------
# def fetch_book_subjetcs(subject, limit=10, page=1):
#     search_url = f"https://openlibrary.org/subjects/{subject}.json?limit={limit}&page={page}"
#     try:
#         response = requests.get(search_url)
#         response.raise_for_status()
#         books = response.json().get('works', [])

#         for book in books:
#             cover_id = book.get('cover_url')
#             if cover_id:
#                 book['cover_url'] = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
#             else:
#                 book['cover_url'] = r"frontE\styles\defaultimg.png"

#             # Ensure book_id is set for consistency
#             if 'key' in book:
#                 book['book_id'] = book['key'].split('/')[-1]
#             else:
#                 # Generate a unique id using title and author
#                 unique_string = book['title'] + ''.join(book.get('author_name', [])) if 'author_name' in book else book['title']
#                 book['book_id'] = hashlib.md5(unique_string.encode()).hexdigest()
        
#         return books
#     except Exception as e:
#         logging.error(f"An error occurred while fetching books by subject: {e}")
#         return []