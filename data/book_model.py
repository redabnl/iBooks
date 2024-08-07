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

# Ensure book is added to the database and return its ID

# books_collection.create_index([('title', pymongo.ASCENDING), ('authors', pymongo.ASCENDING)], unique=True)

def check_book_exists(book):
    # Create a filter based on title and author
    filter = {
        'title': book.get('title'),
        'authors': book.get('authors', 'N/A')
    }
    # Check if the book exists in the database
    return books_collection.find_one(filter)


# def add_book_to_db(book):
#     try:
#         # Insert the book into the database
        
#         ## 
#         result= books_collection.insert_one(book)
#         book_id = result.inserted_id
#         logging.info(f"Book inserted with ID: {book_id}")
#          # Fetch additional book details from Google Books API if ISBN is available
#         isbn = book.get('isbn', [])[0] if isinstance(book.get('isbn'), list) else book.get('isbn', '')
        
#         google_books_api_url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
#         response = requests.get(google_books_api_url)
#         google_book_data = response.json().get('items', [])[0].get('volumeInfo', {}) if response.status_code == 200 else {}

#         book_data = {
#             '_id': book_id,  # Generate a new ObjectId
#             'isbn': isbn,
#             'title': book.get('title', ''),
#             'authors': ', '.join(book.get('author_name', ['N/A'])[:3]),  # Take the first three authors
#             'published_year': book.get('first_publish_year', 'N/A'),
#             'publisher': ', '.join(book.get('publisher', ['N/A'])[:3]),  # Take the first three publishers
#             'cover_url': f"https://covers.openlibrary.org/b/id/{book.get('cover_i')}-L.jpg" if book.get('cover_i') else r"frontE\styles\defaultimg.png",
#             'ratings_average': book.get('ratings_average', 0),
#             'ratings_count': book.get('ratings_count', 0),
#             'already_read_count': book.get('already_read_count', 0),
#             'summary': google_book_data.get('description', ''),
#         }

#         # Insert new book into the database
#         books_collection.insert_one(book_data)
#         logging.info(f"Inserted book: {book_data['title']} with ID: {book_data['_id']}")
#         return book_data['_id']
#         # return result.inserted_id
#     except Exception as e:
#         logging.error(f"An error occurred while adding the book to the database: {e}")
#         return None



def check_or_add_book_db(book):
    existing_book = books_collection.find_one({"title": book["title"], "authors": book["authors"]})
    if not existing_book:
        book['_id'] = ObjectId()  # Assign an ObjectId
        books_collection.insert_one(book)
        logging.info(f"Book inserted with ID: {book['_id']}")
    else:
        logging.info(f"Book already exists in the database: {existing_book['_id']}")
    return existing_book or book

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
                #     'authors': ', '.join(book.get('author_name', ['N/A'])[:3]),  # Take the first three authors
                #     'published_year': book.get('first_publish_year', 'N/A'),
                #     'publisher': ', '.join(book.get('publisher', ['N/A'])[:3]),  # Take the first three publishers
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
#         logging.error(f"An error occurred while checking or adding book to the database: {e}")
#         return None




# Fetch books by subject
# def fetch_book_subjects(subject, limit=9, page=1):
#     search_url = f"https://openlibrary.org/subjects/{subject}.json?limit={limit}&page={page}"
#     try:
#         response = requests.get(search_url)
#         response.raise_for_status()
#         books = response.json().get('works', [])

#         book_details = []
#         for book in books:
#             book_in_db = books_collection.find_one({'title': book.get('title', ''), 'authors': ', '.join(book.get('author_name', []))})
#             if book_in_db:
#                 print(f"book already in db.")
#                 book_details.append(book_in_db)
            
#             else :
#              # Fetch additional details for each book
#                 book_key = book.get('key', '')
#                 if book_key:
#                     additional_details = fetch_additional_book_details_from_key(book_key)
#                     if additional_details:
#                         book_details.append(additional_details)
                

#         return book_details
#     except Exception as e:
#         logging.error(f"An error occurred while fetching books by subject: {e}")
#         return []
            # Skip books without a rating average
            # if 'ratings_average' not in book:
            #     continue

            # Check if book already exists in the database
            
                
            # else:
            #     details = {
            #         'title': book.get('title', 'N/A'),
            #         'authors': ', '.join(book.get('author_name', [])),
            #         'published_year': book.get('first_publish_year', 'N/A'),
            #         'publisher': ', '.join(book.get('publisher', ['N/A'])),
            #         'isbn': ', '.join(book.get('isbn', [])[:3]),
            #         'cover_url': f"https://covers.openlibrary.org/b/id/{book.get('cover_id', 'default')}-L.jpg",
            #         'ratings_average': book.get('ratings_average', 0),
            #         'ratings_count': book.get('ratings_count', 0),
            #         'already_read_count': book.get('already_read_count', 0),
            #         'summary': book.get('summary', 'None'),
            #         'categories': ', '.join(book.get('subject', ['N/A']))
            #     }

                # If summary is missing, generate it using OpenAI
                # if details['summary'] == 'None':
                #     details['summary'] = generate_summary(details['title'], details['authors'])

                


# def fetch_book_subjects(subject, limit=9, page=1):
#     search_url = f"https://openlibrary.org/subjects/{subject}.json?limit={limit}&page={page}"
#     try:
#         response = requests.get(search_url)
#         response.raise_for_status()
#         books = response.json().get('works', [])
#         book_details = []

#         for book in books:
#             book_key = book.get('key', '')
#             if book_key:
#                 additional_details = fetch_additional_book_details_from_key(book_key)
#                 if additional_details:
#                     book_details.append(additional_details)

#         return book_details
#     except Exception as e:
#         logging.error(f"An error occurred while fetching books by subject: {e}")
#         return []


# def fetch_book_subjects(subject, limit=50, page=1):
#     search_url = f"https://openlibrary.org/subjects/{subject}.json?limit={limit}&offset={(page-1)*limit}"
#     try:
#         response = requests.get(search_url)
#         response.raise_for_status()
#         books = response.json().get('works', [])

#         # Add cover URLs and ensure book_id is set
#         for book in books:
#             cover_id = book.get('cover_id')
#             if cover_id:
#                 book['cover_url'] = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
#             else:
#                 book['cover_url'] = r"C:\Users\surface\Desktop\PORTEFOLIO\bookAppDemo\redasbooks\frontE\styles\defaultimg.png"

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


# def fetch_additional_book_details(book):
#     details = {
#         'isbn': ', '.join(book.get('isbn', [])),
#         'summary': book.get('summary', 'None'),
#         'categories': ', '.join(book.get('subjects', 'None'))
#     }
    
#     if not details['summary'] or details['summary'] == 'None':
#         details['summary'] = generate_summary(book.get('title', 'Unknown Title'), book.get('authors', []))
    
#     return details

def generate_summary(title, authors):
    prompt = f"Generate a brief summary for the book titled '{title}' by {', '.join(authors)}."
    response = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=150)
    summary = response.choices[0].text.strip()
    return summary

# def fetch_book_subject(subject, limit=9, page=1):
#     search_url = f"https://openlibrary.org/subjects/{subject}.json?limit={limit}&page={page}"
#     try:
#         response = requests.get(search_url)
#         response.raise_for_status()
#         books = response.json().get('works', [])
        
#         book_details = []
        
#         for book in books:
#             book_in_db = books_collection.find_one({'title': book.get('title', ''), 'authors': ', '.join(book.get('authors', []))})
            
#             if book_in_db:
#                 book_details.append(book_in_db)
#             else:
#                 # Safely join lists of strings
#                 def safe_join(items):
#                     return ', '.join([item for item in items if isinstance(item, str)])
                
#                 details = {
#                     'title': book.get('title', 'N/A'),
#                     'authors': safe_join(book.get('authors', [])),
#                     'published_year': book.get('first_publish_year', 'N/A'),
#                     'publisher': safe_join(book.get('publishers', [])),
#                     'cover_url': f"https://covers.openlibrary.org/b/id/{book.get('cover_id', 'default')}-L.jpg",
#                     'ratings_average': book.get('ratings_average', 0),
#                     'ratings_count': book.get('ratings_count', 0),
#                     'already_read_count': book.get('already_read_count', 0),
#                 }
                
#                 additional_details = fetch_additional_book_details(book)
#                 details.update(additional_details)
                
#                 inserted_id = books_collection.insert_one(details).inserted_id
#                 details['_id'] = inserted_id
#                 book_details.append(details)
        
#         return book_details
#     except Exception as e:
#         logging.error(f"An error occurred while fetching books by subject: {e}")
#         return []
# Note: Ensure generate_summary function and openai.Completion.create() are updated as per the latest API.

    
    
# def generate_summary(title, authors):
#     prompt = f"Generate a summary for the book titled '{title}' written by {authors}."

#     response = openai.completions.create(
#         engine="text-davinci-003",
#         prompt=prompt,
#         max_tokens=150
#     )

#     return response.choices[0].text.strip()

############################################################################
###########################################################################
## -------- BOOK SUBJECT SEARCH ---------------------------
# def fetch_book_subjetcs(subject, limit=10, page=1):
#     search_url = f"https://openlibrary.org/subjects/{subject}.json?limit={limit}&page={page}"
#     try:
#         response = requests.get(search_url)
#         response.raise_for_status()
#         books = response.json().get('works', [])

#         # Add cover URLs and ensure book_id is set
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

# Fetch book details by search query
# def fetch_book_details(search_query, limit=9, page=1):
#     search_url = f"https://openlibrary.org/search.json?q={search_query}&limit={limit}&page={page}"
#     try:
#         response = requests.get(search_url)
#         response.raise_for_status()
#         books = response.json().get('docs', [])
#         filtered_books = [books_collection.find_one({'_id': check_or_add_book_db(book)}) for book in books if book.get('ratings_average') and book.get('ratings_count')]
#         return [book for book in filtered_books if book]
#     except Exception as e:
#         logging.error(f"Error fetching data: {e}")
#         return []

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


# def generate_summary(title, authors):
#     prompt = f"Generate a brief summary for the book titled '{title}' by {authors}."
#     response = openai.Completion.create(
#         model="text-davinci-003",
#         prompt=prompt,
#         max_tokens=150,
#         n=1,
#         stop=None,
#         temperature=0.7
#     )
#     return response.choices[0].text.strip()
# def fetch_book_details(query):
#     # Step 1: Search using Open Library API
#     open_library_url = f"https://openlibrary.org/search.json?q={query}&limit=1"
#     response = requests.get(open_library_url)
#     data = response.json()
    
#     if not data['docs']:
#         return None  # No results found
    
#     book = data['docs'][0]
    
#     # Basic book details from Open Library API
#     book_details = {
#         'title': book.get('title', 'N/A'),
#         'authors': book.get('author_name', ['N/A']),
#         'isbn': book.get('isbn', ['N/A'])[0] if 'isbn' in book else 'N/A',
#         'cover_url': f"http://covers.openlibrary.org/b/id/{book.get('cover_i', 'default')}-L.jpg",
#         'published_year': book.get('first_publish_year', 'N/A'),
#         'publisher': book.get('publisher', ['N/A'])[:3],  # Limit to first 3 publishers
#         'summary': None,
#         'categories': book.get('subject', ['N/A'])[:3],  # Limit to first 3 categories
#     }
    
#     # Step 2: Fetch missing details from Google Books API
#     google_books_url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{book_details['isbn']}"
#     response = requests.get(google_books_url)
#     data = response.json()
    
#     if 'items' in data and data['items']:
#         volume_info = data['items'][0]['volumeInfo']
#         book_details['summary'] = volume_info.get('description', None)
#         book_details['categories'] = volume_info.get('categories', book_details['categories'])[:3]
    
#     # Step 3: Generate summary using OpenAI if still missing
#     if not book_details['summary']:
#         prompt = f"Write a brief summary for the book titled '{book_details['title']}' by {', '.join(book_details['authors'][:3])}."
#         response = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=150)
#         book_details['summary'] = response.choices[0].text.strip()
    
#     return book_details


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


# def log_interaction(user_pseudo, book_id, interaction_type):
#     interaction_collection = db['interactions']
#     interaction_collection.insert_one({
#         'user_id': user_pseudo,
#         'book_id': book_id,
#         'interaction_type': interaction_type,
#         'timestamp': datetime.now(datetime.timezone.utc)
        
#     })

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


# Add review to book
# def add_review_to_book(user_pseudo, book_id, review_text, rating):
#     try:
#         with get_mongo_client() as client:
#             db = client['ibooks']
#             reviews_collection = db['reviews']
#             users_collection = db['users']
#             books_collection = db['books']

#             user = users_collection.find_one({'pseudo': user_pseudo})
#             book = books_collection.find_one({'_id': ObjectId(book_id)})

#             if user and book:
#                 review = {
#                     "user_pseudo": user['pseudo'],
#                     "book_id": book['_id'],
#                     "review_text": review_text,
#                     "rating": rating,
#                     "review_date": datetime.datetime.utcnow()
#                 }
#                 result = reviews_collection.insert_one(review)
#                 review_id = result.inserted_id

#                 # Update user_reviews array in the user's document
#                 users_collection.update_one(
#                     {'pseudo': user_pseudo},
#                     {'$addToSet': {'user_reviews': review_id}}
#                 )
#                 return True
#             return False
#     except Exception as e:
#         logging.error(f"An error occurred while adding the review: {e}")
#         return False


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



# def add_review_to_book(user_pseudo,isbn,rating, review_text):
#     try:
#         review = {
#         "user_pseudo": user_pseudo,
#         "isbn": isbn,
#         "rating": rating,
#         "review_text": review_text,
#         "review_date": datetime.datetime.utcnow()
#         }
    
#         # Insert review into the reviews collection
#         review_id = reviews_collection.insert_one(review).inserted_id
        
#         # Update the user's document to include the new review
#         users_collection.update_one(
#             {"pseudo": user_pseudo},
#             {"$push": {"user_reviews": review_id}}
#         )
        
#         # Update the book's document to include the new review
#         books_collection.update_one(
#             {"isbn": isbn},
#             {"$push": {"user_reviews": review_id}}
#         )
        
#         print("Review added successfully.")
#     except Exception as e:
#         print(f"An error occurred while adding the review: {e}")
#         return False



# def validate_and_prepare_book_data(book):
#     isbn = book.get('isbn', [None])[0]
#     if not isbn:
#         return None

#     google_books_details = fetch_google_books_details(book.get('title'))
    
#     book_data = {
#         'isbn': isbn,
#         'title': book.get('title', ''),
#         'authors': book.get('author_name', ['N/A']),
#         'published_year': book.get('first_publish_year', 'N/A'),
#         'publisher': book.get('publisher', 'N/A'),
#         'cover_url': f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg" if 'isbn' in book else r"frontE\styles\defaultimg.png",
#         'ratings_average': book.get('ratings_average', 0),
#         'ratings_count': book.get('ratings_count', 0),
#         'already_read_count': book.get('already_read_count', 0),
#         'summary': google_books_details.get("description", "") if google_books_details else "",
#         'categories': google_books_details.get("categories", []) if google_books_details else []
#     }

#     # Generate a summary if it's not available
#     if not book_data['summary']:
#         book_data['summary'] = generate_summary(book_data['title'], ', '.join(book_data['authors']))
    
#     # Ensure authors are a list
#     if not isinstance(book_data['authors'], list):
#         book_data['authors'] = [book_data['authors']]
    
#     return book_data

# def check_or_add_book_db(book):
#     try:
#         db = client['ibooks']
#         books_collection = db['books']
#         book_data = validate_and_prepare_book_data(book)
#         if not book_data:
#             return 'N/A'

#         book_in_db = books_collection.find_one({'isbn': book_data['isbn']})

#         if not book_in_db:
#             inserted_book = books_collection.insert_one(book_data)
#             book_data['_id'] = inserted_book.inserted_id
#             logging.info(f"Inserted book: {book_data['title']}, ID: {book_data['_id']}")
#             return book_data['_id']
#         else:
#             logging.info(f"Book already stored with ID: {book_in_db['_id']}, ISBN: {book_data['isbn']}")
#             return book_in_db['_id']
#     except Exception as e:
#         logging.error(f"An error occurred: {e}")
#         return 'N/A'



# def fetch_book_details(search_query, limit=9, page=1):
#     search_url = f"https://openlibrary.org/search.json?q={search_query}&limit={limit}&page={page}"
#     try:
#         response = requests.get(search_url)
#         response.raise_for_status()
#         data = response.json()
#         books = data.get('docs', [])
#         filtered_books = []

#         with get_mongo_client() as client:
#             db = client['ibooks']
#             books_collection = db['books']

#             for book in books:
#                 if 'ratings_average' in book and 'ratings_count' in book:
#                     isbn = book.get('isbn', [None])[0]
#                     if isbn:
#                         isbn_value = isbn if isinstance(isbn, list) else isbn
#                         book_in_db = books_collection.find_one({'isbn': isbn_value})

#                         if not book_in_db:
#                             google_books_details = fetch_google_books_details(book.get('title'))
#                             book_data = {
#                                 'isbn': isbn_value,
#                                 'title': book.get('title', ''),
#                                 'authors': book.get('author_name', ['N/A']),
#                                 'published_year': book.get('first_publish_year', 'N/A'),
#                                 'publisher': book.get('publisher', 'N/A'),
#                                 'cover_url': f"https://covers.openlibrary.org/b/isbn/{isbn_value}-L.jpg" if 'isbn' in book else r"frontE\styles\defaultimg.png",
#                                 'ratings_average': book.get('ratings_average', 0),
#                                 'ratings_count': book.get('ratings_count', 0),
#                                 'already_read_count': book.get('already_read_count', 0),
#                                 'summary': google_books_details.get("description", "") if google_books_details else "",
#                                 'categories': google_books_details.get("categories", []) if google_books_details else []
#                             }

#                             if not book_data['summary']:
#                                 book_data['summary'] = generate_summary(book_data['title'], ', '.join(book_data['authors']))

#                             inserted_book = books_collection.insert_one(book_data)
#                             book_data['_id'] = inserted_book.inserted_id
#                             filtered_books.append(book_data)
#                         else:
#                             filtered_books.append(book_in_db)

#             return filtered_books
#     except requests.exceptions.RequestException as e:
#         logging.error(f"Error fetching data from Open Library API: {e}")
#         return []
#     except ValueError as e:
#         logging.error(f"Error parsing response: {e}")
#         return []


# with get_mongo_client() as client:
        #     db = client['ibooks']
        #     reviews_collection = db['reviews']
        #     users_collection = db['users']

        #     # Create the review document
        #     review_data = {
        #         'user_pseudo': user_pseudo,
        #         'book_id': book_id,
        #         'rating': rating,
        #         'text': review_text,
        #         'date': datetime.datetime.utcnow()
        #     }

        #     # Insert the review into the reviews collection
        #     inserted_review = reviews_collection.insert_one(review_data)
        #     review_id = inserted_review.inserted_id

        #     # Update the user's user_reviews array with the new review ID
        #     users_collection.update_one(
        #         {'pseudo': user_pseudo},
        #         {'$push': {'user_reviews': review_id}}
        #     )

        #     print(f"Review with ID: {review_id} added for book ID: {book_id} by user: {user_pseudo}")
        #     return True
    


# Function to update books collection


# # Function to update users collection
# def update_users_collection():
#     updates = []
#     for user in users_collection.find():
#         update = {
#             "$set": {
#                 "pseudo": user.get("pseudo", ""),
#                 "pwd": user.get("pwd", ""),
#                 "account_creation_date": user.get("account_creation_date", datetime.datetime.utcnow()),
#                 "email": user.get("email", ""),
#                 "isPrivate": user.get("isPrivate", False),
#                 "role": user.get("role", "user"),
#                 "user_reviews": user.get("user_reviews", []),
#                 "already_read": user.get("already_read", []),
#                 "reading_goals": user.get("reading_goals", {"yearly_goal": 0, "current_progress": 0}),
#                 "wishlist": user.get("wishlist", [])
#             }
#         }
#         updates.append(UpdateOne({"_id": user["_id"]}, update))
    
#     if updates:
#         users_collection.bulk_write(updates)
#     print("Users collection updated successfully.")

# # Function to migrate reviews to a new reviews collection
# def migrate_reviews():
#     reviews = []
#     for user in users_collection.find():
#         for review in user.get("user_reviews", []):
#             # Ensure review is a dictionary or properly formatted
#             if isinstance(review, dict):
#                 reviews.append({
#                     "user_id": user["_id"],  # ObjectId
#                     "isbn": review.get("isbn", ""),
#                     "rating": review.get("rating", 0),
#                     "review_text": review.get("review_text", ""),
#                     "review_date": review.get("review_date", datetime.datetime.utcnow())
#                 })
#             else:
#                 print(f"Skipping invalid review format for user {user['_id']}: {review}")

#     if reviews:
#         reviews_collection.insert_many(reviews)
#     print("Reviews migrated successfully.")

# # Execute updates
# # update_books_collection()
# # update_users_collection()
# # migrate_reviews()


# def update_books_collection():
#     updates = []
#     for book in books_collection.find():
#         update = {
#             "$set": {
#                 "isbn": book.get("isbn", ""),
#                 "title": book.get("title", ""),
#                 "authors": book.get("author", ""),
#                 "published_year": book.get("published_year", 0),
#                 "publisher": book.get("publisher", []),
#                 "cover_url": book.get("cover_url", ""),
#                 "ratings_average": book.get("ratings_average", 0.0),
#                 "ratings_count": book.get("ratings_count", 0),
#                 "already_read_count": book.get("already_read_count", 0), 
#                 "summary" : book.get("summary",""),
#                 "categories" : book.get("categories", [])
#             }
#         }
#         updates.append(UpdateOne({"_id": book["_id"]}, update))
    
#     if updates:
#         books_collection.bulk_write(updates)
#     print("Books collection updated successfully.")


# update_books_collection()


###############################################################
# def add_book_to_already_read(user_pseudo, book_id):
#     with get_mongo_client() as client :
#         db = client['ibooks']
#         user_collection = db['users']
#         user_pseudo = st.session_state['current_user']
#         user = user_collection.find_one({"pseudo" : user_pseudo})
#         current_read_count = len(user.get('already_read', []))
        
#         if user : 
#             read_books = user.get('already_read', [])
#             if book_id not in read_books : 
#                 user_collection.update_one(
#                     {'pseudo' : user_pseudo},
#                     {'$push' : {'already_read' : book_id}}
#                 )
#                 # st.session_state['already_read'].append(book_id)
#                 print(f"boook with ID : {book_id} added to {user_pseudo}'s biblio")
#                 current_book_read = user.get('reading_goal', {}).get('books_read', 0)
#                 new_book_read = current_book_read + 1
#                 user.update_one({'pseudo': user_pseudo}, 
#                                 {'$set': {
#                             'already_read': read_books,
#                             'reading_goal.books_read': new_book_read
#                         }
#                                  })
#                 print(f"{user_pseudo}'s read count for now is {current_read_count}")
#             else : 
#                 print(f"Book {book_id} is already in {user_pseudo}'s already read collection")

#         else :
#             print(f"user pseudo {user_pseudo} hasn't been found")

# def add_book_to_already_read(user_pseudo, book_id):
#     print(f"book's ID to be added {book_id}")
#     with get_mongo_client() as client :
#         db = client['ibooks']
#         users_collection = db['users']
#         user_pseudo = st.session_state['current_user']
#         user = users_collection.find_one({"pseudo": user_pseudo})
#         if user:
#             read_books_ids = user.get('read_books', [])
#             if book_id not in read_books_ids:
#                 users_collection.update_one(
#                     {'pseudo' : user_pseudo},
#                     {'$push' : {'already_read': book_id}}
#                 )
#                 st.session_state['already_read'].append(book_id)
#                 st.session_state['button_clicked'] = True
#                 # read_books_ids.append(book_id)
#                 # users_collection.update_one({'pseudo': user_pseudo}, {'$set': {'read_books': book_id}})
#                 print(f"Book {book_id} added to {user_pseudo}'s biblio.")
#             elif book_id in read_books_ids:
#                 print(f"book with ID {book_id} is already registred")
#             else:
#                 print(f"error somewhere : {Exception}")
#         else:
#             print(f"User {user_pseudo} not found.")  
       
##########################################################
##########################################################
## ADDING A NEW "ALREADY READ" OPTION FOR BOOKS INSTEAD OF FAVS
## USEFULL FOR REAL TIME LEARNING FOR OUR PREDICTION MODEL
   
        
        
    
    # with get_mongo_client() as client:
    #     db = client['ibooks']
    #     users_collection = db['users']
    #     user_pseudo = st.session_state['current_user']
        
    #     user = users_collection.find_one({'pseudo': user_pseudo})
    #     if user:
    #         already_read_books = user.get('already_read', [])
    #         print(f"user's already read books : \n {already_read_books}")
    #         if book_id not in already_read_books:
    #             print(f"adding book with ID {book_id} to {user_pseudo}'s biblio")
    #             already_read_books.append(book_id)
    #             users_collection.update_one({'pseudo': user_pseudo}, {'$set': {'already_read': already_read_books}})
    #             return True
        
    # except Exception as e:
    #     print(f"An error occurred: {e}")
    #     return False



    # base_url = "https://openlibrary.org/search.json"
    # params = {"q": search_query}
    # response = requests.get(base_url, params=params)
    # response = requests.get(search_url)
    # if response.status_code == 200:
    #     results = response.json()
    #     books = results.get('docs', [])
    #     if books:
    #         unique_books = []
    #         seen_isbns = set()
    #         for book in books:
                
    #             isbn_list = book.get('isbn', [])
    #             if isbn_list:
    #                 isbn = isbn_list[0]
    #                 print(f"book's ISBN fetched : {isbn} \n ")
    #                 if isbn not in seen_isbns:
    #                     seen_isbns.add(isbn)
    #                     unique_books.append(book)
    #             if len(unique_books) >= limit:
    #                 break
            
    #         return {'docs': unique_books}
    #     else:
    #         return "error fetching the books !"
    # return None

       
    # try:
    #     db = client['ibooks']
    #     users = client['users']
        # isbn = book.get('isbn', [])[0]
        # if isbn:
        #     isbn_value = isbn if isinstance(isbn, list) else isbn  # makin sure the ISBN single value
        #     book_in_db = db.books.find_one({'ISBN': isbn_value})
        #     is_book_in_favs
        #     if not book_in_db:
        #         book_data = {
        #             'ISBN' : isbn_value, 
        #             'title' : book.get('title', ''), 
        #             'author': ','.join(book.get('author_name', [])),
        #             'published_year': book.get('first_publish_year'),
        #             'summary': book.get('summary', 'N/A'),
        #             'cover_url': f"https://covers.openlibrary.org/b/isbn/{book['isbn']}-M.jpg" if book['isbn'] != 'N/A' else None,
        #             'ratings_average': book.get('ratings_average', 0),
        #             'ratings_count': book.get('ratings_count', 0),
        #             'already_read': 0
                    
        #         }
                
        #         book_id = db.books.insert_one(book_data).inserted_id
        #         book['_id'] = book_id
        #         return book_id
                
        #     else :
        #         book['_id'] = book_in_db['_id']
        #         return book['id']
            
    #     else:
    #         raise ValueError("Book does not have a valid ISBN")
    # except Exception as e:
    #     print(f"An error occurred: {e}")
    #     return None   
       
     
    # try:
    #     with get_mongo_client() as client:
    #         db = client['ibooks']
    #         books_collection = db['books']

    #         # Check if the book already exists by ISBN
    #         existing_book = books_collection.find_one({'isbn': book['isbn']})
    #         if existing_book:
    #             return existing_book['_id']
    #         else:
    #             # Extract necessary fields
    #             book_data = {
    #                 'isbn': book.get('isbn', 'N/A'),
    #                 'title': book.get('title', 'N/A'),
    #                 'author': ' ,'.join(book.get('authors', [])),
    #                 'published_year': book.get('first_publish_year', 'Unknown'),
    #                 'summary': book.get('summary', 'N/A'),
    #                 'cover_url': f"https://covers.openlibrary.org/b/isbn/{book['isbn']}-M.jpg" if book['isbn'] != 'N/A' else None,
    #                 'ratings_average': book.get('ratings_average', 0),
    #                 'ratings_count': book.get('ratings_count', 0),
    #                 'already_read': 0
    #             }

    #             # Add new book to the database
    #             inserted = books_collection.insert_one(book_data)
    #             print(f"book inserted : \n {book_data}")
    #             return inserted.inserted_id
    # except Exception as e:
    #     print(f"An error occurred: {e}")
    #     return None
    

        
        




# def display_book_details(book):
#     st.write(f"### Title: {book['title']}")
#     st.write(f"**Author:** {book['author']}")
#     st.write(f"**Published Year:** {book['published_year']}")
#     st.write(f"**ISBN:** {book['isbn'][0]}")
#     st.write(f"[Buy this book](https://cheaper99.com/{book['isbn'][0]})")

#     user_pseudo = st.session_state.get('current_user', 'guest')
#     book_id = book.get('_id', 'No ID av.')

#     if book.get('cover_url'):
#         st.image(book['cover_url'], width=100)
#     else:
#         st.write("No image found")

#     if book_id != 'No ID av.':
#         if st.checkbox(f"Add to 'Already Read' {book['isbn'][0]}", key=f"read_{book['isbn'][0]}"):
#             with get_mongo_client() as client:
#                 db = client['ibooks']
#                 users_collection = db['users']
#                 user = users_collection.find_one({'pseudo': user_pseudo})
#                 if user:
#                     read_books = user.get('read_books', [])
#                     if book['_id'] not in read_books:
#                         read_books.append(book['_id'])
#                         users_collection.update_one({'pseudo': user_pseudo}, {'$set': {'read_books': read_books}})
#                         st.success(f"Added {book['title']} to 'Already Read'")
#     else:
#         st.write("No ID found")




##############################################
## CHECKING IF THE BOOK IS ALREADY IN FAVORITE'S COLLECTION

    
# def add_book_to_favorites(user_pseudo, book_id):
#     with get_mongo_client() as client:
#         db = client['ibooks']
#         users_collection = db['users']
        
#         # Make sure the book_id is a valid ObjectId
#         if not ObjectId.is_valid(book_id):
#             print("Invalid book ID")
#             return False

#         # Convert book_id to string format to store in favBooks as per your database schema
#         book_id_str = str(ObjectId(book_id))
#         user = users_collection.find_one({'pseudo': user_pseudo})
#         if user:
#             fav_books_ids = user.get('favBooks', [])
#             if book_id_str not in fav_books_ids:
#                 fav_books_ids.append(book_id_str)
#                 users_collection.update_one(
#                     {'pseudo': user_pseudo},
#                     {'$set': {'favBooks': fav_books_ids}}
#                 )
#                 print("Book added to favorites")  # Debug message
#                 return True
#             else:
#                 print("Book already in favorites")  # Debug message
#                 return False
#         else:
#             print("User not found")  # Debug message
#             return False

##########################################################
## ADDING BOOK TO USER'S FAVORITE FUNCTIONS 
## PRO        

# def add_to_favorites(user_pseudo, book_id):
    # user = users_collection.find_one({"pseudo": user_pseudo})
    # if user:
    #     # Add the book to the user's favorite books
    #     users_collection.update_one(
    #         {"pseudo": user_pseudo}, 
    #         {"$addToSet": {"favBooks": ObjectId(book_id)}}
    #     )
    #     print(f"Book {book_id} added to {user_pseudo}'s favorites.")
    # else:
    #     print(f"User {user_pseudo} not found.")
        
        
        

    
    
    
############################################################
############################################################
## FUNCTION TO CHECK IF THE BOOK SELECTED IS ALREADY IN THE FAVBOOKS COLLECTION
 

# ######################################################
# def add_to_favorites_new(user_pseudo, book_id):
#     with get_mongo_client() as client:
#         db = client['ibooks']
#         users_collection = db['users']
#         books_collection = db['books']

#         # Validate the book_id
#         if not ObjectId.is_valid(book_id):
#             print("Invalid book ID")
#             return False

#         # Check if the book exists
#         if books_collection.count_documents({'_id': ObjectId(book_id)}) == 0:
#             print("Book not found")
#             return False

#         # Find the user by pseudo and check if the book is already in favorites
#         user = users_collection.find_one({'pseudo': user_pseudo})
#         if not user:
#             print("User not found")
#             return False

#         # Convert book_id to string to match your database favBooks format
#         book_id_str = str(ObjectId(book_id))
#         if book_id_str in user.get('favBooks', []):
#             print("Book already in favorites")
#             return False

#         # Add book_id to the user's favBooks list
#         result = users_collection.update_one(
#             {'pseudo': user_pseudo},
#             {'$addToSet': {'favBooks': book_id_str}}
#         )

#         if result.modified_count == 1:
#             print("Book successfully added to favorites")
#             return True
#         else:
#             print("Failed to add book to favorites")
#             return False
        


# def check_or_add_book_to_db(book):
#     client = get_mongo_client()
#     try:
#         db = client['ibooks']
#         users = client['users']
#         isbn = book.get('isbn', [])[0]
#         if isbn:
#             isbn_value = isbn if isinstance(isbn, list) else isbn  # makin sure the ISBN single value
#             book_in_db = db.books.find_one({'ISBN': isbn_value})
#             is_book_in_favs
#             if not book_in_db:
#                 book_data = {
#                     'ISBN' : isbn_value, 
#                     'title' : book.get('title', ''), 
#                     'author': ','.join(book.get('author_name', [])),
#                     'published_year': book.get('first_publish_year'),
#                     'reviews': []
#                 }
                
#                 book_id = db.books.insert_one(book_data).inserted_id
#                 book['_id'] = book_id
#                 return book_id
                
#             else :
#                 book['_id'] = book_in_db['_id']
#                 return book['id']
            
#         else:
#             raise ValueError("Book does not have a valid ISBN")
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         return None  # Return None if there's an error
    
#     finally:
#         client.close()  # closin the client
    

# def check_or_add_book_db(book):
#     with get_mongo_client() as client:
#         db = client['ibooks']
#         books_collection = db['books']
#         # Assume book has an 'isbn' field which is unique
#         existing_book = books_collection.find_one({'isbn': book['isbn']})
#         if existing_book:
#             return existing_book['_id']
#         else:
#             # Add new book to the database if not exists
#             inserted = books_collection.insert_one(book)
#             return inserted.inserted_id 
    
# # # CHATGPT innovation 
# def add_book_to_favorites(user_pseudo, book_id):
#     with get_mongo_client() as client:
#         db = client['ibooks']
#         users_collection = db['users']
#         books_collection = db['books']

#         user = users_collection.find_one({'pseudo': user_pseudo})
#         if user:
#             fav_books_ids = user.get('favBooks', [])
#             book = books_collection.find_one({'_id': book_id})
#             if book:
#                 if book_id not in fav_books_ids:
#                     fav_books_ids.append(book_id)
#                     users_collection.update_one({'pseudo': user_pseudo}, {'$set': {'favBooks': fav_books_ids}})
#                     return True
#     return False

# def remove_for_favs(user_pseudo, book_id):
#     with get_mongo_client() as client:
#         db = client['ibooks']
#         users_collection = db['users']
#         books_collection = db['books']

#         # Get the ObjectId of the book to be removed
#         book_to_remove = books_collection.find_one({'_id': book_id})
#         if not book_to_remove:
#             return False

#         book_id = book_to_remove['_id']
        
#         result = users_collection.update_one(
#             {'pseudo': user_pseudo},
#             {'$pull': {'favBooks': book_id}}
#         )
#         return result.modified_count > 0
