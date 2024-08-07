######################################################
######### FUNCTIONAL MACHINE LEARNING MODEL 
######### WAS COMMENTED FOR AN ENHANCED MODEL 
import ast
import time
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import pandas as pd
import nltk
import pymongo
from pymongo import MongoClient
import os
from data.models import get_mongo_client
from nltk.corpus import stopwords
import schedule
import seaborn as sns
import matplotlib.pyplot as plt
nltk.download('stopwords')

# connection_string = os.getenv('MONGO_DB_URI')
# client = pymongo.MongoClient(connection_string)
client = get_mongo_client()
db = client['ibooks']

try:
    client.admin.command('ping')
    print("Connected to MongoDB successfully!")
except Exception as e:
    print(f"Could not connect to MongoDB: {e}")

# Select the database and collection

collection = db['books']

# # Fetch all documents from the collection
# books_cursor = collection.find()

# # Convert the cursor to a list of dictionaries and print the first few documents
# books_list = list(books_cursor)

# if books_list:

#     books_df = pd.DataFrame(books_list)
    
#     print(f"book's table collumns : \n {books_df.columns}")
# else:
#     books_df = pd.DataFrame()
#     print("No documents found in the collection. No data to create dataframe.")
    

def load_and_prepare_data(df):
    # Debugging statements
    print("Type of df:", type(df))
    if isinstance(df, pd.DataFrame):
        print("Columns in df:", df.columns)
    else:
        print("Content of df:", df)
    
    # Fill missing values and convert to string
    df['summary'] = df['summary'].fillna('').astype(str).str.lower()
    df['categories'] = df['categories'].fillna('').astype(str).str.lower()

    # Combining book's summary and categories for more context
    df['Combined_Text'] = df['categories'] + ' ' + df['summary']

    # Text processing
    stop_words = set(stopwords.words('english'))
    df['Combined_Text'] = df['Combined_Text'].apply(lambda x: ' '.join(word for word in x.split() if word not in stop_words))

    # TF-IDF vectorization
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform(df['Combined_Text'])
    return df, tfidf_matrix, tfidf_vectorizer

def recommend_books(user_description, data, tfidf_vectorizer, tfidf_matrix, top_n=10):
    user_tfidf = tfidf_vectorizer.transform([user_description])
    cosine_similarities = linear_kernel(user_tfidf, tfidf_matrix).flatten()
    top_indices = cosine_similarities.argsort()[-top_n:][::-1]
    return data.iloc[top_indices]

def update_books_df():
    global books_df
    # Fetch all documents from the collection
    books_cursor = collection.find()
    books_list = list(books_cursor)
    books_df = pd.DataFrame(books_list)
    # Optionally, save the updated dataframe to a file
    books_df.to_csv('data/updated_dataset/books_data.csv', index=False)
    print("Dataframe updated")

books_df = pd.read_csv(r'data/updated_dataset/books_data.csv')
print(books_df.describe())
    
# Function to convert categories to a string
def categories_to_string(cat):
    if isinstance(cat, str):
        try:
            # Safely evaluate the string representation of the list
            cat = ast.literal_eval(cat)
        except ValueError:
            pass
    if isinstance(cat, list):
        return ', '.join(cat)
    return str(cat)

# Apply the function to the categories column
books_df['categories_str'] = books_df['categories'].apply(categories_to_string)

# Verify the output
print(books_df['categories_str'].head())

# EDA

# Summary statistics
print(books_df.describe())

# Distribution of average ratings
plt.figure(figsize=(10, 6))
sns.histplot(books_df['ratings_average'], bins=20, kde=True)
plt.title('Distribution of Average Ratings')
plt.xlabel('Average Rating')
plt.ylabel('Frequency')
plt.show()

# Most common categories
categories_series = pd.Series(','.join(books_df['categories_str']).split(','))

plt.figure(figsize=(12, 8))
sns.countplot(y=categories_series, order=categories_series.value_counts().iloc[:10].index)
plt.title('Top 10 Most Common Categories')
plt.xlabel('Count')
plt.ylabel('Category')
plt.show()

# Correlation matrix
# plt.figure(figsize=(12, 8))
# sns.heatmap(books_df.corr(), annot=True, cmap='coolwarm')
# plt.title('Correlation Matrix')
# plt.show()

# Books with the highest ratings
top_rated_books = books_df.sort_values(by='ratings_average', ascending=False).head(10)
print(f"top rated books : \n")
print(top_rated_books[['title', 'authors', 'ratings_average', 'categories']])

# Most reviewed books
most_reviewed_books = books_df.sort_values(by='ratings_count', ascending=False).head(10)
print(f"most reviewd books : \n ")
print(most_reviewed_books[['title', 'authors', 'ratings_count', 'categories']])



###########################################################

# Load and prepare data
# data, tfidf_matrix, tfidf_vectorizer = load_and_prepare_data(books_df)

# # Sample description to test the recommendation system
# sample_description = "sciencitif studies and revelations"
# recommended_books = recommend_books(sample_description, data, tfidf_vectorizer, tfidf_matrix)

# # Display recommended books
# print(f"recommendation for the description : {sample_description} \n ")
# print(recommended_books[['title', 'summary', 'authors', 'categories']])
    
# schedule.every().day.do(update_books_df)

# Initial fetch
# update_books_df()

# Keep running the scheduled tasks
# while True:
#     schedule.run_pending()
#     time.sleep(1)
#####################################################################################
#############################################################################
# # load data from the csv file and train it for recommandations based on book's genre and it's description
# def load_and_prepare_data(csv_file):
#     data = pd.read_csv(csv_file)
#     data['Description'] = data['Description'].fillna('').astype(str).str.lower()
#     data['Category'] = data['Category'].fillna('').astype(str).str.lower()

#     # combining boook's description and category for more ctx
#     data['Combined_Text'] =data['Category'] + ' ' +  data['Description']

#     # text processing
#     stop_words = set(stopwords.words('english'))
#     data['Combined_Text'] = data['Combined_Text'].apply(lambda x: ' '.join(word for word in x.split() if word not in stop_words))

#     # TF-IDF vectorization
#     tfidf_vectorizer = TfidfVectorizer()
#     tfidf_matrix = tfidf_vectorizer.fit_transform(data['Combined_Text'])
#     return data, tfidf_matrix, tfidf_vectorizer

# def recommend_books(user_description, data, tfidf_vectorizer, tfidf_matrix, top_n=9):
#     user_tfidf = tfidf_vectorizer.transform([user_description])
#     cosine_similarities = linear_kernel(user_tfidf, tfidf_matrix).flatten()
#     top_indices = cosine_similarities.argsort()[-top_n:][::-1]
#     return data.iloc[top_indices]


# data, tfidf_matrix, tfidf_vectorizer = load_and_prepare_data('data/final_datasets/dataSetCleaned.csv')


# sample_description = "self developement books "
# recommended_books = recommend_books(sample_description, data, tfidf_vectorizer, tfidf_matrix)
# print(f"here's some books you might like : \n {recommended_books}")




# # Load data
# data = np.load('data/preprocessed_data.npz')
# X = data['X']
# df = pd.read_csv('data/cleaned_books_desc_sentiments.csv')
# y = df['Category']  # Assuming 'Category' is the target column

# # Split data to train and test subs
# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# # Initialize and train model
# model = LogisticRegression(max_iter=1000, solver='saga')
# param_grid = {'C': [0.1, 1, 10, 100]}
# grid_search = GridSearchCV(model, param_grid, cv=5, scoring='accuracy')
# grid_search.fit(X_train, y_train)

# # Save the trained model
# joblib.dump(grid_search.best_estimator_, 'model/book_recommendation_model.pkl')

# # Print results
# print(f"Best Hyperparameters: {grid_search.best_params_}")
# print(f"Training Accuracy: {grid_search.best_score_}")
# print(f"Test Accuracy: {grid_search.score(X_test, y_test)}")




# sample_description = "algorihtmes "
# recommended_books = recommend_books(sample_description, data, tfidf_vectorizer, tfidf_matrix)
# print(f"here's some books you might like : \n {recommended_books}")



# if __name__ == "__main__":
#     sample_description = "learning new cultures and religion"
#     book_data = load_and_prepare_data('data/dataSetCleaned.csv')
#     try:
#         recommended_books = recommend_books(sample_description, data, tfidf_vectorizer, tfidf_matrix)
#         print(recommended_books)
#     except Exception as e:
#         print(str(e))