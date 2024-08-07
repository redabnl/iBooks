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

# Add sentiment analysis on user reviews
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
        data.append(1)  # Assuming interaction value of 1

    if not rows or not cols or not data:
        print("No interaction data found")
        return None

    interaction_matrix = coo_matrix((data, (rows, cols)), shape=(len(user_ids), len(item_ids)))
    print(f"Interaction matrix shape: {interaction_matrix.shape}")
    print(f"Non-zero entries in interaction matrix: {interaction_matrix.nnz}")
    return interaction_matrix

# Fetch interactions from the interactions collection
interactions = list(interaction_collection.find())

# Debug: Print interaction data
print(f"Total interactions: {len(interactions)}")
print(interactions[:5])  # Print first 5 interactions for verification

# Preprocess and encode categories and summaries
categories = np.array([book.get('categories', ['None'])[0] if book.get('categories') else 'None' for book in books])
summaries = np.array([book.get('summary', '') for book in books])
encoded_categories = encode_categories(categories)
processed_summaries = preprocess_summaries(summaries)
tfidf_matrix, vectorizer = convert_summaries_to_tfidf(processed_summaries)

# Combine features
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

# # Function to calculate precision, recall, and F1 score
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




# Function to recommend books
# def recommend_books(user_id, user_ids, item_ids, model, interaction_matrix, num_recommendations=10):
#     user_index = np.where(user_ids == user_id)[0][0]
#     user_interaction = interaction_matrix.tocsr()[user_index]

#     print(f"User index for {user_id}: {user_index}")
#     print(f"User interaction matrix row: {user_interaction}")

#     try:
#         recommended_items, _ = model.recommend(user_index, user_interaction, N=num_recommendations)
#         print(f"Recommended items for user {user_id}: {recommended_items}")
#         return [item_ids[item] for item in recommended_items]
#     except ValueError as e:
#         print(f"Error recommending items for user {user_id}: {e}")
#         return []

# # Test the recommendation function
# user_id = 'reda'  # Example: recommend books for the test user
# recommended_books = recommend_books(user_id, user_ids, item_ids, model, interaction_matrix, num_recommendations=10)
# print(f"Recommended books for user: {user_id}")
# print(recommended_books)
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

# def content_based_recommendations(user_id, user_ids, item_ids, interaction_matrix, combined_features, num_recommendations=10):
#     user_index = np.where(user_ids == user_id)[0][0]
#     user_books = interaction_matrix.tocsr()[user_index].indices
#     if len(user_books) == 0:
#         return []
#     user_profile = combined_features[user_books].mean(axis=0)
#     similarities = combined_features.dot(user_profile.T).flatten()
#     recommendations = (-similarities).argsort()[:num_recommendations]
#     return item_ids[recommendations]

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

# import random

# def fetch_book_details(book_ids):
#     books = []
#     for book_id in book_ids:
#         try:
#             book = book_collection.find_one({"_id": ObjectId(str(book_id).strip())})
#             if book:
#                 books.append({
#                     "book_id": book_id,
#                     "title": book.get("title", "Unknown Title"),
#                     "author": book.get("authors", ["Unknown Author"])
#                 })
#         except Exception as e:
#             print(f"Error fetching book details for book_id {book_id}: {e}")
#     return books

# def content_based_recommendations(user_id, user_ids, item_ids, interaction_matrix, combined_features, num_recommendations=10):
#     user_index = np.where(user_ids == user_id)[0][0]
#     user_books = interaction_matrix.tocsr()[user_index].indices

#     if len(user_books) == 0:
#         return []

#     user_profile = combined_features[user_books].mean(axis=0)
#     similarities = combined_features.dot(user_profile.T).flatten()
#     recommendations = (-similarities).argsort()
#     recommended_book_ids = item_ids[recommendations]
    
#     # Fetch book details for each recommended item
#     recommended_books = fetch_book_details(recommended_book_ids)
    
#     # Randomly select the specified number of recommendations
    # if len(recommended_books) > num_recommendations:
    #     recommended_books = random.sample(recommended_books, num_recommendations)
    
#     return recommended_books

# # Test the content-based recommendation function
# user_id = 'reda'  # Example: recommend books for the test user
# num_recommendations = 10
# recommended_books = content_based_recommendations(user_id, user_ids, item_ids, interaction_matrix, combined_features, num_recommendations=num_recommendations)
# print(f"Content-based recommended books for user: {user_id}")
# for book in recommended_books:
#     print(f"Book ID: {book['book_id']}, Title: {book['title']}, Author: {book['author']}")


# Test the content-based recommendation function
# user_id = 'reda'  # Example: recommend books for the test user
# recommended_books = content_based_recommendations(user_id, user_ids, item_ids, interaction_matrix, combined_features, num_recommendations=10)
# print(f"Content-based recommended books for user: {user_id}")
# for book in recommended_books:
#     print(f"Book ID: {book['book_id']}, Title: {book['title']}, Author: {book['author']}")



# Test the recommendation function
# user_id = 'reda'  # Example: recommend books for the test user
# recommended_books = recommend_books(user_id, user_ids, item_ids, model, interaction_matrix, num_recommendations=10)
# print(f"Recommended books for user: {user_id}")
# for book in recommended_books:
#     print(f"Book ID: {book['book_id']}, Title: {book['title']}, Author : {book['author']}")

# content_recommended_books = content_based_recommendations(user_id, user_ids, item_ids, interaction_matrix, combined_features, num_recommendations=10)
# print(f"Content-based recommended books for user: {user_id}")
# print(content_recommended_books)

# import numpy as np
# from pymongo import MongoClient
# from bson.objectid import ObjectId
# from implicit.als import AlternatingLeastSquares
# from scipy.sparse import coo_matrix, csr_matrix
# from dotenv import load_dotenv
# from textblob import TextBlob
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.preprocessing import LabelEncoder
# import os
# import datetime

# # Load environment variables
# load_dotenv()

# # Connect to MongoDB
# client = MongoClient(os.getenv('MONGO_DB_URI'))
# db = client['ibooks']
# user_collection = db['users']
# book_collection = db['books']
# review_collection = db['reviews']
# interaction_collection = db['interactions']

# # Fetch users and books
# users = list(user_collection.find())
# books = list(book_collection.find())
# user_ids = np.array([user['pseudo'] for user in users])
# item_ids = np.array([str(book['_id']) for book in books])

# # Function to update the model
# def update_model():
#     global interaction_matrix, model
#     interaction_matrix = create_interaction_matrix(users, books, interactions)
#     if interaction_matrix is not None:
#         model.fit(interaction_matrix.tocsr())
#         print("Model updated successfully.")
#     else:
#         print("Interaction matrix creation failed.")

# # Add sentiment analysis on user reviews
# def get_sentiment_score(review_text):
#     analysis = TextBlob(review_text)
#     return analysis.sentiment.polarity

# for review in review_collection.find():
#     sentiment_score = get_sentiment_score(review['review_text'])
#     review_collection.update_one(
#         {'_id': review['_id']},
#         {'$set': {'sentiment_score': sentiment_score}}
#     )

# # Label encode the book categories
# def encode_categories(categories):
#     le = LabelEncoder()
#     return le.fit_transform(categories)

# def preprocess_summaries(summaries):
#     processed_summaries = [summary.lower() for summary in summaries]
#     return processed_summaries

# def convert_summaries_to_tfidf(summaries):
#     vectorizer = TfidfVectorizer(max_features=5000)
#     tfidf_matrix = vectorizer.fit_transform(summaries)
#     return tfidf_matrix, vectorizer

# def combine_features(categories, tfidf_matrix):
#     combined_features = csr_matrix(np.hstack([categories.reshape(-1, 1), tfidf_matrix.toarray()]))
#     return combined_features

# def create_interaction_matrix(users, books, interactions):
#     rows, cols, data = [], [], []
#     user_ids = np.array([user['pseudo'] for user in users])
#     item_ids = np.array([str(book['_id']) for book in books])

#     for interaction in interactions:
#         user_index = np.where(user_ids == interaction['user_id'])[0]
#         if user_index.size == 0:
#             continue
#         user_index = user_index[0]
#         book_index = np.where(item_ids == str(interaction['book_id']))[0]
#         if book_index.size == 0:
#             continue
#         book_index = book_index[0]

#         rows.append(user_index)
#         cols.append(book_index)
#         data.append(1)  # Assuming interaction value of 1

#     if not rows or not cols or not data:
#         print("No interaction data found")
#         return None

#     return coo_matrix((data, (rows, cols)), shape=(len(user_ids), len(item_ids)))

# # Fetch interactions from the interactions collection
# interactions = list(interaction_collection.find())

# # Preprocess and encode categories and summaries
# categories = np.array([book.get('categories', ['None'])[0] if book.get('categories') else 'None' for book in books])
# summaries = np.array([book.get('summary', '') for book in books])
# encoded_categories = encode_categories(categories)
# processed_summaries = preprocess_summaries(summaries)
# tfidf_matrix, vectorizer = convert_summaries_to_tfidf(processed_summaries)

# # Combine features
# combined_features = combine_features(encoded_categories, tfidf_matrix)

# # Create the interaction matrix
# interaction_matrix = create_interaction_matrix(users, books, interactions)
# interaction_matrix_csr = interaction_matrix.tocsr()

# # Initialize the model
# model = AlternatingLeastSquares(factors=50, regularization=0.01, iterations=15)

# # Ensure interaction_matrix is not None before fitting the model
# if interaction_matrix is not None:
#     model.fit(interaction_matrix_csr)
#     print("Model updated successfully.")
# else:
#     print("Interaction matrix creation failed.")

# # Function to calculate precision, recall, and F1 score
# def calculate_metrics(interaction_matrix, user_ids, model):
#     precision_list, recall_list = [], []
#     interaction_matrix_csr = interaction_matrix.tocsr()

#     for user_index in range(interaction_matrix.shape[0]):
#         if interaction_matrix_csr[user_index].nnz == 0:
#             continue

#         recommended_items, _ = model.recommend(user_index, interaction_matrix_csr, N=10)
#         user_items = interaction_matrix_csr[user_index].indices

#         user_items_set = set(user_items)
#         recommended_items_set = set(recommended_items)

#         true_positives = len(user_items_set & recommended_items_set)
#         precision = true_positives / len(recommended_items_set) if recommended_items_set else 0
#         recall = true_positives / len(user_items_set) if user_items_set else 0

#         precision_list.append(precision)
#         recall_list.append(recall)

#     precision = np.mean(precision_list)
#     recall = np.mean(recall_list)
#     f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

#     return precision, recall, f1

# precision, recall, f1 = calculate_metrics(interaction_matrix, user_ids, model)
# print(f"Precision: {precision}, Recall: {recall}, F1 Score: {f1}")

# # Add the missing functions
# def recommend_books(user_id, user_ids, item_ids, model, interaction_matrix, num_recommendations=10):
#     user_index = np.where(user_ids == user_id)[0][0]
#     user_interaction = interaction_matrix.tocsr()[user_index]
#     recommended_items, _ = model.recommend(user_index, user_interaction, N=num_recommendations)
#     return [item_ids[item] for item in recommended_items]

# def content_based_recommendations(user_id, user_ids, item_ids, interaction_matrix, combined_features, num_recommendations=10):
#     user_index = np.where(user_ids == user_id)[0][0]
#     user_books = interaction_matrix.tocsr()[user_index].indices
#     if len(user_books) == 0:
#         return []
#     user_profile = combined_features[user_books].mean(axis=0)
#     similarities = combined_features.dot(user_profile.T).toarray().flatten()
#     recommendations = (-similarities).argsort()[:num_recommendations]
#     return item_ids[recommendations]

# def combined_recommendations(user_id, user_ids, item_ids, interaction_matrix, categories, model, num_recommendations=10):
#     collaborative_recommendations = recommend_books(user_id, user_ids, item_ids, model, interaction_matrix, num_recommendations)
#     content_recommendations = content_based_recommendations(user_id, user_ids, item_ids, interaction_matrix, categories, num_recommendations)
#     combined_recommendations = list(set(collaborative_recommendations + content_recommendations))
#     if len(combined_recommendations) > num_recommendations:
#         combined_recommendations = combined_recommendations[:num_recommendations]
#     return combined_recommendations

# # Test the recommendation function
# user_id = 'reda'  # Example: recommend books for the first user
# recommended_books = recommend_books(user_id, user_ids, item_ids, model, interaction_matrix, num_recommendations=10)
# print(f"Recommended books for user: {user_id}")
# print(recommended_books)

# Generate content-based recommendations
# content_recommended_books = content_based_recommendations(user_id, user_ids, item_ids, interaction_matrix, combined_features, num_recommendations=10)
# print(f"Content-based recommended books for user: {user_id}")
# print(content_recommended_books)

# # Generate combined recommendations
# final_recommendations = combined_recommendations(user_id, user_ids, item_ids, interaction_matrix, encoded_categories, model, num_recommendations=10)
# print("Final combined recommendations for user:", user_id)
# print(final_recommendations)


# Generate combined recommendations
# final_recommendations = combined_recommendations(user_id, user_ids, item_ids, interaction_matrix, encoded_categories, model, num_recommendations=10)
# print("Final combined recommendations for user:", user_id)
# print(final_recommendations)


# Function to calculate precision, recall, and F1 score
# def calculate_metrics(interaction_matrix, user_ids, model):
#     precision_list, recall_list = [], []
#     interaction_matrix_csr = interaction_matrix.tocsr()

#     for user_index in range(interaction_matrix.shape[0]):
#         if interaction_matrix_csr[user_index].nnz == 0:
#             continue

#         user_items = interaction_matrix_csr[user_index]
#         recommended_items, _ = model.recommend(user_index, interaction_matrix_csr[user_index], N=10)

#         user_items_set = set(user_items.indices)
#         recommended_items_set = set(recommended_items)

#         true_positives = len(user_items_set & recommended_items_set)
#         precision = true_positives / len(recommended_items_set) if recommended_items_set else 0
#         recall = true_positives / len(user_items_set) if user_items_set else 0

#         precision_list.append(precision)
#         recall_list.append(recall)

#     precision = np.mean(precision_list)
#     recall = np.mean(recall_list)
#     f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

#     return precision, recall, f1

# precision, recall, f1 = calculate_metrics(interaction_matrix, user_ids, model)
# print(f"Precision: {precision}, Recall: {recall}, F1 Score: {f1}")



    
    
    
# # Test the recommendation function
# user_id = 'reda'  # Example: recommend books for the first user
# recommended_books = recommend_books(user_id, user_ids, item_ids, model, interaction_matrix, num_recommendations=10)
# print(f"Recommended books for user: {user_id}")
# print(recommended_books)

# Generate content-based recommendations
# content_recommended_books = content_based_recommendations(user_id, user_ids, item_ids, interaction_matrix, combined_features, num_recommendations=10)
# print(f"Content-based recommended books for user: {user_id}")
# print(content_recommended_books)

# # Generate combined recommendations
# final_recommendations = combined_recommendations(user_id, user_ids, item_ids, interaction_matrix, encoded_categories, model, num_recommendations=10)
# print("Final combined recommendations for user:", user_id)
# print(final_recommendations)

# Add a new review and update the model
# add_review_and_update(user_id, ObjectId('66a7d293a8ae66cfbcb6cbbf'), f"Would highly recommend it to anyone who loves reading! Very inspirational", 5)

# # Get updated recommendations
# updated_recommended_books = recommend_books(user_id, user_ids, item_ids, model, interaction_matrix, num_recommendations=10)
# print("Updated recommended books for user:", user_id)
# print(updated_recommended_books)

# Function to recommend books based on user interaction history
# def recommend_books(user_id, user_ids, item_ids, model, interaction_matrix, num_recommendations=10):
#     user_index = np.where(user_ids == user_id)[0][0]
#     user_items = interaction_matrix.tocsr()[user_index]
#     recommended_items, scores = model.recommend(user_index, user_items, N=num_recommendations)
#     recommended_item_ids = [item_ids[i] for i in recommended_items]
#     return recommended_item_ids

# # Function to generate content-based recommendations
# def content_based_recommendations(user_id, user_ids, item_ids, interaction_matrix, combined_features, num_recommendations=10):
#     user_index = np.where(user_ids == user_id)[0][0]
#     user_books = interaction_matrix.tocsr()[user_index].indices
#     if len(user_books) == 0:
#         return []
    
#     user_profile = combined_features[user_books].mean(axis=0)
#     # similarities = combined_features.dot(user_profile.T).toarray().flatten()
#     similarities = combined_features.dot(user_profile.T).np.array().flatten()  
#     recommendations = (-similarities).argsort()[:num_recommendations]
#     return item_ids[recommendations]

# # Function to generate combined recommendations
# def combined_recommendations(user_id, user_ids, item_ids, interaction_matrix, combined_features, model, num_recommendations=10):
#     collaborative_recommendations = recommend_books(user_id, user_ids, item_ids, model, interaction_matrix, num_recommendations)
#     content_recommendations = content_based_recommendations(user_id, user_ids, item_ids, interaction_matrix, combined_features, num_recommendations)
    
#     combined_recommendations = list(set(collaborative_recommendations + content_recommendations))
#     if len(combined_recommendations) > num_recommendations:
#         combined_recommendations = combined_recommendations[:num_recommendations]
    
#     return combined_recommendations

# # Function to add a new review and update the model
# def add_review_and_update(user_pseudo, book_id, review_text, rating):
#     sentiment_score = get_sentiment_score(review_text)
#     review_collection.insert_one({
#         'user_pseudo': user_pseudo,
#         'book_id': book_id,
#         'review_text': review_text,
#         'sentiment_score': sentiment_score,
#         'rating': rating,
#         'review_date': datetime.now(datetime.timezone.utc)
#     })
#     update_model()


# import numpy as np
# from pymongo import MongoClient
# from bson.objectid import ObjectId
# from implicit.als import AlternatingLeastSquares
# from scipy.sparse import coo_matrix, csr_matrix
# from dotenv import load_dotenv
# from sklearn.preprocessing import LabelEncoder
# from textblob import TextBlob
# from sklearn.feature_extraction.text import TfidfVectorizer
# import os
# import datetime

# # Load environment variables
# load_dotenv()

# # Connect to MongoDB
# client = MongoClient(os.getenv('MONGO_DB_URI'))
# db = client['ibooks']
# user_collection = db['users']
# book_collection = db['books']
# review_collection = db['reviews']

# # Fetch users and books
# users = list(user_collection.find())
# books = list(book_collection.find())
# categories = [book.get('categories', ['None'])[0] if book.get('categories') else 'None' for book in books]
# summaries = [book.get('summary', '') for book in books]

# # Create mappings from user and item IDs to indices
# user_ids = np.array([user['pseudo'] for user in users])
# item_ids = np.array([str(book['_id']) for book in books])

# # Ensure these are defined at the top of your script
# model = AlternatingLeastSquares(factors=50, regularization=0.01, iterations=15)

# # Add sentiment analysis on user reviews
# def get_sentiment_score(review_text):
#     analysis = TextBlob(review_text)
#     return analysis.sentiment.polarity

# for review in review_collection.find():
#     sentiment_score = get_sentiment_score(review['review_text'])
#     review_collection.update_one(
#         {'_id': review['_id']},
#         {'$set': {'sentiment_score': sentiment_score}}
#     )

# # Label encode the book categories
# def encode_categories(categories):
#     le = LabelEncoder()
#     return le.fit_transform(categories)

# def preprocess_summaries(summaries):
#     processed_summaries = [summary.lower() for summary in summaries]
#     return processed_summaries

# def convert_summaries_to_tfidf(summaries):
#     vectorizer = TfidfVectorizer(max_features=5000)
#     tfidf_matrix = vectorizer.fit_transform(summaries)
#     return tfidf_matrix, vectorizer

# def combine_features(categories, tfidf_matrix):
#     combined_features = np.hstack([categories.reshape(-1, 1), tfidf_matrix.toarray()])
#     return combined_features

# def create_interaction_matrix(users, books, already_read_key):
#     rows, cols, data = [], [], []
    
#     if not users or not books:
#         print("Users or books list is empty")
#         return None

#     user_ids = np.array([user['pseudo'] for user in users])
#     item_ids = np.array([str(book['_id']) for book in books])
    
#     for user in users:
#         user_index = np.where(user_ids == user['pseudo'])[0]
#         if user_index.size == 0:
#             continue
#         user_index = user_index[0]

#         for book_id in user.get(already_read_key, []):
#             book_id_str = str(book_id)
#             book_index = np.where(item_ids == book_id_str)[0]
#             if book_index.size == 0:
#                 continue
#             book_index = book_index[0]

#             rows.append(user_index)
#             cols.append(book_index)
#             review = review_collection.find_one({'user_pseudo': user['pseudo'], 'book_id': book_id})
#             sentiment_score = review.get('sentiment_score', 1) if review else 1
#             data.append(sentiment_score)

#     if not rows or not cols or not data:
#         print("No interaction data found")
#         return None

#     return coo_matrix((data, (rows, cols)), shape=(len(users), len(books)))

# interaction_matrix = create_interaction_matrix(users, books, 'already_read')
# if interaction_matrix is not None:
#     model.fit(interaction_matrix.tocsr())
#     print("Model updated successfully.")
# else:
#     print("Interaction matrix creation failed.")

# def content_based_recommendations(user_pseudo, user_ids, item_ids, interaction_matrix, combined_features, num_recommendations=10):
#     print(f"Generating content-based recommendations for user ID {user_pseudo}...")
    
#     user_index = np.where(user_ids == user_pseudo)[0]
#     if user_index.size == 0:
#         print(f"No index found for user ID {user_pseudo}")
#         return []
#     user_index = user_index[0]
    
#     user_books = interaction_matrix.tocsr()[user_index].indices
    
#     if len(user_books) == 0:
#         return []
    
#     user_profile = combined_features[user_books].mean(axis=0)
#     similarities = np.dot(combined_features, user_profile)
    
#     recommendations = np.argsort(-similarities)[:num_recommendations]
    
#     return item_ids[recommendations]

# def recommend_books(user_id, user_ids, item_ids, model, interaction_matrix, num_recommendations=10):
#     print(f"Recommending books for user ID {user_id}...")
    
#     interaction_matrix = interaction_matrix.tocsr()
#     user_index_array = np.where(user_ids == user_id)[0]
    
#     if user_index_array.size == 0:
#         raise ValueError(f"User ID {user_id} not found in user_ids array")
    
#     user_index = user_index_array[0]
    
#     user_items = interaction_matrix[user_index]
#     user_items = csr_matrix(user_items)
    
#     recommended_items, scores = model.recommend(user_index, user_items, N=num_recommendations)
    
#     print("Recommendations generated:", recommended_items)
    
#     recommended_item_ids = [item_ids[i] for i in recommended_items]
    
#     return recommended_item_ids

# def combined_recommendations(user_id, user_ids, item_ids, interaction_matrix, combined_features, model, num_recommendations=10):
#     collaborative_recommendations = recommend_books(user_id, user_ids, item_ids, model, interaction_matrix, num_recommendations)
#     content_recommendations = content_based_recommendations(user_id, user_ids, item_ids, interaction_matrix, combined_features, num_recommendations)

#     collaborative_recommendations = [str(rec) for rec in collaborative_recommendations]
#     content_recommendations = [str(rec) for rec in content_recommendations]

#     combined_recommendations = list(set(collaborative_recommendations + content_recommendations))

#     if len(combined_recommendations) > num_recommendations:
#         combined_recommendations = combined_recommendations[:num_recommendations]

#     return combined_recommendations

# def update_model():
#     global interaction_matrix, model
#     interaction_matrix = create_interaction_matrix(users, books, 'already_read')
#     if interaction_matrix is None:
#         print("Interaction matrix is None, skipping model update")
#         return
#     model.fit(interaction_matrix.tocsr())
#     print("Model updated successfully.")

# # Simulate adding a new review and updating the model
# def add_review_and_update(user_pseudo, book_id, review_text, rating):
#     sentiment_score = get_sentiment_score(review_text)
#     review_collection.insert_one({
#         'user_pseudo': user_pseudo,
#         'book_id': book_id,
#         'review_text': review_text,
#         'sentiment_score': sentiment_score,
#         'rating': rating,
#         'review_date': datetime.datetime.now(datetime.timezone.utc)
#     })
#     update_model()

# # Preprocess and encode categories and summaries
# encoded_categories = encode_categories(categories)
# processed_summaries = preprocess_summaries(summaries)
# tfidf_matrix, vectorizer = convert_summaries_to_tfidf(processed_summaries)

# # Combine features
# combined_features = combine_features(encoded_categories, tfidf_matrix)

# # Create the interaction matrix
# interaction_matrix = create_interaction_matrix(users, books, 'already_read')

# # Ensure interaction_matrix is not None before fitting the model
# if interaction_matrix is not None:
#     model.fit(interaction_matrix.tocsr())
#     print("Model updated successfully.")
# else:
#     print("Interaction matrix creation failed.")

# # Test the recommendation function
# user_id = 'reda'  # Example: recommend books for the first user
# recommended_books = recommend_books(user_id, user_ids, item_ids, model, interaction_matrix, num_recommendations=10)
# print(f"Recommended books for user: {user_id}")
# print(recommended_books)

# # Generate content-based recommendations
# content_recommended_books = content_based_recommendations(user_id, user_ids, item_ids, interaction_matrix, combined_features, num_recommendations=10)
# print(f"Content-based recommended books for user: {user_id}")
# print(content_recommended_books)

# # Generate combined recommendations
# final_recommendations = combined_recommendations(user_id, user_ids, item_ids, interaction_matrix, combined_features, model, num_recommendations=10)
# print("Final combined recommendations for user:", user_id)
# print(final_recommendations)

# Add a new review and update the model
# add_review_and_update(user_id, ObjectId('669a919aa54befca3f02409a'), f"such a beautiful masterpiece ! loved it so much", 5)



# # Preprocess and encode categories and summaries
# encoded_categories = encode_categories(categories)
# processed_summaries = preprocess_summaries(summaries)
# tfidf_matrix, vectorizer = convert_summaries_to_tfidf(processed_summaries)

# # Combine features
# combined_features = combine_features(encoded_categories, tfidf_matrix)

# # Create the interaction matrix
# interaction_matrix = create_interaction_matrix(users, books, 'already_read')

# # Ensure interaction_matrix is not None before fitting the model
# if interaction_matrix is not None:
#     model.fit(interaction_matrix.tocsr())
#     print("Model updated successfully.")
# else:
#     print("Interaction matrix creation failed.")

# # --- main.py ---
# from recommendations_serv.app.data_preparation import (
#     combine_features, convert_summaries_to_tfidf, encode_categories,
#     get_sentiment_score, preprocess_summaries, update_model,
#     content_based_recommendations, create_interaction_matrix
# )
# import streamlit as st
# import requests
# from data.models import get_mongo_client
# from data.book_model import fetch_book_by_id, fetch_wishlist_books
# from PIL import Image
# from io import BytesIO
# import datetime
# from frontE.libraryI import add_review_and_update, get_reviews_for_book
# from frontE.homePage import display_books_grid, display_book_details
# import numpy as np

# client = get_mongo_client()
# db = client['ibooks']
# book_collection = db['books']
# users_collection = db['users']

# users = list(users_collection.find())
# books = list(book_collection.find())
# user_ids = np.array([user['pseudo'] for user in users])
# item_ids = np.array([str(book['_id']) for book in books])
# categories = [book.get('categories', ['None'])[0] if book.get('categories') else 'None' for book in books]
# summaries = [book.get('summary', '') for book in books]

# encoded_categories = encode_categories(categories)
# processed_summaries = preprocess_summaries(summaries)
# tfidf_matrix, vectorizer = convert_summaries_to_tfidf(processed_summaries)

# combined_features = combine_features(encoded_categories, tfidf_matrix)

# interaction_matrix = create_interaction_matrix(users, books, 'already_read')

# if interaction_matrix is not None:
#     model.fit(interaction_matrix.tocsr())
#     print("Model updated successfully.")
# else:
#     print("Interaction matrix creation failed.")

# def show_library(user_pseudo):
#     user_pseudo = st.session_state['current_user']
#     st.markdown("<link rel='stylesheet' href='/mnt/data/library.css'>", unsafe_allow_html=True)
    
#     st.header(f"{user_pseudo}'s Library")
    
#     display_wishlist(user_pseudo)
        
#     books_read = get_books_read_by_user(user_pseudo)
    
#     if not books_read:
#         st.write("You haven't read any books yet.")
#         return
    
#     st.markdown("<div class='book-container'>", unsafe_allow_html=True)
    
#     readB_display = set()
    
#     for book in books_read:
#         if book['_id'] not in readB_display:
#             readB_display.add(book['_id'])
#             display_readBook_details(book)
            














# import numpy as np
# from pymongo import MongoClient
# from bson.objectid import ObjectId
# from implicit.als import AlternatingLeastSquares
# from scipy.sparse import coo_matrix, csr_matrix
# from dotenv import load_dotenv
# from sklearn.preprocessing import LabelEncoder
# from sklearn.feature_extraction.text import TfidfVectorizer
# from textblob import TextBlob
# from sklearn.ensemble import RandomForestClassifier
# from sklearn.metrics import precision_score, recall_score, f1_score
# import os
# from datetime import datetime, timezone
# import streamlit as st
# # Load environment variables
# load_dotenv()

# # Connect to MongoDB
# client = MongoClient(os.getenv('MONGO_DB_URI'))
# db = client['ibooks']
# user_collection = db['users']
# book_collection = db['books']
# review_collection = db['reviews']

# # Fetch users and books
# users = list(user_collection.find())
# books = list(book_collection.find())

# # Create mappings from user and item IDs to indices
# user_ids = np.array([user['pseudo'] for user in users])
# item_ids = np.array([book['_id'] for book in books])

# print("User IDs:", user_ids)  # Print user IDs for debugging
# print("Current User ID:", st.session_state['current_user'])  # Print current user ID for debugging

# # Ensure these are defined at the top of your script
# model = AlternatingLeastSquares(factors=50, regularization=0.01, iterations=15)

# # Add sentiment analysis on user reviews
# def get_sentiment_score(review_text):
#     analysis = TextBlob(review_text)
#     return analysis.sentiment.polarity

# for review in review_collection.find():
#     sentiment_score = get_sentiment_score(review['review_text'])
#     review_collection.update_one(
#         {'_id': review['_id']},
#         {'$set': {'sentiment_score': sentiment_score}}
#     )

# def create_interaction_matrix(users, books, already_read_key):
#     rows, cols, data = [], [], []
    
#     if not users or not books:
#         print("Users or books list is empty")
#         return None  # Return None if the users or books list is empty

#     user_ids = np.array([user['pseudo'] for user in users])
#     item_ids = np.array([str(book['_id']) for book in books])
#     already_read_key = (book['_id'] for book in books)
     
#     for user in users:
       
#         user_index = np.where(user_ids == user['pseudo'])[0]
#         if user_index.size == 0:
#             continue
#         user_index = user_index[0]

#         for book_id in user.get(already_read_key, []):
#             book_id_str = str(book_id)  # Ensure book_id is a string for comparison
#             book_index = np.where(item_ids == book_id_str)[0]
#             if book_index.size == 0:
#                 continue
#             book_index = book_index[0]

#             rows.append(user_index)
#             cols.append(book_index)
#             review = review_collection.find_one({'user_pseudo': user['pseudo'], 'book_id': book_id})
#             sentiment_score = review.get('sentiment_score', 1) if review else 1  # Default sentiment score
#             data.append(sentiment_score)

#     if not rows or not cols or not data:
#         print("No interaction data found")
#         return None  # Return None if the lists are empty

#     return coo_matrix((data, (rows, cols)), shape=(len(users), len(books)))

# # Ensure the function is called correctly
# interaction_matrix = create_interaction_matrix(users, books, 'already_read')
# if interaction_matrix is not None:
#     model.fit(interaction_matrix.tocsr())
#     print("Model updated successfully.")
# else:
#     print("Interaction matrix creation failed.")

# def encode_categories(categories):
#     le = LabelEncoder()
#     return le.fit_transform(categories)

# def preprocess_summaries(summaries):
#     # Example preprocessing function
#     # You can add more preprocessing steps like stemming/lemmatization
#     processed_summaries = [summary.lower() for summary in summaries]
#     return processed_summaries

# def convert_summaries_to_tfidf(summaries):
#     vectorizer = TfidfVectorizer(max_features=5000)  # Adjust max_features as needed
#     tfidf_matrix = vectorizer.fit_transform(summaries)
#     return tfidf_matrix, vectorizer


# def combine_features(categories, tfidf_matrix):
#     # Assuming categories are already encoded as numerical features
#     combined_features = csr_matrix(np.hstack([categories.reshape(-1, 1), tfidf_matrix.toarray()]))
#     return combined_features


# # Preprocess the book summaries
# summaries = [book.get('summary', '') for book in books]
# processed_summaries = preprocess_summaries(summaries)

# # Convert the summaries to TF-IDF features
# tfidf_matrix, vectorizer = convert_summaries_to_tfidf(processed_summaries)

# # Encode the book categories
# categories = encode_categories([book.get('categories', 'unknown') for book in books])

# # Combine these features
# combined_features = combine_features(categories, tfidf_matrix)

# def content_based_recommendations(user_pseudo, user_ids, item_ids, interaction_matrix, combined_features, num_recommendations=10):
#     print(f"Generating content-based recommendations for user ID {user_pseudo}...")
    
#     user_index = np.where(user_ids == user_pseudo)[0]
#     if user_index.size == 0:
#         print(f"No index found for user ID {user_pseudo}")
#         return []
#     user_index = user_index[0]
    
#     user_books = interaction_matrix.tocsr()[user_index].indices
    
#     if len(user_books) == 0:
#         return []
    
#     user_profile = combined_features[user_books].mean(axis=0)
#     similarities = combined_features.dot(user_profile.T).toarray().flatten()
    
#     recommendations = (-similarities).argsort()[:num_recommendations]
    
#     return item_ids[recommendations]

# def recommend_books(user_id, user_ids, item_ids, model, interaction_matrix, num_recommendations=10):
#     print(f"Recommending books for user ID {user_id}...")
    
#     # Ensure the interaction_matrix is in CSR format
#     interaction_matrix = interaction_matrix.tocsr()
    
#     # Find the user index in the user_ids array
#     user_index_array = np.where(user_ids == user_id)[0]
    
#     if user_index_array.size == 0:
#         raise ValueError(f"User ID {user_id} not found in user_ids array")
    
#     user_index = user_index_array[0]
    
#     # Get the user’s interaction vector
#     user_items = interaction_matrix[user_index]
    
#     # Ensure user_items is in CSR format
#     user_items = csr_matrix(user_items)
    
#     # Use the model to recommend items for the user
#     recommended_items, scores = model.recommend(user_index, user_items, N=num_recommendations)
    
#     print("Recommendations generated:", recommended_items)
    
#     # Map the recommended item indices to item IDs
#     recommended_item_ids = [item_ids[i] for i in recommended_items]
    
#     return recommended_item_ids


# # def content_based_recommendations(user_id, user_ids, item_ids, interaction_matrix, categories, num_recommendations=10):
# #     print(f"Generating content-based recommendations for user ID {user_id}...")
    
# #     # Get the user's already read books
# #     user_index = np.where(user_ids == user_id)[0][0]
# #     user_books = interaction_matrix.tocsr()[user_index].indices
    
# #     if len(user_books) == 0:
# #         return []
    
# #     # Get the categories of the books the user has already read
# #     user_categories = categories[user_books]
    
# #     # Get the most frequent category
# #     most_frequent_category = np.bincount(user_categories).argmax()
    
# #     # Recommend books from the same category
# #     category_books = np.where(categories == most_frequent_category)[0]
    
# #     return item_ids[category_books[:num_recommendations]]



# def recommend_books(user_id, user_ids, item_ids, model, interaction_matrix, num_recommendations=10):
#     print(f"Recommending books for user ID {user_id}...")
    
#     # Ensure the interaction_matrix is in CSR format
#     interaction_matrix = interaction_matrix.tocsr()
    
#     # Find the user index in the user_ids array
#     user_index_array = np.where(user_ids == user_id)[0]
    
#     if user_index_array.size == 0:
#         raise ValueError(f"User ID {user_id} not found in user_ids array")
    
#     user_index = user_index_array[0]
    
#     # Get the user’s interaction vector
#     user_items = interaction_matrix[user_index]
    
#     # Ensure user_items is in CSR format
#     user_items = csr_matrix(user_items)
    
#     # Use the model to recommend items for the user
#     recommended_items, scores = model.recommend(user_index, user_items, N=num_recommendations)
    
#     print("Recommendations generated:", recommended_items)
    
#     # Map the recommended item indices to item IDs
#     recommended_item_ids = [item_ids[i] for i in recommended_items]
    
#     return recommended_item_ids




# def combined_recommendations(user_id, user_ids, item_ids, interaction_matrix, categories, model, num_recommendations=10):
#     collaborative_recommendations = recommend_books(user_id, user_ids, item_ids, model, interaction_matrix, num_recommendations)
#     content_recommendations = content_based_recommendations(user_id, user_ids, item_ids, interaction_matrix, combined_features, num_recommendations)

#     # Convert ObjectId to strings to make them hashable and unique
#     collaborative_recommendations = [str(rec) for rec in collaborative_recommendations]
#     content_recommendations = [str(rec) for rec in content_recommendations]

#     # Combine and ensure uniqueness
#     combined_recommendations = list(set(collaborative_recommendations + content_recommendations))

#     # Limit to num_recommendations if necessary
#     if len(combined_recommendations) > num_recommendations:
#         combined_recommendations = combined_recommendations[:num_recommendations]

#     return combined_recommendations

# # Update model incrementally
# def update_model():
#     global interaction_matrix, model
#     interaction_matrix = create_interaction_matrix(users, books, 'already_read')
#     if interaction_matrix is None:
#         print("Interaction matrix is None, skipping model update")
#         return
#     model.fit(interaction_matrix.tocsr())
#     print("Model updated successfully.")

# # Preprocess the book summaries
# summaries = [book.get('summary', '') for book in books]
# processed_summaries = preprocess_summaries(summaries)

# # Convert the summaries to TF-IDF features
# tfidf_matrix, vectorizer = convert_summaries_to_tfidf(processed_summaries)

# # Encode the book categories
# categories = encode_categories([book.get('categories', 'unknown') for book in books])

# # Combine these features
# combined_features = combine_features(categories, tfidf_matrix)

# Simulate adding a new review and updating the model
# def add_review_and_update(user_pseudo, book_id, review_text, rating):
#     sentiment_score = get_sentiment_score(review_text)
#     review_collection.insert_one({
#         'user_pseudo': user_pseudo,
#         'book_id': book_id,
#         'review_text': review_text,
#         'sentiment_score': sentiment_score,
#         'rating' : rating,
#         'review_date': datetime.now(timezone.utc)
#     })
#     update_model()

# Test the recommendation function
# test_user_id = 'reda'  # Example: recommend books for the first user
# recommended_books = recommend_books(test_user_id, user_ids, item_ids, model, interaction_matrix, num_recommendations=10)
# print("Recommended books for user:", test_user_id)
# print(recommended_books)

# Generate content-based recommendations
# content_recommended_books = content_based_recommendations(test_user_id, user_ids, item_ids, interaction_matrix, encoded_categories, num_recommendations=10)
# print("Content-based recommended books for user:", test_user_id)
# print(content_recommended_books)

# Generate combined recommendations
# final_recommendations = combined_recommendations(test_user_id, user_ids, item_ids, interaction_matrix, encoded_categories, model, num_recommendations=10)
# print("Final combined recommendations for user:", test_user_id)
# print(final_recommendations)

# Add a new review and update the model
# add_review_and_update('fernand', ObjectId('667eef1a6b108eb7bf378215'), f"It was one of the books that really made me love reading !", 5)

# Get updated recommendations
# updated_recommended_books = recommend_books(test_user_id, user_ids, item_ids, model, interaction_matrix, num_recommendations=10)
# print("Updated recommended books for user:", test_user_id)
# print(updated_recommended_books)



# # Example usage
# # try:
# #     combined_recs = combined_recommendations(test_user_id, user_ids, item_ids, model, interaction_matrix, encoded_categories, num_recommendations=10)
# #     print("Combined recommendations for user:", test_user_id)
# #     print(combined_recs)
# # except Exception as e:
# #     print(f"Error generating combined recommendations: {e}")

# # # Update model after adding a review
# # def add_review_and_update(user_pseudo, book_id, review_text, rating):
# #     sentiment_score = get_sentiment_score(review_text)
# #     review_collection.insert_one({
# #         'user_pseudo': user_pseudo,
# #         'book_id': book_id,
# #         'review_text': review_text,
# #         'sentiment_score': sentiment_score,
# #         'rating': rating,
# #         'review_date': datetime.now(timezone.utc)
# #     })
# #     update_model()

# # # Test adding a review and getting updated recommendations
# # add_review_and_update('reda', ObjectId('66916ffe3ccbd040dab475fb'), "An excellent book that I thoroughly enjoyed.", 5)
# # try:
# #     updated_recs = combined_recommendations(test_user_id, user_ids, item_ids, model, interaction_matrix, encoded_categories, num_recommendations=10)
# #     print("Updated combined recommendations for user:", test_user_id)
# #     print(updated_recs)
# # except Exception as e:
# #     print(f"Error generating updated recommendations: {e}")

# # Simulate adding a new review and updating the model
# # def add_review_and_update(user_pseudo, book_id, review_text, rating):
# #     sentiment_score = get_sentiment_score(review_text)
# #     review_collection.insert_one({
# #         'user_pseudo': user_pseudo,
# #         'book_id': book_id,
# #         'review_text': review_text,
# #         'sentiment_score': sentiment_score,
# #         'rating' : rating,
# #         'review_date': datetime.now(timezone.utc)
# #     })
# #     update_model()


# # def content_based_recommendations(user_id, user_ids, item_ids, model, interaction_matrix, categories, num_recommendations=10):
# #     print(f"Generating content-based recommendations for user ID {user_id}...")
    
# #     # Get the user's already read books
# #     user_index = np.where(user_ids == user_id)[0][0]
# #     user_books = interaction_matrix.tocsr()[user_index].indices
    
# #     if len(user_books) == 0:
# #         return []
    
# #     # Get the categories of the books the user has already read
# #     user_categories = categories[user_books]
    
# #     # Get the most frequent category
# #     most_frequent_category = np.bincount(user_categories).argmax()
    
# #     # Recommend books from the same category
# #     category_books = np.where(categories == most_frequent_category)[0]
    
# #     return item_ids[category_books[:num_recommendations]]


# #def recommend_books(user_id, user_ids, item_ids, model, interaction_matrix, num_recommendations=10):
# #     print(f"Recommending books for user ID {user_id}...")
    
# #     # Ensure the interaction_matrix is in CSR format
# #     interaction_matrix = interaction_matrix.tocsr()
    
# #     # Find the user index in the user_ids array
# #     user_index_array = np.where(user_ids == user_id)[0]
    
# #     if user_index_array.size == 0:
# #         raise ValueError(f"User ID {user_id} not found in user_ids array")
    
# #     user_index = user_index_array[0]
    
# #     # Get the user’s interaction vector
# #     user_items = interaction_matrix[user_index]
    
# #     # Ensure user_items is in CSR format
# #     user_items = csr_matrix(user_items)
    
# #     # Use the model to recommend items for the user
# #     recommended_items, scores = model.recommend(user_index, user_items, N=num_recommendations)
    
# #     print("Recommendations generated:", recommended_items)
    
# #     # Map the recommended item indices to item IDs
# #     recommended_item_ids = [item_ids[i] for i in recommended_items]
    
# #     return recommended_item_ids


# # from pymongo import MongoClient
# # from bson.objectid import ObjectId
# # from dotenv import load_dotenv
# # import os
# # from datetime import datetime

# # # Load environment variables
# # load_dotenv()

# # # Connect to MongoDB
# # client = MongoClient(os.getenv('MONGO_DB_URI'))
# # db = client['ibooks']
# # review_collection = db['reviews']
# # book_collection = db['books']

# # # Function to update review structure
# # def update_review_structure():
# #     reviews = list(review_collection.find())

# #     for review in reviews:
# #         # Convert 'isbn' to 'book_id'
# #         if 'isbn' in review:
# #             isbn = review['isbn']
# #             book = book_collection.find_one({'isbn': isbn})
# #             if book:
# #                 book_id = book['_id']
# #                 review['book_id'] = book_id
# #             del review['isbn']
        
# #         # Ensure 'sentiment_score' exists
# #         if 'sentiment_score' not in review:
# #             review['sentiment_score'] = None
        
# #         # Remove 'date' field if it exists
# #         if 'date' in review:
# #             review['review_date'] = review['date']
# #             del review['date']
        
# #         # Ensure all necessary fields exist
# #         required_fields = ['user_pseudo', 'book_id', 'review_text', 'rating', 'review_date', 'sentiment_score']
# #         for field in required_fields:
# #             if field not in review:
# #                 if field == 'review_date':
# #                     review[field] = datetime.datetime.utcnow()
# #                 else:
# #                     review[field] = None
        
# #         # Update the review document in the collection
# #         review_collection.replace_one({'_id': review['_id']}, review)

# # # Run the update function
# # update_review_structure()
# # print("Review structure updated successfully.")