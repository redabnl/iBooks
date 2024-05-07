import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer


nltk.download('stopwords')

book_data = pd.read_csv('booksDatasetClean.csv')



# handling missing values
book_data['Description'] = book_data['Description'].fillna('')

# convert to lower case and remove punctuation
book_data['Description'] = book_data['Description'].apply(lambda x: x.lower())
book_data['Description'] = book_data['Description'].apply(lambda x: re.sub(r'[\W_]+', ' ', x))

#convert text to tokens
book_data['Description'] = book_data['Description'].apply(lambda x: x.split())

#stop word removal
stop_words = set(stopwords.words('english'))
book_data['Description'] = book_data['Description'].apply(lambda x: [word for word in x if word not in stop_words])

stemmer = PorterStemmer()
book_data['Description'] = book_data['Description'].apply(lambda x: [stemmer.stem(word) for word in x])

book_data.to_csv('dataSetCleaned.csv', index=False)

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