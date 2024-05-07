import pandas as pd
import re
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer

# Load data
data = pd.read_csv('dataSetCleaned.csv')

# Sampling a subset of data
book_data = data.sample(frac=0.3) if len(data) > 1000 else data

# Handling missing values
book_data['Description'] = book_data['Description'].fillna('')

# Convert to lower case and remove punctuation
book_data['Description'] = book_data['Description'].str.lower().str.replace(r'[\W_]+', ' ', regex=True)

# Tokenization
book_data['Description'] = book_data['Description'].str.split()

# Stop word removal
stop_words = set(stopwords.words('english'))
book_data['Description'] = book_data['Description'].apply(lambda x: [word for word in x if word not in stop_words])

# Stemming
stemmer = PorterStemmer()
book_data['Description'] = book_data['Description'].apply(lambda x: [stemmer.stem(word) for word in x])

# Combine tokens back to a single string
book_data['Description'] = book_data['Description'].apply(lambda x: ' '.join(x))

# Save processed data to CSV
book_data.to_csv('dataSetCleaned.csv', index=False)

# Print head of the DataFrame to check
print(book_data.head())
