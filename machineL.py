######################################################
######### FUNCTIONAL MACHINE LEARNING MODEL 
######### WAS COMMENTED FOR AN ENHANCED MODEL 
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import pandas as pd
import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')



# load data from the csv file and train it for recommandations based on book's genre and it's description
def load_and_prepare_data(csv_file):
    data = pd.read_csv(csv_file)
    data['Description'] = data['Description'].fillna('').astype(str).str.lower()
    data['Category'] = data['Category'].fillna('').astype(str).str.lower()

    # combining boook's description and category for more ctx
    data['Combined_Text'] = data['Description'] + ' ' + data['Category']

    # text processing
    stop_words = set(stopwords.words('english'))
    data['Combined_Text'] = data['Combined_Text'].apply(lambda x: ' '.join(word for word in x.split() if word not in stop_words))

    # TF-IDF vectorization
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform(data['Combined_Text'])
    return data, tfidf_matrix, tfidf_vectorizer

def recommend_books(user_description, data, tfidf_vectorizer, tfidf_matrix, top_n=9):
    user_tfidf = tfidf_vectorizer.transform([user_description])
    cosine_similarities = linear_kernel(user_tfidf, tfidf_matrix).flatten()
    top_indices = cosine_similarities.argsort()[-top_n:][::-1]
    return data.iloc[top_indices]


data, tfidf_matrix, tfidf_vectorizer = load_and_prepare_data('data/dataSetCleaned.csv')
# sample_description = "cooking books with multicultural food and recipes "
# recommended_books = recommend_books(sample_description, data, tfidf_vectorizer, tfidf_matrix)
# print(f"here's some books you might like : \n {recommended_books}")




# import numpy as np
# from sklearn.linear_model import LogisticRegression
# from sklearn.model_selection import train_test_split, GridSearchCV
# import joblib
# import pandas as pd

# # Load data
# data = np.load('data/preprocessed_data.npz')
# X = data['X']
# df = pd.read_csv('data/cleaned_books_desc_sentiments.csv')
# y = df['Category']  # Assuming 'Category' is the target column

# # Split data
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