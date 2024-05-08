from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import pandas as pd

def load_and_prepare_data(filepath):
    data = pd.read_csv(filepath)
    data['Description'] = data['Description'].fillna('').astype(str).str.lower()
    data['Description'] = data['Description'].str.replace(r'[^\w\s]', ' ')
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf_vectorizer.fit_transform(data['Description'])
    return data, tfidf_matrix, tfidf_vectorizer

def recommend_books(user_description, data, tfidf_vectorizer, tfidf_matrix, top_n=5):
    user_tfidf = tfidf_vectorizer.transform([user_description])
    cosine_similarities = linear_kernel(user_tfidf, tfidf_matrix).flatten()
    top_indices = cosine_similarities.argsort()[-top_n:][::-1]
    return data.iloc[top_indices]


data, tfidf_matrix, tfidf_vectorizer = load_and_prepare_data('dataSetCleaned.csv')
sample_description = " moliere and french culture"
recommended_books = recommend_books(sample_description, data, tfidf_vectorizer, tfidf_matrix)
print(f"here's some books you might like : \n {recommended_books}")



# if __name__ == "__main__":
#     sample_description = "mystery and crime books."
#     book_data = load_and_prepare_data()
#     try:
#         recommended_books = recommend_books_based_on_description(book_data, sample_description)
#         print(recommended_books)
#     except Exception as e:
#         print(str(e))

