import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer



def load_data(source) :
# Load the data
    data_path = 'final_book_dataset_kaggle2.csv'  # Update this with the path to your CSV file
    book_data = pd.read_csv(data_path)

    # Display the first few rows of the dataset to understand its structure
    #print(book_data.head())
    print(book_data.isnull().sum())

    book_data['avg_reviews'] = book_data['avg_reviews'].fillna(book_data['avg_reviews'].mean())

    # Convert data types if needed
    book_data['ISBN'] = book_data['ISBN'].astype(str)
    print(book_data.head())

    return pd.read_csv(source)


def preprocessing_data(book_description) :
    tfidf = TfidfVectorizer(stop_words='english')
    return tfidf.fit_transform(book_description)

def aggregate_data(users, books, ratings):
    data = pd.merge(books, ratings, on='book_id')
    data = pd.merge(data, users, on='pseudo')
    return data