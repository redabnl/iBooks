import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

# Load processed data
data = np.load('data/processed_data.npz')
X, y = data['X'], data['y']

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize logistic regression model
model = LogisticRegression(max_iter=200, solver='saga')

# Hyperparameter tuning
param_grid = {'C': [0.1, 1, 10, 100]}
grid_search = GridSearchCV(model, param_grid, cv=5, scoring='accuracy')
grid_search.fit(X_train, y_train)

# Evaluate model
best_model = grid_search.best_estimator_
y_pred = best_model.predict(X_test)
metrics = {
    'Model Accuracy': accuracy_score(y_test, y_pred),
    'Precision': precision_score(y_test, y_pred),
    'Recall': recall_score(y_test, y_pred),
    'F1-Score': f1_score(y_test, y_pred),
    'ROC-AUC': roc_auc_score(y_test, y_pred),
    'Best Hyperparameters': grid_search.best_params_,
    'Training Time': grid_search.refit_time_
}

print("Logistic Regression Metrics:", metrics)

# Save the model and metrics
joblib.dump(best_model, 'best_logistic_regression_model.pkl')
joblib.dump(grid_search.best_params_, 'best_hyperparameters.pkl')
np.savez_compressed('model_metrics.npz', **metrics)

print("Model training completed and saved.")



print("Model training completed and saved.")


#############################################
# import joblib
# from sklearn.linear_model import LogisticRegression
# from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
# from sklearn.model_selection import GridSearchCV
# import time

# # Load the preprocessed data
# X_train, X_test, y_train, y_test = joblib.load('data/preprocessed_data.pkl')
# tfidf = joblib.load('data/tfidf_vectorizer.pkl')

# # Define a function to train and evaluate a classifier
# def train_and_evaluate_model(model, param_grid, model_name):
#     grid_search = GridSearchCV(model, param_grid, cv=5, scoring='accuracy', n_jobs=-1, verbose=1)
    
#     start_time = time.time()
#     grid_search.fit(X_train, y_train)
#     training_time = time.time() - start_time
    
#     best_model = grid_search.best_estimator_
#     y_pred = best_model.predict(X_test)
    
#     metrics = {
#         'Model Accuracy': accuracy_score(y_test, y_pred),
#         'Precision': precision_score(y_test, y_pred),
#         'Recall': recall_score(y_test, y_pred),
#         'F1-Score': f1_score(y_test, y_pred),
#         'ROC-AUC': roc_auc_score(y_test, y_pred),
#         'Best Hyperparameters': grid_search.best_params_,
#         'Training Time': training_time
#     }
    
#     print(f"{model_name} Metrics: {metrics}")
    
#     return best_model, metrics

# # Logistic Regression
# log_reg = LogisticRegression()
# log_reg_param_grid = {'C': [0.1, 1, 10, 100], 'solver': ['liblinear', 'saga']}
# best_log_reg_model, log_reg_metrics = train_and_evaluate_model(log_reg, log_reg_param_grid, "Logistic Regression")

# # Save the best model
# joblib.dump(best_log_reg_model, 'best_description_model.pkl')


######################################################################################
# import pandas as pd
# from sklearn.model_selection import train_test_split, GridSearchCV
# from sklearn.linear_model import LogisticRegression
# from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
# from sklearn.feature_extraction.text import TfidfVectorizer
# import joblib

# # Load the prepared dataset
# prepared_data = pd.read_csv('data/datasets/cleaned_books_desc_sentiments.csv')

# # Ensure column names are strings
# prepared_data.columns = prepared_data.columns.astype(str)

# # Convert sentiment to float
# prepared_data['sentiment'] = prepared_data['sentiment'].astype(float)

# # Binary classification for high/low ratings
# prepared_data['binary_rating'] = prepared_data['sentiment'].apply(lambda x: 1 if x >= 0 else 0)

# # Initialize TF-IDF Vectorizer
# tfidf = TfidfVectorizer(stop_words='english')
# tfidf_matrix = tfidf.fit_transform(prepared_data['description'])

# # Train-test split
# X_train, X_test, y_train, y_test = train_test_split(tfidf_matrix, prepared_data['binary_rating'], test_size=0.2, random_state=42)

# # Initialize Logistic Regression model
# log_reg = LogisticRegression()

# # Hyperparameter grid
# log_reg_param_grid = {
#     'C': [0.1, 1, 10],
#     'max_iter': [100, 200],
#     'solver': ['liblinear', 'saga']
# }

# # GridSearchCV for Logistic Regression
# log_reg_grid_search = GridSearchCV(estimator=log_reg, param_grid=log_reg_param_grid, cv=3, scoring='accuracy', verbose=1, n_jobs=-1)
# log_reg_grid_search.fit(X_train, y_train)

# # Best model and its scores
# log_reg_best_model = log_reg_grid_search.best_estimator_

# # Model evaluation
# log_reg_y_pred = log_reg_best_model.predict(X_test)

# # Metrics
# log_reg_metrics = {
#     'Model Accuracy': accuracy_score(y_test, log_reg_y_pred),
#     'Precision': precision_score(y_test, log_reg_y_pred),
#     'Recall': recall_score(y_test, log_reg_y_pred),
#     'F1-Score': f1_score(y_test, log_reg_y_pred),
#     'ROC-AUC': roc_auc_score(y_test, log_reg_y_pred),
#     'Best Hyperparameters': log_reg_grid_search.best_params_,
#     'Training Time': log_reg_grid_search.refit_time_
# }

# print(f"Logistic Regression Metrics: {log_reg_metrics}")

# # Save the best model
# joblib.dump(log_reg_best_model, 'best_model_descriptions.pkl')
# joblib.dump(tfidf, 'tfidf_vectorizer_descriptions.pkl')
