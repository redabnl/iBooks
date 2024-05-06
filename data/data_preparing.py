import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

book_data = pd.read_csv('booksDatasetclean.csv')
print(book_data.head())

# def load_data(source) :
# # Load the data
#     data_path = 'BooksDatasetClean.csv' 
#     book_data = pd.read_csv(data_path)

#     # Display the first few rows of the dataset to understand its structure
#     #print(book_data.head())
#     print(book_data.isnull().sum())

#     book_data['avg_reviews'] = book_data['avg_reviews'].fillna(book_data['avg_reviews'].mean())

#     # Convert data types if needed
#     book_data['ISBN'] = book_data['ISBN'].astype(str)
#     print(book_data.head())

#     return pd.read_csv(source)
# load_data(source="booksDatasetClean.csv")


# def preprocessing_data(book_description) :
#     tfidf = TfidfVectorizer(stop_words='english')
#     return tfidf.fit_transform(book_description)

# def aggregate_data(users, books, ratings):
#     data = pd.merge(books, ratings, on='book_id')
#     data = pd.merge(data, users, on='pseudo')
#     return data