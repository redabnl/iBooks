import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from transformers import BertTokenizer, BertModel
import torch
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from tqdm import tqdm




# Load the prepared dataset with a specified encoding and error handling
df = pd.read_csv('BooksDatasetClean.csv', encoding='latin1', on_bad_lines='skip')

# Ensure column names are stripped of any leading/trailing whitespace
df.columns = df.columns.str.strip()

print("dataset's columns : \n")
print(df.columns)

print("dataset's head : \n", df.head())

# Initialize sentiment analyzer
sia = SentimentIntensityAnalyzer()

# Calculate sentiment scores for descriptions
df['sentiment'] = df['Description'].apply(lambda x: sia.polarity_scores(str(x))['compound'])

# Initialize BERT tokenizer and model
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')

print("tokenizer and BERT initialized...")
print("gpu or cpu ?")
# Move model to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
print("using : ", device)

def get_bert_embeddings(text):
    inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=512)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).detach().cpu().numpy()

batch_size = 16
embeddings = []
for i in tqdm(range(0, len(df), batch_size)):
    batch_texts = df['Description'][i:i + batch_size].fillna('').tolist()
    batch_embeddings = get_bert_embeddings(batch_texts)
    embeddings.append(batch_embeddings)

# Calculate BERT embeddings for descriptions
df['bert_embeddings'] = df['Description'].apply(lambda x: get_bert_embeddings(str(x)))
print("BERT embeddings calculated")

# Combine TF-IDF and sentiment features
tfidf = TfidfVectorizer(stop_words='english', max_features=5000, ngram_range=(1, 2))
tfidf_matrix = tfidf.fit_transform(df['Description'].fillna(''))
print("TF-IDF calculated")

# Reduce dimensions of TF-IDF features
svd = TruncatedSVD(n_components=100)
tfidf_matrix_reduced = svd.fit_transform(tfidf_matrix)
print("TF-IDF dimensions reduced")

# Stack TF-IDF features with sentiment scores and BERT embeddings
bert_embeddings = np.vstack(df['bert_embeddings'])
X = np.hstack((tfidf_matrix_reduced, df[['sentiment']].values, bert_embeddings))
y = df['Category']  # Assuming 'Category' is the target column

# Save processed data
np.savez_compressed('processed_data.npz', X=X, y=y)
print("Data preprocessing completed and saved.")

df.to_csv('datasets/cleaned_books_desc_sentiments.csv', index=False)
print("Data preprocessing completed and saved to 'datasets/cleaned_books_desc_sentiments.csv'")
