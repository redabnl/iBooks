import numpy as np
from pymongo import MongoClient
from bson.objectid import ObjectId
from implicit.als import AlternatingLeastSquares
from scipy.sparse import coo_matrix
from dotenv import load_dotenv
import os
import schedule
import time
import datetime

# Load environment variables
load_dotenv()

# Connect to MongoDB for real-time data
client = MongoClient(os.getenv('MONGO_DB_URI'))
real_db = client['ibooks']  # Real  database
user_collection = real_db['users']
book_collection = real_db['books']
interaction_collection = real_db['interactions']

# Fetch users and books from real  database
users = list(user_collection.find())
books = list(book_collection.find())

# mappings from user and item IDs to indices
user_ids = np.array([user['pseudo'] for user in users])
item_ids = np.array([book['_id'] for book in books])

# Initialise an empty interaction matrix
interaction_matrix = coo_matrix(([], ([], [])), shape=(len(user_ids), len(item_ids)))

# Func to update interaction matrix with new user interactions
def update_interaction_matrix(new_interactions, interaction_matrix, user_ids, item_ids):
    rows, cols, data = interaction_matrix.row.tolist(), interaction_matrix.col.tolist(), interaction_matrix.data.tolist()
    for interaction in new_interactions:
        user_index = np.where(user_ids == interaction['user_id'])[0][0]
        book_index = np.where(item_ids == interaction['book_id'])[0][0]
        rows.append(user_index)
        cols.append(book_index)
        data.append(1)  # Assuming interaction value of 1
    updated_matrix = coo_matrix((data, (rows, cols)), shape=(len(user_ids), len(item_ids)))
    return updated_matrix

# Function to collect new interactions
def collect_new_interactions():
    last_update_time = get_last_update_time()  # Function to get the last update time
    interaction_collection = real_db['interactions']
    
    # Fetch new interactions since the last update time
    new_interactions = list(interaction_collection.find({'timestamp': {'$gt': last_update_time}}))
    
    # Update the last update time to the latest interaction's timestamp
    if new_interactions:
        latest_interaction_time = max(interaction['timestamp'] for interaction in new_interactions)
        update_last_update_time(latest_interaction_time)  # Function to update the last update time
    
    # Return the new interactions in the required format
    return [{'user_id': interaction['user_id'], 'book_id': interaction['book_id']} for interaction in new_interactions]

def get_last_update_time():
    try:
        with open('last_update_time.txt', 'r') as file:
            last_update_time = float(file.read())
    except FileNotFoundError:
        last_update_time = 0  # If the file doesn't exist, assume no previous updates
    return last_update_time

def update_last_update_time(timestamp):
    with open('last_update_time.txt', 'w') as file:
        file.write(str(timestamp))

# Periodically update the model with new interactions
def periodic_model_update():
    global interaction_matrix, model, user_ids, item_ids
    
    new_interactions = collect_new_interactions()
    if new_interactions:
        interaction_matrix = update_interaction_matrix(new_interactions, interaction_matrix, user_ids, item_ids)
        model = AlternatingLeastSquares(factors=50, regularization=0.01, iterations=15)
        model.fit(interaction_matrix.tocsr())
        print("Model updated with new interactions")

# Schedule periodic updates for the model (daily)
schedule.every().day.at("00:00").do(periodic_model_update)

while True:
    schedule.run_pending()
    time.sleep(60)
