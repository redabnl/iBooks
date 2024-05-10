from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import pandas as pd
import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')


def load_and_prepare_data(csv_file):
    data = pd.read_csv(csv_file)
    data['Description'] = data['Description'].fillna('').astype(str).str.lower()
    data['Category'] = data['Category'].fillna('').astype(str).str.lower()

    # Combine description and category into a single text column
    data['Combined_Text'] = data['Description'] + ' ' + data['Category']

    # Optional: further text processing (e.g., stemming, lemmatization)
    stop_words = set(stopwords.words('english'))
    data['Combined_Text'] = data['Combined_Text'].apply(lambda x: ' '.join(word for word in x.split() if word not in stop_words))

    # Proceed with TF-IDF vectorization
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform(data['Combined_Text'])
    return data, tfidf_matrix, tfidf_vectorizer

def recommend_books(user_description, data, tfidf_vectorizer, tfidf_matrix, top_n=9):
    user_tfidf = tfidf_vectorizer.transform([user_description])
    cosine_similarities = linear_kernel(user_tfidf, tfidf_matrix).flatten()
    top_indices = cosine_similarities.argsort()[-top_n:][::-1]
    return data.iloc[top_indices]


data, tfidf_matrix, tfidf_vectorizer = load_and_prepare_data('data/dataSetCleaned.csv')
# sample_description = "algorihtmes "
# recommended_books = recommend_books(sample_description, data, tfidf_vectorizer, tfidf_matrix)
# print(f"here's some books you might like : \n {recommended_books}")



if __name__ == "__main__":
    sample_description = "books to read to kids about superheroes and villans"
    book_data = load_and_prepare_data('data/dataSetCleaned.csv')
    try:
        recommended_books = recommend_books(sample_description, data, tfidf_vectorizer, tfidf_matrix)
        print(recommended_books)
    except Exception as e:
        print(str(e))

