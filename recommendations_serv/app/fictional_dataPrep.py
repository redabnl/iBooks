import random
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv('MONGO_DB_URI'))
db = client['fictional_ibooks']
book_collection = db['books']

# # Define categories
# SUBJECTS = [
#     "art", "biographies", "children", "computers", "education", 
#     "fiction", "history", "mathematics", "medicine", "philosophy", 
#     "religion", "science", "technology"
# ]

# # Fetch all books
# books = list(book_collection.find())

# # Update categories randomly
# for book in books:
#     new_category = random.choice(SUBJECTS)
#     book_collection.update_one(
#         {"_id": book["_id"]},
#         {"$set": {"category": new_category}}
#     )

# print("Book categories updated successfully!")

# Drop the 'categories' array from all documents in the 'books' collection
result = book_collection.update_many(
    {},
    {"$unset": {"categories": ""}}
)

print(f"Modified {result.modified_count} documents to remove 'categories' array.")


# from faker import Faker
# from pymongo import MongoClient, InsertOne
# import random
# from datetime import datetime
# from bson.objectid import ObjectId
# import os
# from dotenv import load_dotenv


# fake = Faker()
# load_dotenv()

# # Connect to MongoDB and create a separate database for fictional data
# MONGO_DB_URI = os.getenv('MONGO_DB_URI')
# if not MONGO_DB_URI:
#     raise ValueError("MONGO_DB_URI environment variable not set")

# client = MongoClient(MONGO_DB_URI)
# fictional_db = client['fictional_ibooks']

# def generate_fictional_book():
#     return {
#         "_id": ObjectId(),
#         "isbn": fake.isbn13(),
#         "title": fake.sentence(nb_words=5),
#         "authors": [fake.name() for _ in range(random.randint(1, 3))],
#         "published_year": random.randint(1950, 2023),
#         "publisher": [fake.company() for _ in range(random.randint(1, 3))],
#         "cover_url": fake.image_url(),
#         "ratings_average": round(random.uniform(1.0, 5.0), 2),
#         "ratings_count": random.randint(1, 1000),
#         "already_read_count": random.randint(0, 1000),
#         "summary": fake.text(max_nb_chars=200),
#         "categories": [fake.word() for _ in range(random.randint(1, 5))]
#     }

# def generate_fictional_user(book_ids, review_ids):
#     return {
#         "_id": ObjectId(),
#         "pseudo": fake.user_name(),
#         "pwd": fake.password(),
#         "account_creation_date": datetime.now(),
#         "email": fake.email(),
#         "isPrivate": False,
#         "role": "user",
#         "user_reviews": random.sample(review_ids, k=random.randint(0, len(review_ids))),
#         "already_read": random.sample(book_ids, k=random.randint(0, len(book_ids))),
#         "reading_goals": {
#             "goal": random.choice([0, 25, 50, 100, 125, 150]),
#             "current": random.randint(0, 150)
#         },
#         "wishlist": random.sample(book_ids, k=random.randint(0, len(book_ids)))
#     }

# def main():
#     try:
#         # Generate fictional books and insert them in bulk
#         fictional_book_collection = fictional_db['books']
#         fictional_books = [generate_fictional_book() for _ in range(1000)]
#         fictional_book_ids = [book['_id'] for book in fictional_books]
#         fictional_book_collection.bulk_write([InsertOne(book) for book in fictional_books])

#         # Generate fictional users and insert them in bulk
#         fictional_user_collection = fictional_db['users']
#         fictional_review_ids = [ObjectId() for _ in range(500)]  # Assuming some fictional review IDs
#         fictional_users = [generate_fictional_user(fictional_book_ids, fictional_review_ids) for _ in range(500)]
#         fictional_user_collection.bulk_write([InsertOne(user) for user in fictional_users])

#         print("Fictional data generated and inserted successfully into the fictional database.")

#     except Exception as e:
#         print(f"An error occurred: {e}")

# if __name__ == "__main__":
#     main()
