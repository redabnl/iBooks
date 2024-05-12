import pandas as pd
import re
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer

# Load data
book_data = pd.read_csv('BooksDatasetClean.csv')

# Sampling data for CPU and memory reasons
#book_data = book_data.sample(frac=0.3) if len(book_data) > 1000 else book_data

# Handling missing values for both description and category
book_data['Description'] = book_data['Description'].fillna('').astype(str)
book_data['Category'] = book_data['Category'].fillna('').astype(str)

# Convert to lower case and remove non-alphanumeric characters for bot fieds
book_data['Description'] = book_data['Description'].str.lower().str.replace(r'[\W_]+', ' ', regex=True)
book_data['Category'] = book_data['Category'].str.lower().str.replace(r'[\W_]+', ' ', regex=True)

# Combine description and category into a single string
book_data['Combined_Text'] = book_data['Description'] + ' ' + book_data['Category']

# Tokenization
book_data['Combined_Text'] = book_data['Combined_Text'].str.split()

# Stop word removal
stop_words = set(stopwords.words('english'))
book_data['Combined_Text'] = book_data['Combined_Text'].apply(lambda x: [word for word in x if word not in stop_words])

# Stemming (said it was optional but why not )
stemmer = PorterStemmer()
book_data['Combined_Text'] = book_data['Combined_Text'].apply(lambda x: [stemmer.stem(word) for word in x])

# Combining tokens back to a single string
book_data['Combined_Text'] = book_data['Combined_Text'].apply(lambda x: ' '.join(x))

# Save the processed data into a clean csv file
book_data.to_csv('dataSetCleaned.csv', index=False)

print(f"data prepared for you \n {book_data['Combined_Text']}")

# Test function
# print(book_data.head())
