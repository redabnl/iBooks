####################################################
##### FUNCTIONNAL EXPLORER PAGE 

import streamlit as st 
from machineL import load_and_prepare_data, recommend_books, books_df
import os
import requests

NYT_API_KEY = os.getenv('NYT_TRNDS_BOOKS_KEY')


def get_trending_books():
    url = f'https://api.nytimes.com/svc/books/v3/lists/current/hardcover-fiction.json?api-key={NYT_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        books = data['results']['books']
        return books
    else:
        st.error("Failed to fetch trending books from NYT.")
        return []

def show_explorer_page():
    pseudo = st.session_state['current_user']
    
    data, tfidf_matrix, tfidf_vectorizer = load_and_prepare_data(books_df)

    st.write("Welcome to the explorer page.")
    user_description = st.text_input("Describe the book you're interested in:", '')

    # if st.button("Find Books", key='explorer_search_btn'):
    #     recommended_books = recommend_books(user_description, data, tfidf_vectorizer, tfidf_matrix)
    #     if recommended_books.empty:
    #         st.error("No books found. Please try again.")
    #     else:
    #         st.write(f"here's our recommendations for : {pseudo}")
    #         show_books_as_cards(recommended_books)

    # Layout for main content and sidebar for trending books
    col1, col2 = st.columns([3, 1])

    with col1:
        # Main content (book recommendations based on books description)
        if st.button("Find Books", key='explorer_search_btn'):
            recommended_books = recommend_books(user_description, data, tfidf_vectorizer, tfidf_matrix)
            if recommended_books.empty:
                st.error("No books found. Please try again.")
            else:
                st.write("## Recommendations :")
                st.write(f"here's our recommendations for : {pseudo}")
                show_books_as_cards(recommended_books)
         # Display top rated books
        st.header("Top Rated Books")
        top_rated_books = books_df.sort_values(by='ratings_average', ascending=False).head(10)
        show_books_as_cards(top_rated_books)

    with col2:
        # Sidebar content (trending books)
        st.write("## Trending Books")
        trending_books = get_trending_books()
        if trending_books:
            show_trending_books_as_cards(trending_books)
            
            
def generate_card(title, authors,description,image_url, rank, buy_links):
    """Generate HTML content for a single book card."""
    card_html = f"""
    <div style="margin: 10px; width: 300px; border: 1px solid #ccc; border-radius: 5px; padding: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <img src="{image_url}" alt="Book Cover" style="width:100%">
        <h3>{title}</h3>
        <h4>{authors}</h4>  
        <p>{description} ... </p>
    </div>
    """
    return card_html

def show_books_as_cards(books_df):
    st.write("<div style='display: flex; flex-wrap: wrap;'>", unsafe_allow_html=True)
    
    for _, row in books_df.iterrows():
        card_html = generate_card(
            rank = None,
            title=row['title'],
            authors=row['authors'],
            description=row['summary'][:200],  # Limit description characters   
            image_url=row.get('cover_url', ''),  
            buy_links = None
        )
        st.markdown(card_html, unsafe_allow_html=True)
    st.write("</div>", unsafe_allow_html=True)

def show_trending_books_as_cards(books):
    st.write("<div style='display: flex; flex-wrap: wrap;'>", unsafe_allow_html=True)
    
    for book in books:
        card_html = generate_card(
            rank = book['rank'],
            title=book['title'],
            authors=book['author'],
            description=book['description'][:200], 
            image_url=book['book_image'], 
            buy_links = book['buy_links']
        )
        st.markdown(card_html, unsafe_allow_html=True)
    st.write("</div>", unsafe_allow_html=True)

# import streamlit as st
# import pandas as pd
# import numpy as np
# import joblib
# from sklearn.metrics.pairwise import cosine_similarity
# import random

# # Load the trained model and preprocessed data
# model = joblib.load('model/book_recommendation_model.pkl')
# data = np.load('data/preprocessed_data.npz')
# X = data['X']
# book_data = pd.read_csv('data/cleaned_books_desc_sentiments.csv')

# def recommend_books(description):
#     # Preprocess the description
#     description_features = model['vectorizer'].transform([description])
    
#     # Compute similarity
#     similarities = cosine_similarity(description_features, X)
#     similarities = similarities.flatten()
    
#     # Get top N similar books
#     top_n_idx = similarities.argsort()[-5:][::-1]
#     recommended_books = book_data.iloc[top_n_idx]
#     return recommended_books

# def display_trending_books():
#     trending_books = book_data.sample(n=5)
#     for _, book in trending_books.iterrows():
#         st.write(f"**Title:** {book['title']}")
#         st.write(f"**Author:** {book['Authors']}")
#         st.write(f"**Published Year:** {book['Publish Date (Year)']}")
#         st.write(f"**ISBN:** {book['ISBN']}")
#         st.image(book['cover_url'], width=100)
#         st.write("---")

# st.title("Explorer Page")
# st.write("Describe the book you're interested in:")

# description = st.text_area("Book Description")

# if st.button("Find Books"):
#     if description:
#         recommended_books = recommend_books(description)
#         st.write("Here are our recommendations for you:")
#         for _, book in recommended_books.iterrows():
#             st.write(f"**Title:** {book['title']}")
#             st.write(f"**Author:** {book['Authors']}")
#             st.write(f"**Published Year:** {book['Publish Date (Year)']}")
#             st.write(f"**ISBN:** {book['ISBN']}")
#             st.image(book['cover_url'], width=100)
#             st.write("---")
#     else:
#         st.write("Please enter a book description.")

# st.write("Trending Books:")
# display_trending_books()









    # Close the HTML block
    # Example of a card layout for book details
    # st.markdown(
    #     """
    #     <div class="card">
    #         <div class="card-title">Empires Ascendant: Time Frame 400 Bc-Ad 200</div>
    #         <div class="card-author">By Time-Life Books</div>
    #         <div class="card-description">examines the different cultures that were emerging between 400 bc and 200...</div>
    #     </div>
    #     <div class="card">
    #         <div class="card-title">The Holy Land (Lost Civilizations)</div>
    #         <div class="card-author">By Time-Life Books</div>
    #         <div class="card-description">looks at the history geography and ancient cultures of the holy land...</div>
    #     </div>
    #     """, unsafe_allow_html=True
    # )

              

# def main():
#     # Check login state
#     if st.session_state.get('logged_in', False):
#         show_explorer_page()  
#     else:
#         st.write("Please log in.")  # Or redirect them to the login page

# if __name__ == "__main__":
#     main()