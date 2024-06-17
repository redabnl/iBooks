import pandas as pd
import numpy as np
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from transformers import BertTokenizer, BertModel
import torch
from sklearn.metrics.pairwise import cosine_similarity
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Load the prepared dataset
prepared_data = pd.read_csv('data/datasets/cleaned_books_rev.csv')

# Ensure column names are strings
prepared_data.columns = prepared_data.columns.astype(str)

# Convert average_rating to float
prepared_data['average_rating'] = prepared_data['average_rating'].astype(float)

# Binary classification for high/low ratings
prepared_data['binary_rating'] = prepared_data['average_rating'].apply(lambda x: 1 if x >= 4.0 else 0)

# Initialize Sentiment Analyzer
sia = SentimentIntensityAnalyzer()
prepared_data['sentiment'] = prepared_data['Combined_Text'].apply(lambda x: sia.polarity_scores(x)['compound'])
print(f"sentiment analysis inintialized : {prepared_data['sentiment']}")

# BERT Tokenizer and Model
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')

print("getting BERT embeddings ...")

def get_bert_embeddings(text):
    inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=512)
    outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).detach().numpy()

# Generate BERT embeddings for Combined_Text
bert_embeddings = np.vstack(prepared_data['Combined_Text'].apply(get_bert_embeddings))

print(f"BERT text embedding done. \n Train and split Now ...")
# Train-test split
X_train, X_test, y_train, y_test = train_test_split(bert_embeddings, prepared_data['binary_rating'], test_size=0.2, random_state=42)

# Function to evaluate models
def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred)
    return accuracy, precision, recall, f1, roc_auc

# Store results
results = {}

# Logistic Regression
log_reg = LogisticRegression()
param_grid_lr = {'C': [0.1, 1, 10], 'max_iter': [100, 200], 'solver': ['liblinear']}
grid_search_lr = GridSearchCV(estimator=log_reg, param_grid=param_grid_lr, cv=3, scoring='accuracy', verbose=1, n_jobs=-1)
grid_search_lr.fit(X_train, y_train)
best_lr = grid_search_lr.best_estimator_
results['Logistic Regression'] = {
    'Best Hyperparameters': grid_search_lr.best_params_,
    'Model Accuracy': grid_search_lr.best_score_,
    'Training Time': grid_search_lr.refit_time_,
    'Evaluation': evaluate_model(best_lr, X_test, y_test)
}



# Display results
for model_name, result in results.items():
    print(f"{model_name}: {result}")

# Save the results
results_df = pd.DataFrame(results).T
results_df.to_csv('data/datasets/FINAL_model_comparison_results.csv')

# Save the best model (Logistic Regression in this case)
joblib.dump(best_lr, 'best_model.pkl')
joblib.dump(tokenizer, 'tokenizer.pkl')




####################
## RANDOM FOREST CLASSIFIER 
# rf = RandomForestClassifier()
# param_grid_rf = {'n_estimators': [100, 200], 'min_samples_split': [2, 5], 'max_depth': [None, 10]}
# grid_search_rf = GridSearchCV(estimator=rf, param_grid=param_grid_rf, cv=3, scoring='accuracy', verbose=1, n_jobs=-1)
# grid_search_rf.fit(X_train, y_train)
# best_rf = grid_search_rf.best_estimator_
# results['Random Forest'] = {
#     'Best Hyperparameters': grid_search_rf.best_params_,
#     'Model Accuracy': grid_search_rf.best_score_,
#     'Training Time': grid_search_rf.refit_time_,
#     'Evaluation': evaluate_model(best_rf, X_test, y_test)
# }



# # Function to get book recommendations based on a given title
# def recommend_books(title, cosine_sim=linear_kernel(tfidf_matrix, tfidf_matrix)):
#     title = title.strip().lower()
#     idx = None
#     for i, t in enumerate(prepared_data['title']):
#         if title in t.lower():
#             idx = i
#             break
#     if idx is None:
#         print(f"The title '{title}' is not found in the dataset.")
#         return []

#     # Get the pairwise similarity scores
#     sim_scores = list(enumerate(cosine_sim[idx]))
#     # Sort the books based on the similarity scores
#     sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
#     # Get the scores of the 10 most similar books
#     sim_scores = sim_scores[1:11]
#     # Get the book indices
#     book_indices = [i[0] for i in sim_scores]
#     # Return the top 10 most similar books
#     return prepared_data['title'].iloc[book_indices]

# # Example usage
# print(recommend_books('soufi mon amour'))

# import pandas as pd
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import linear_kernel
# import nltk
# from nltk.sentiment.vader import SentimentIntensityAnalyzer

# # Load the prepared dataset
# prepared_data = pd.read_csv('data/datasets/cleaned_books_rev.csv', encoding='latin-1')

# # Initialize Sentiment Analyzer
# nltk.download('vader_lexicon')
# sia = SentimentIntensityAnalyzer()

# # Compute the sentiment score for the combined text
# prepared_data['sentiment'] = prepared_data['Combined_Text'].apply(lambda x: sia.polarity_scores(x)['compound'])

# # Create TF-IDF matrix
# tfidf = TfidfVectorizer(stop_words='english')
# tfidf_matrix = tfidf.fit_transform(prepared_data['Combined_Text'])

# # Compute cosine similarity matrix
# cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

# # Function to get book recommendations
# def recommend_books(title, cosine_sim=cosine_sim):
#     title = title.strip().lower()  # Convert input title to lowercase and strip whitespace
#     idx = None
#     for i, t in enumerate(prepared_data['title']):
#         if title in t.lower().strip():
#             idx = i
#             break
#     if idx is None:
#         print(f"The title '{title}' is not found in the dataset.")
#         return []

#     # Get the pairwise similarity scores of all books with that book
#     sim_scores = list(enumerate(cosine_sim[idx]))
#     # Sort the books based on the similarity scores
#     sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
#     # Get the scores of the 10 most similar books
#     sim_scores = sim_scores[1:11]
#     # Get the book indices
#     book_indices = [i[0] for i in sim_scores]
#     # Return the top 10 most similar books
#     return prepared_data['title'].iloc[book_indices]

# # Example usage:
# print(recommend_books('the great gatsby '))



# import pandas as pd
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import linear_kernel
# from sklearn.model_selection import train_test_split, GridSearchCV
# from sklearn.linear_model import LogisticRegression
# import matplotlib.pyplot as plt
# from sklearn.metrics.pairwise import cosine_similarity
# import seaborn as sns
# from nltk.sentiment.vader import SentimentIntensityAnalyzer
# import nltk
# import joblib
# import np
# # Ensure VADER lexicon is downloaded
# nltk.download('vader_lexicon')

# # Load the prepared dataset
# prepared_data = pd.read_csv('data/datasets/cleaned_books_rev.csv')

# # Display the first few rows of the dataset


# #convert the av rating column to float 
# prepared_data['average_rating'] = prepared_data['average_rating'].astype(float)

# prepared_data['title'] = prepared_data['title'].str.lower()

# print(prepared_data.head())
# print(prepared_data.info())


# # Perform sentiment analysis on the combined text
# sia = SentimentIntensityAnalyzer()
# prepared_data['sentiment'] = prepared_data['Combined_Text'].apply(lambda x: sia.polarity_scores(x)['compound'])

# # Binary classification for high/low ratings
# prepared_data['binary_rating'] = prepared_data['average_rating'].astype(float).apply(lambda x: 1 if x >= 4.0 else 0)

# # TF-IDF Vectorization
# tfidf = TfidfVectorizer(stop_words='english')
# tfidf_matrix = tfidf.fit_transform(prepared_data['Combined_Text'])

# # Compute the cosine similarity matrix
# cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

# # Train-test split
# X_train, X_test, y_train, y_test = train_test_split(tfidf_matrix, prepared_data['binary_rating'], test_size=0.2, random_state=42)

# # # Train logistic regression model
# model = LogisticRegression()
# model.fit(X_train, y_train)

# # # Evaluate the model
# # accuracy = model.score(X_test, y_test)
# # print(f"Model Accuracy: {accuracy}")



# # Define the parameter grid
# param_grid = {
#     'C': [0.1, 1, 10, 100],
#     'solver': ['liblinear', 'saga'],
#     'max_iter': [100, 200, 300]
# }

# # Initialize the logistic regression model
# log_reg = LogisticRegression()

# # Initialize GridSearchCV
# grid_search = GridSearchCV(estimator=log_reg, param_grid=param_grid, cv=5, scoring='accuracy', verbose=1, n_jobs=-1)

# # Fit GridSearchCV
# grid_search.fit(X_train, y_train)

# # Best parameters
# print(f"Best Hyperparameters: {grid_search.best_params_}")
# print(f"Model Accuracy: {grid_search.best_score_}")

# # # Save the model for later use
# joblib.dump(model, 'logistic_model.pkl')
# joblib.dump(tfidf, 'tfidf_vectorizer.pkl')




# def recommend_books(title, prepared_data, tfidf_matrix, cosine_sim):
#     try:
#         # Check if the title exists in the DataFrame
#         if title not in prepared_data['title'].values:
#             print(f"The title '{title}' is not found in the dataset.")
#             return []
        
#         # Get the index of the book that matches the title
#         idx = prepared_data[prepared_data['title'] == title].index[0]
        
#         # Get the pairwise similarity scores of all books with that book
#         sim_scores = list(enumerate(cosine_sim[idx]))
        
#         # Sort the books based on the similarity scores
#         sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        
#         # Get the scores of the 10 most similar books
#         sim_scores = sim_scores[1:11]
        
#         # Get the book indices
#         book_indices = [i[0] for i in sim_scores]
        
#         # Return the top 10 most similar books
#         return prepared_data.iloc[book_indices]
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         return []

# # Test the function with a valid and an invalid title
# prepared_data = pd.read_csv('data/datasets/cleaned_books_rev.csv')
# tfidf = TfidfVectorizer(stop_words='english')
# tfidf_matrix = tfidf.fit_transform(prepared_data['Combined_Text'])
# cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

# # Example of a valid title
# print(recommend_books("Harry Potter and the Half-Blood Prince", prepared_data, tfidf_matrix, cosine_sim))

# Example of an invalid title
# print(recommend_books("Some Non-Existent Book Title", prepared_data, tfidf_matrix, cosine_sim))


# # Logistic Regression with GridSearchCV for hyperparameter tuning
# param_grid = {
#     'C': [0.01, 0.1, 1, 10],
#     'solver': ['liblinear', 'saga']
# }
# grid_search = GridSearchCV(LogisticRegression(), param_grid, cv=5)
# grid_search.fit(X_train, y_train)



######## LOGISTIC REGRESSION TEST
# logreg = LogisticRegression(max_iter=1000)
# grid_search = GridSearchCV(logreg, param_grid, cv=5, verbose=1, n_jobs=-1)
# grid_search.fit(X_train, y_train)

# Best parameters and model accuracy
# print(f"Best Hyperparameters: {grid_search.best_params_}")
# best_model = grid_search.best_estimator_
# accuracy = best_model.score(X_test, y_test)
# print(f"Model Accuracy: {accuracy}")

# Plotting the distribution of average ratings
# sns.histplot(prepared_data['average_rating'], kde=True)
# plt.title('Distribution of Average Ratings')
# plt.xlabel('Average Rating')
# plt.ylabel('Frequency')
# plt.show()


######## FIRST TEST 70 % ACCURACY
# # Logistic Regression with hyperparameter tuning
# param_grid = {'C': [0.1, 1, 10], 'solver': ['liblinear', 'saga']}
# logreg = LogisticRegression(max_iter=1000)
# grid_search = GridSearchCV(logreg, param_grid, cv=5, scoring='accuracy')



# import pandas as pd
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import linear_kernel
# from sklearn.model_selection import train_test_split
# from sklearn.linear_model import LogisticRegression
# import matplotlib.pyplot as plt
# import seaborn as sns
# from nltk.sentiment.vader import SentimentIntensityAnalyzer
# import nltk
# import joblib


# nltk.download('vader_lexicon')

# # Load the prepared dataset
# prepared_data = pd.read_csv('data/datasets/cleaned_books_rev.csv')

# # Display the first few rows of the dataset
# print(prepared_data.head())
# print(prepared_data.info())

# # Ensure 'average_rating' is numeric and handle errors
# prepared_data['average_rating'] = pd.to_numeric(prepared_data['average_rating'], errors='coerce')

# # Remove rows with NaN values in 'average_rating'
# prepared_data = prepared_data.dropna(subset=['average_rating'])

# # Binary classification for high/low rating
# prepared_data['binary_rating'] = prepared_data['average_rating'].apply(lambda x: 1 if x >= 4.0 else 0)

# # Text vectorization
# tfidf = TfidfVectorizer(stop_words='english')
# tfidf_matrix = tfidf.fit_transform(prepared_data['Combined_Text'])

# # Sentiment analysis
# sia = SentimentIntensityAnalyzer()
# prepared_data['sentiment'] = prepared_data['Combined_Text'].apply(lambda x: sia.polarity_scores(x)['compound'])

# # Prepare features and labels for model training
# X = tfidf_matrix
# y = prepared_data['binary_rating']

# # Split data into training and test sets
# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# # Train logistic regression model
# model = LogisticRegression()
# model.fit(X_train, y_train)

# # Evaluate the model
# accuracy = model.score(X_test, y_test)
# print(f"Model Accuracy: {accuracy}")

# # Save the model for later use
# joblib.dump(model, 'logistic_model.pkl')
# joblib.dump(tfidf, 'tfidf_vectorizer.pkl')
