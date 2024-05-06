from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from data.data_preparing import book_data

# Using TF-IDF to convert text data to feature vectors
tfidf = TfidfVectorizer(stop_words='english')
book_data['text_feature'] = book_data['text_feature'].fillna('')
tfidf_matrix = tfidf.fit_transform(book_data['text_feature'])

# Compute the cosine similarity matrix
cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)
