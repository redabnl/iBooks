from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import pandas as pd

def load_data():
    
    dataset = pd.read_csv('data/dataSetCleaned.csv')
    sampled_data = dataset.sample(frac=0.2)
    
    return sampled_data

def tfidf_feature_extraction(book_data):
    tfidf = TfidfVectorizer(stop_words='english', max_features=2000)
    tfidf_matrix = tfidf.fit_transform(book_data['Description'])
    return tfidf_matrix

def compute_similarity(tfidf_matrix):
    cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)
    return cosine_sim

def main():
    book_data = load_data()
    tfidf_matrix = tfidf_feature_extraction(book_data)
    cosine_sim = compute_similarity(tfidf_matrix)
    # Save or process the cosine similarity matrix as needed
    print(cosine_sim)

if __name__ == "__main__":
    main()

