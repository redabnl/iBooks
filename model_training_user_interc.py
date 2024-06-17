import pandas as pd 
import numpy as np
from data.models import get_mongo_client
import joblib
import pickle
import requests
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from data.book_model import get_all_books, fetch_book_by_id

## FETCHING BOOKS AND USER'S DATA FOR MACHINE LEARNING

def fetch_book_subjects(isbn):
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&jscmd=data&format=json"
    response = requests.get(url)
    data = response.json()
    book_key = f"ISBN:{isbn}"
    if book_key in data:
        book_data = data[book_key]
        subjects = [subject['name'] for subject in book_data.get('subjects', [])]
        return subjects
    return []

def fetch_books_data():
    with get_mongo_client() as client:
        db = client['ibooks']
        books_collection = db['books']
        books_data = list(books_collection.find({}))
    return books_data

def fetch_user_data(user_pseudo):
    with get_mongo_client() as client:
        db = client['ibooks']
        users_collection = db['users']
        reviews_collection = db['reviews']
        
        user_data = users_collection.find_one({'pseudo': user_pseudo})
        read_books = user_data.get('already_read', [])
        
        reviews = []
        for review_id in user_data.get('user_reviews', []):
            review = reviews_collection.find_one({'_id': review_id})
            reviews.append({'book_id': review['book_id'], 'rating': review['rating']})
            
    return read_books, reviews





## TRAINING ON THE MODEL ONTHE PROCESSED DATA

def train_user_model(user_pseudo):
    read_books, reviews = fetch_user_data(user_pseudo)

    # Use subjects instead of descriptions
    book_subjects = []
    ratings = []

    for review in reviews:
        isbn = review['book_id']
        subjects = fetch_book_subjects(isbn)
        if subjects:
            book_subjects.append(" ".join(subjects))
            ratings.append(review['rating'])

    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(book_subjects)
    y = ratings

    model = LogisticRegression()
    model.fit(X, y)

    with open(f'{user_pseudo}_logistic_model.pkl', 'wb') as f:
        pickle.dump((model, vectorizer), f)

    return model, vectorizer

def recommend_books(user_pseudo, threshold=0.1):
    # Fetch user data
    read_books, _ = fetch_user_data(user_pseudo)
    
    if not read_books:
        return []

    # Fetch subjects for the read books
    book_subjects = []
    for book_id in read_books:
        book_data = fetch_book_by_id(book_id)
        isbn = book_data.get('isbn')
        if isbn:
            subjects = fetch_book_subjects(isbn)
            if subjects:
                book_subjects.extend(subjects)
    
    # If no subjects are found, return an empty list
    if not book_subjects:
        return []

    # Fetch all books from the database
    all_books = fetch_books_data()

    # Filter out already read books
    unread_books = [book for book in all_books if book['_id'] not in read_books]

    # Prepare data for vectorization
    all_subjects = [' '.join(fetch_book_subjects(book['isbn'])) for book in unread_books]
    
    if not all_subjects:
        return []

    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(all_subjects)
    
    user_subjects = ' '.join(book_subjects)
    user_vector = vectorizer.transform([user_subjects])

    similarities = cosine_similarity(user_vector, X).flatten()
    similar_books_indices = similarities.argsort()[::-1]

    recommended_books = [unread_books[i] for i in similar_books_indices if similarities[i] > threshold]

    return recommended_books
# def recommend_books(user_pseudo, candidate_books):
#     # Load the user-specific model
#     with open(f'{user_pseudo}_logistic_model.pkl', 'rb') as f:
#         model = pickle.load(f)

#     # Fetch details of candidate books
#     candidate_book_details = fetch_book_details(candidate_books)

#     # Prepare the feature set for candidate books
#     X_candidates = [
#         [
#             book.get('ratings_average', 0),
#             book.get('ratings_count', 0),
#             book.get('already_read_count', 0)
#         ]
#         for book in candidate_book_details
#     ]

#     # Predict ratings for candidate books
#     predicted_ratings = model.predict(X_candidates)

#     # Combine book details with predicted ratings
#     recommendations = [
#         {
#             'book': candidate_book_details[i],
#             'predicted_rating': predicted_ratings[i]
#         }
#         for i in range(len(candidate_books))
#     ]

#     # Sort recommendations by predicted rating
#     recommendations.sort(key=lambda x: x['predicted_rating'], reverse=True)

#     return recommendations