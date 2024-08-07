import random
import numpy as np
from pymongo import MongoClient
from bson.objectid import ObjectId
from implicit.als import AlternatingLeastSquares
from scipy.sparse import coo_matrix, csr_matrix
from dotenv import load_dotenv
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
import os
import datetime

# Load environment variables
load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv('MONGO_DB_URI'))
db = client['ibooks']
user_collection = db['users']
book_collection = db['books']
review_collection = db['reviews']
interaction_collection = db['interactions']

# Fetch users and books
users = list(user_collection.find())
books = list(book_collection.find())
user_ids = np.array([user['pseudo'] for user in users])
item_ids = np.array([str(book['_id']) for book in books])

# Function to update the model
def update_model():
    global interaction_matrix, model
    interaction_matrix = create_interaction_matrix(users, books, interactions)
    if interaction_matrix is not None:
        model.fit(interaction_matrix.tocsr())
        print("Model updated successfully.")
    else:
        print("Interaction matrix creation failed.")

# Add sentiment analysis on users reviews on read books
def get_sentiment_score(review_text):
    analysis = TextBlob(review_text)
    return analysis.sentiment.polarity

for review in review_collection.find():
    sentiment_score = get_sentiment_score(review['review_text'])
    review_collection.update_one(
        {'_id': review['_id']},
        {'$set': {'sentiment_score': sentiment_score}}
    )

# Label encode the book categories
def encode_categories(categories):
    le = LabelEncoder()
    return le.fit_transform(categories)

def preprocess_summaries(summaries):
    processed_summaries = [summary.lower() for summary in summaries]
    return processed_summaries

def convert_summaries_to_tfidf(summaries):
    vectorizer = TfidfVectorizer(max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(summaries)
    return tfidf_matrix, vectorizer

def combine_features(categories, tfidf_matrix):
    combined_features = csr_matrix(np.hstack([categories.reshape(-1, 1), tfidf_matrix.toarray()]))
    return combined_features

def create_interaction_matrix(users, books, interactions):
    rows, cols, data = [], [], []
    user_ids = np.array([user['pseudo'] for user in users])
    item_ids = np.array([str(book['_id']) for book in books])

    for interaction in interactions:
        user_index = np.where(user_ids == interaction['user_id'])[0]
        if user_index.size == 0:
            continue
        user_index = user_index[0]
        book_index = np.where(item_ids == str(interaction['book_id']))[0]
        if book_index.size == 0:
            continue
        book_index = book_index[0]

        rows.append(user_index)
        cols.append(book_index)
        data.append(1)  

    if not rows or not cols or not data:
        print("No interaction data found")
        return None

    interaction_matrix = coo_matrix((data, (rows, cols)), shape=(len(user_ids), len(item_ids)))
    print(f"Interaction matrix shape: {interaction_matrix.shape}")
    print(f"Non-zero entries in interaction matrix: {interaction_matrix.nnz}")
    return interaction_matrix

# Fetch interactions from the interactions collection
interactions = list(interaction_collection.find())

# interaction data print for debugging purps
print(f"Total interactions: {len(interactions)}")
print(interactions[:5])  # first 5 interac

# Preprocess and encode categories and summaries
categories = np.array([book.get('categories', ['None'])[0] if book.get('categories') else 'None' for book in books])
summaries = np.array([book.get('summary', '') for book in books])
encoded_categories = encode_categories(categories)
processed_summaries = preprocess_summaries(summaries)
tfidf_matrix, vectorizer = convert_summaries_to_tfidf(processed_summaries)

# Combine features f
combined_features = combine_features(encoded_categories, tfidf_matrix)

# Create the interaction matrix
interaction_matrix = create_interaction_matrix(users, books, interactions)
if interaction_matrix is not None:
    interaction_matrix_csr = interaction_matrix.tocsr()

    # Initialize the model
    model = AlternatingLeastSquares(factors=50, regularization=0.01, iterations=15)

    # Fit the model
    model.fit(interaction_matrix_csr)
    print("Model updated successfully.")
else:
    print("Interaction matrix creation failed.")

# # Function to calculate moedls metrics for general info to debugg
# def calculate_metrics(interaction_matrix, user_ids, model):
#     precision_list, recall_list = [], []
#     interaction_matrix_csr = interaction_matrix.tocsr()

#     for user_index in range(interaction_matrix.shape[0]):
#         user_interactions = interaction_matrix_csr[user_index].nnz
#         print(f"User index {user_index} has {user_interactions} interactions.")

#         if user_interactions < 5:  # Assuming a minimum of 5 interactions required
#             continue

#         try:
#             print(f"Generating recommendations for user index {user_index}")
#             recommended_items, _ = model.recommend(user_index, interaction_matrix_csr, N=10)
#             print(f"Recommended items for user index {user_index}: {recommended_items}")

#             user_items = interaction_matrix_csr[user_index].indices
#             print(f"User items for user index {user_index}: {user_items}")

#             if user_items.size == 0:
#                 continue

#             user_items_set = set(user_items)
#             recommended_items_set = set(recommended_items)

#             true_positives = len(user_items_set & recommended_items_set)
#             precision = true_positives / len(recommended_items_set) if recommended_items_set else 0
#             recall = true_positives / len(user_items_set) if user_items_set else 0

#             precision_list.append(precision)
#             recall_list.append(recall)
        
#         except ValueError as e:
#             print(f"Error recommending items for user index {user_index}: {e}")

#     if precision_list and recall_list:
#         precision = np.mean(precision_list)
#         recall = np.mean(recall_list)
#         f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
#     else:
#         precision = recall = f1 = 0

#     return precision, recall, f1

# if interaction_matrix is not None:
#     precision, recall, f1 = calculate_metrics(interaction_matrix, user_ids, model)
#     print(f"Precision: {precision}, Recall: {recall}, F1 Score: {f1}")
# else:
#     print("Metrics calculation failed due to empty interaction matrix.")




def recommend_books(user_id, user_ids, item_ids, model, interaction_matrix, num_recommendations=10):
    user_index = np.where(user_ids == user_id)[0][0]
    user_interaction = interaction_matrix.tocsr()[user_index]

    print(f"User index for {user_id}: {user_index}")
    print(f"User interaction matrix row: {user_interaction}")

    try:
        recommended_items, _ = model.recommend(user_index, user_interaction, N=num_recommendations)
        print(f"Recommended items for user {user_id}: {recommended_items}")
        
        # Fetch book details for each recommended item
        recommended_books = []
        for item in recommended_items:
            book_id = item_ids[item]
            book = book_collection.find_one({"_id": ObjectId(book_id)})
            if book:
                recommended_books.append({
                    "book_id": book_id,
                    "title": book.get("title", "Unknown Title"),
                    "author": book.get("authors", ["Unknown Author"])
                })

        return recommended_books
    except ValueError as e:
        print(f"Error recommending items for user {user_id}: {e}")
        print(f"Interaction matrix row for user {user_id}: {user_interaction}")
        return []


def fetch_book_details(book_ids):
    books = []
    for book_id in book_ids:
        try:
            book = book_collection.find_one({"_id": ObjectId(book_id)})
            if book:
                books.append({
                    "book_id": book_id,
                    "title": book.get("title", "Unknown Title"),
                    "author": book.get("authors", ["Unknown Author"])
                })
        except Exception as e:
            print(f"Error fetching book details for book_id {book_id}: {e}")
    return books

def content_based_recommendations(user_id, user_ids, item_ids, interaction_matrix, combined_features, num_recommendations=10):
    user_index = np.where(user_ids == user_id)[0][0]
    user_books = interaction_matrix.tocsr()[user_index].indices

    if len(user_books) == 0:
        return []

    user_profile = combined_features[user_books].mean(axis=0)
    similarities = combined_features.dot(user_profile.T).flatten()
    recommendations = (-similarities).argsort()[:num_recommendations]
    recommended_book_ids = item_ids[recommendations]
    
    # Fetch book details for each recommended item
    # recommended_books = fetch_book_details(recommended_book_ids)
    for book_id in recommended_book_ids :
        ctt_recommended_books = fetch_book_details(book_id)
        if len(ctt_recommended_books) > num_recommendations:
            ctt_recommended_books = random.sample(ctt_recommended_books, num_recommendations)
    return ctt_recommended_books

# Test the content-based recommendation function
user_id = 'elisa'  # Example: recommend books for the test user
recommended_books = recommend_books(user_id, user_ids, item_ids, model, interaction_matrix, num_recommendations=10)
print(f"Recommended books for user: {user_id}")
for book in recommended_books:
    print(f"Book ID: {book['book_id']}, Title: {book['title']}, Author : {book['author']}")


# num_rec = 10
# ctt_recommended_books = content_based_recommendations(user_id, user_ids, item_ids, interaction_matrix, combined_features, num_recommendations=num_rec)
# print(f"Content-based recommended books for user: {user_id}")
# for book in ctt_recommended_books:
#     print(f"Book ID: {book['book_id']}, Title: {book['title']}, Author: {book['author']}")

