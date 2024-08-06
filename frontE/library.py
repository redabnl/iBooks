import os
import streamlit as st
import requests
from data.models import get_mongo_client
from data.book_model import add_review_and_update, fetch_book_by_id, fetch_most_popular_articles, fetch_wishlist_books, update_reading_goal
from PIL import Image
from io import BytesIO
import datetime
from frontE.homePage import display_books_grid, display_book_details, load_user_data
import numpy as np

# Initialize database connection
client = get_mongo_client()
db = client['ibooks']
book_collection = db['books']
users_collection = db['users']
reviews_collection = db['reviews']
interactions = db['interactions']

# Fetch necessary data for recommendations
users = list(users_collection.find())
books = list(book_collection.find())
user_ids = np.array([user['pseudo'] for user in users])
item_ids = np.array([str(book['_id']) for book in books])
categories = [book.get('categories', ['None'])[0] if book.get('categories') else 'None' for book in books]
summaries = [book.get('summary', '') for book in books]


def show_library(user_pseudo):
    user_pseudo = st.session_state['current_user']
    user_data = load_user_data(user_pseudo)
    st.markdown("<link rel='stylesheet' href='frontE/styles/library.css'>", unsafe_allow_html=True)
    st.markdown("""
    <div class="header">
        <h1>Library</h1>
        <div class="nav-links">
            <a href="?page=home">Home</a>
            <a href="?page=library">Library</a>
            <a href="?page=explorer">Explorer</a>
            <a href="?page=logout">Logout</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.header(f"{user_pseudo}'s Library")
    
    st.sidebar.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
    st.sidebar.markdown("<h2>Trending Articles</h2>", unsafe_allow_html=True)
    trending_articles = fetch_most_popular_articles(os.getenv('NYT_API_KEY'))

    if trending_articles:
        if 'article_index' not in st.session_state:
            st.session_state['article_index'] = 0
        
        article_index = st.session_state['article_index']
        article = trending_articles[article_index]
        title = article['title']
        url = article['url']
        media = article.get('media', [])
        cover_url = media[0]['media-metadata'][0]['url'] if media else "frontE/styles/defaultimg.png"
        st.sidebar.image(cover_url, width=100)
        st.sidebar.write(f"[{title}]({url})")

        if st.sidebar.button("Previous Article", key='previous_article'):
            st.session_state['article_index'] = (article_index - 1) % len(trending_articles)
            st.rerun()
        if st.sidebar.button("Next Article", key='next_article'):
            st.session_state['article_index'] = (article_index + 1) % len(trending_articles)
            st.rerun()
    else:
        st.sidebar.write("No trending articles found.")
    st.sidebar.markdown("</div>", unsafe_allow_html=True)

    st.sidebar.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
    st.sidebar.markdown("<h2>Reading Goal</h2>", unsafe_allow_html=True)
    if 'reading_goals' in user_data:
        current_goal = user_data['reading_goals'].get('goal', 'Not set')
        books_read = user_data.get('already_read', [])
        st.sidebar.markdown(f"<p>You have read {len(books_read)} book(s)</p>", unsafe_allow_html=True)
    else:
        current_goal = 'Not set'
        books_read = []

    reading_goal = st.sidebar.radio(
        "Set your reading goal:", 
        [0, 25, 50, 100, 125, 150], 
        index=[0, 25, 50, 100, 125, 150].index(current_goal) if current_goal != 'Not set' else 0,
        key='reading_goal'
    )
    st.sidebar.markdown(f"<p>Current Reading Goal: {reading_goal} books</p>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<p>Books Read: {len(books_read)}</p>", unsafe_allow_html=True)
    
    if st.sidebar.button("Save Goal", key='save_goal'):
        update_reading_goal(user_pseudo, reading_goal)
        st.rerun()
    st.sidebar.markdown("</div>", unsafe_allow_html=True)

    display_wishlist(user_pseudo)
    
    books_read = get_books_read_by_user(user_pseudo)
    if books_read:
        st.write(f"## Read Books by {user_pseudo}")
        cols = st.columns(2)  # Create two columns for displaying books
        for idx, book in enumerate(books_read):
            with cols[idx % 2]:
                display_readBook_details(book)
    else:
        st.write("You haven't read any books yet.")

def generate_wishlist_card(title, book_title_url, authors, description, image_url, published_year, categories):
    """Generate HTML content for a single book card."""
    card_html = f"""
    <div class="wishlist-card">
        <img src="{image_url}" alt="Book Cover" class="wishlist-card-img">
        <div class="wishlist-card-body">
            <h3><a href="{book_title_url}" target="_blank">{title}</a></h3>
            <h4>{authors}</h4>
            <p><strong>Published Year:</strong> {published_year}</p>
            <p><strong>Categories:</strong> {categories}</p>
            <p>{description}...</p>
        </div>
    </div>
    """
    return card_html

def display_wishlist(user_pseudo):
    wishlist_books = fetch_wishlist_books(user_pseudo)
    if not wishlist_books:
        st.write("Your wishlist is empty.")
        return
    
    st.write("## Your Wishlist")

    st.markdown("""
    <style>
        .wishlist-container {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            gap: 20px;
        }
        .wishlist-column {
            flex: 0 0 calc(50% - 20px);
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .wishlist-card {
            display: flex;
            flex-direction: column;
            margin: 10px;
            border: 1px solid #ccc;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            background-color: #fff;
            flex-grow: 1;
        }
        .wishlist-card-img {
            width: 100%;
            border-radius: 10px;
            object-fit: cover;
        }
        .wishlist-card-body {
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            flex-grow: 1;
        }
        .wishlist-card h3 {
            color: #333;
            margin-top: 10px;
        }
        .wishlist-card h3 a {
            text-decoration: none;
            color: #1f77b4;
        }
        .wishlist-card h3 a:hover {
            text-decoration: underline;
        }
        .wishlist-card h4 {
            color: #555;
        }
        .wishlist-card p {
            margin: 5px 0;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='wishlist-container'>", unsafe_allow_html=True)
    # column1, column2 = [], []

    # for i, book in enumerate(wishlist_books):
    #     card_html = generate_wishlist_card(
    #         book_title_url=f"https://cheaper99.com/{book['title'].replace(' ', '%20')}",
    #         title=book['title'],
    #         authors=book['authors'],
    #         description=book.get('summary', '')[:150],  # Limit description characters
    #         image_url=book.get('cover_url', ''),  # Assuming 'cover_url' column for image URLs
    #         published_year=book.get('published_year', 'N/A'),
    #         categories=', '.join(book['categories']) if isinstance(book['categories'], list) else book['categories']
    #     )
    #     if i % 2 == 0:
    #         column1.append(card_html)
    #     else:
    #         column2.append(card_html)

    # st.markdown("<div class='wishlist-column'>" + "".join(column1) + "</div>", unsafe_allow_html=True)
    # st.markdown("<div class='wishlist-column'>" + "".join(column2) + "</div>", unsafe_allow_html=True)
    
    # st.markdown("</div>", unsafe_allow_html=True)
    for i, book in enumerate(wishlist_books):
        card_html = generate_wishlist_card(
            book_title_url=f"https://cheaper99.com/{book['title'].replace(' ', '%20')}",
            title=book['title'],
            authors=book['authors'],
            description=book.get('summary', '')[:150],  # Limit description characters
            image_url=book.get('cover_url', ''),  # Assuming 'cover_url' column for image URLs
            published_year=book.get('published_year', 'N/A'),
            categories=', '.join(book['categories']) if isinstance(book['categories'], list) else book['categories']
        )
        st.markdown(card_html, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

## GET THE REVIEWS LEFT BY USERS FOR LOGGED USER'S READ BOOKS 
def get_reviews_for_book(book_id):
    with get_mongo_client() as client:
        db = client['ibooks']
        reviews_collection = db['reviews']
        return list(reviews_collection.find({"book_id": book_id}))


def get_books_read_by_user(user_pseudo):
    with get_mongo_client() as client:
        db = client['ibooks']
        users_collection = db['users']
        user = users_collection.find_one({"pseudo": user_pseudo})
        if user:
            read_books_ids = user.get('already_read', [])
            books_collection = db['books']
            return list(books_collection.find({"_id": {"$in": read_books_ids}}))
        return []
    
    
def display_readBook_details(book):
    st.markdown("""
     <style>
        .read-book-card {
            display: flex;
            flex-direction: column;
            margin: 10px;
            border: 1px solid #ccc;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            background-color: #fff;
            flex-grow: 1;
        }
        .read-book-card-img {
            width: 100%;
            border-radius: 10px;
            object-fit: cover;
        }
        .read-book-card-body {
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            flex-grow: 1;
        }
        .read-book-card-reviews, .read-book-card-review {
            margin-top: 10px;
        }
        .read-book-card h4 {
            color: #333;
            margin-top: 10px;
        }
        .read-book-card p {
            margin: 5px 0;
        }
    """, unsafe_allow_html=True)
    
    
    title = book.get('title', 'No Title Available')
    authors = book.get('authors', ['Unknown Author'])
    published_year = book.get('published_year', 'Unknown')
    cover_url = book.get('cover_url', r"frontE\styles\defaultimg.png")
    ratings_average = book.get('ratings_average', 0)
    
    user_pseudo = st.session_state.get('current_user', 'guest')
    
    card_html_start = f"""
    <div class="read-book-card">
        <img src="{cover_url}" alt="Book Cover" class="read-book-card-img">
        <div class="read-book-card-body">
            <h4>{title}</h4>
            <p><strong>Authors:</strong> {authors}</p>
            <p><strong>Published Year:</strong> {published_year}</p>
            <p><strong>Average Rating:</strong> {ratings_average}</p>
        </div>
    """
    st.markdown(card_html_start, unsafe_allow_html=True)

    with st.expander("Leave a review?"):
        review_text = st.text_area(f"Leave a review for {title}", key=f"review_{user_pseudo}_{book['_id']}")
        rating = st.slider(f"Rate {title}", 1, 5, key=f"rating_{user_pseudo}_{book['_id']}")
        if st.button(f"Submit review for {title}", key=f"submit_review_{user_pseudo}_{book['_id']}"):
            add_review_and_update(user_pseudo, book['_id'], review_text, rating)
            st.success("Review submitted!")
            st.experimental_rerun()
    
    reviews = get_reviews_for_book(book['_id'])
    
    with st.popover(f"{book['title']}'s reviews :"):
        for review in reviews:
            st.write(f"- {review['user_pseudo']} rated this book {review['rating']} stars")
            st.write(f"  {review['user_pseudo']}'s review : \n > {review['review_text']}")
            st.write("-----------")
        # reviews_html = f"""
        # <div class="read-book-card-reviews">
        #     <details>
        #         <summary>Reviews</summary>
        #         {get_reviews_html(reviews)}
        #     </details>
        # </div>
        # </div>
        # """
        # st.markdown(reviews_html, unsafe_allow_html=True)

def get_reviews_html(book_id):
    reviews = get_reviews_for_book(book_id)
    reviews_html = ""
    for review in reviews:
        reviews_html += f"""
        <div class="review-item">
            <p><strong>{review['user_pseudo']}:</strong> rated this book {review['rating']} stars</p>
            <p>{review['review_text']}</p>
            <hr>
        </div>
        """
    return reviews_html if reviews_html else "<p>No reviews yet.</p>"
###################################################################################
##########################################################################################    
    
# def display_readBook_details(book):
#     title = book.get('title', 'No Title Available')
#     authors = book.get('authors', ['Unknown Author'])
#     published_year = book.get('published_year', 'Unknown')
#     cover_url = book.get('cover_url', r"frontE\styles\defaultimg.png")
#     ratings_average = book.get('ratings_average', 0)

#     user_pseudo = st.session_state.get('current_user', 'guest')
    
#     st.markdown("<div class='read-book-item'>", unsafe_allow_html=True)
    
#     st.image(cover_url, use_column_width=True)
#     st.markdown(f"<div class='read-book-details'>", unsafe_allow_html=True)
#     st.markdown(f"<h4>{title}</h4>", unsafe_allow_html=True)
#     st.markdown(f"<p>Authors: {authors}</p>", unsafe_allow_html=True)
#     st.markdown(f"<p>Published Year: {published_year}</p>", unsafe_allow_html=True)
#     st.markdown(f"<p>Average Rating: {ratings_average}</p>", unsafe_allow_html=True)
    
#     review_pop = st.expander("Leave a review?")
#     with review_pop:
#         review_text = st.text_area(f"Leave a review for {title}", key=f"review_{user_pseudo}_{book['_id']}")
#         rating = st.slider(f"Rate {title}", 1, 5, key=f"rating_{user_pseudo}_{book['_id']}")
#         if st.button(f"Submit review for {title}", key=f"submit_review_{user_pseudo}_{book['_id']}"):
#             add_review_and_update(user_pseudo, book['_id'], review_text, rating)
#             st.success("Review submitted!")
    
#     # st.write("### Reviews:")
#     reviews = get_reviews_for_book(book['_id'])
#     users_rev = st.popover("### Reviews :")
#     with users_rev:
        # for review in reviews:
        #     st.write(f"- {review['user_pseudo']} rated this book {review['rating']} stars")
        #     st.write(f"  {review['user_pseudo']}'s review : \n > {review['review_text']}")
        #     st.write("-----------")
    
#     st.markdown("</div>", unsafe_allow_html=True)
#     st.markdown("</div>", unsafe_allow_html=True)

##################################################################################################
####################################################################################################
# import os
# import streamlit as st
# import requests
# from data.models import get_mongo_client
# from data.book_model import add_review_and_update, fetch_book_by_id, fetch_most_popular_articles, fetch_wishlist_books, update_reading_goal
# from PIL import Image
# from io import BytesIO
# import datetime
# from frontE.libraryI import  get_reviews_for_book
# from frontE.homePage import display_books_grid, display_book_details, load_user_data
# import numpy as np

# # from recommendations_serv.app.data_preparation import (
# #     combine_features, convert_summaries_to_tfidf, encode_categories,
# #     get_sentiment_score, preprocess_summaries, update_model, 
# #     content_based_recommendations, create_interaction_matrix, calculate_metrics, model
# # )



# # Initialize database connection
# client = get_mongo_client()
# db = client['ibooks']
# book_collection = db['books']
# users_collection = db['users']
# reviews_collection = db['reviews']
# interactions = db['interactions']

# # Fetch necessary data for recommendations
# users = list(users_collection.find())
# books = list(book_collection.find())
# user_ids = np.array([user['pseudo'] for user in users])
# item_ids = np.array([str(book['_id']) for book in books])
# categories = [book.get('categories', ['None'])[0] if book.get('categories') else 'None' for book in books]
# summaries = [book.get('summary', '') for book in books]


# def show_library(user_pseudo):
#     user_pseudo = st.session_state['current_user']
#     user_data = load_user_data(user_pseudo)
#     st.markdown("<link rel='stylesheet' href='frontE/styles/library.css'>", unsafe_allow_html=True)
#     st.markdown("""
#     <div class="header">
#         <h1>Library</h1>
#         <div class="nav-links">
#             <a href="?page=home">Home</a>
#             <a href="?page=library">Library</a>
#             <a href="?page=explorer">Explorer</a>
#             <a href="?page=logout">Logout</a>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)
    
#     st.header(f"{user_pseudo}'s Library")
    
#     st.sidebar.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
#     st.sidebar.markdown("<h2>Trending Articles</h2>", unsafe_allow_html=True)
#     trending_articles = fetch_most_popular_articles(os.getenv('NYT_API_KEY'))

#     if trending_articles:
#         if 'article_index' not in st.session_state:
#             st.session_state['article_index'] = 0
        
#         article_index = st.session_state['article_index']
#         article = trending_articles[article_index]
#         title = article['title']
#         url = article['url']
#         media = article.get('media', [])
#         cover_url = media[0]['media-metadata'][0]['url'] if media else "frontE/styles/defaultimg.png"
#         st.sidebar.image(cover_url, width=100)
#         st.sidebar.write(f"[{title}]({url})")

#         if st.sidebar.button("Previous Article", key='previous_article'):
#             st.session_state['article_index'] = (article_index - 1) % len(trending_articles)
#             st.rerun()
#         if st.sidebar.button("Next Article", key='next_article'):
#             st.session_state['article_index'] = (article_index + 1) % len(trending_articles)
#             st.rerun()
#     else:
#         st.sidebar.write("No trending articles found.")
#     st.sidebar.markdown("</div>", unsafe_allow_html=True)

#     st.sidebar.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
#     st.sidebar.markdown("<h2>Reading Goal</h2>", unsafe_allow_html=True)
#     if 'reading_goals' in user_data:
#         current_goal = user_data['reading_goals'].get('goal', 'Not set')
#         books_read = user_data.get('already_read', [])
#         st.sidebar.markdown(f"<p>You have read {len(books_read)} book(s)</p>", unsafe_allow_html=True)
#     else:
#         current_goal = 'Not set'
#         books_read = []

#     reading_goal = st.sidebar.radio(
#         "Set your reading goal:", 
#         [0, 25, 50, 100, 125, 150], 
#         index=[0, 25, 50, 100, 125, 150].index(current_goal) if current_goal != 'Not set' else 0,
#         key='reading_goal'
#     )
#     st.sidebar.markdown(f"<p>Current Reading Goal: {reading_goal} books</p>", unsafe_allow_html=True)
#     st.sidebar.markdown(f"<p>Books Read: {len(books_read)}</p>", unsafe_allow_html=True)
    
#     if st.sidebar.button("Save Goal", key='save_goal'):
#         update_reading_goal(user_pseudo, reading_goal)
#         st.rerun()
#     st.sidebar.markdown("</div>", unsafe_allow_html=True)

    
#     display_wishlist(user_pseudo)
    
#     books_read = get_books_read_by_user(user_pseudo)
#     if books_read:
#         st.write(f"## Read Books by {user_pseudo}")
#         cols = st.columns(2)  # Create two columns for displaying books
#         for idx, book in enumerate(books_read):
#             with cols[idx % 2]:
#                 display_readBook_details(book)
#     else:
#         st.write("You haven't read any books yet.")
    
# def generate_wishlist_card(title, book_title_url, authors, description, image_url, published_year, categories):
#     """Generate HTML content for a single book card."""
#     card_html = f"""
#     <div class="wishlist-card">
#         <img src="{image_url}" alt="Book Cover" class="wishlist-card-img">
#         <div class="wishlist-card-body">
#             <h3><a href="{book_title_url}" target="_blank">{title}</a></h3>
#             <h4>{authors}</h4>
#             <p><strong>Published Year:</strong> {published_year}</p>
#             <p><strong>Categories:</strong> {categories}</p>
#             <p>{description}...</p>
#         </div>
#     </div>
#     """
#     return card_html

# def display_wishlist(user_pseudo):
#     wishlist_books = fetch_wishlist_books(user_pseudo)
#     if not wishlist_books:
#         st.write("Your wishlist is empty.")
#         return
    
#     st.write("## Your Wishlist")

#     st.markdown("""
#     <style>
#         .wishlist-container {
#             display: flex;
#             flex-wrap: wrap;
#             justify-content: space-between;
#             gap: 20px;
#         }
#         .wishlist-column {
#             flex: 0 0 calc(50% - 20px);
#             display: flex;
#             flex-direction: column;
#             gap: 20px;
#         }
#         .wishlist-card {
#             display: flex;
#             flex-direction: column;
#             margin: 10px;
#             border: 1px solid #ccc;
#             border-radius: 10px;
#             padding: 15px;
#             box-shadow: 0 4px 8px rgba(0,0,0,0.1);
#             background-color: #fff;
#             flex-grow: 1;
#         }
#         .wishlist-card-img {
#             width: 100%;
#             border-radius: 10px;
#             object-fit: cover;
#         }
#         .wishlist-card-body {
#             display: flex;
#             flex-direction: column;
#             justify-content: space-between;
#             flex-grow: 1;
#         }
#         .wishlist-card h3 {
#             color: #333;
#             margin-top: 10px;
#         }
#         .wishlist-card h3 a {
#             text-decoration: none;
#             color: #1f77b4;
#         }
#         .wishlist-card h3 a:hover {
#             text-decoration: underline;
#         }
#         .wishlist-card h4 {
#             color: #555;
#         }
#         .wishlist-card p {
#             margin: 5px 0;
#         }
#     </style>
#     """, unsafe_allow_html=True)

#     st.markdown("<div class='wishlist-container'>", unsafe_allow_html=True)
    
    # column1, column2 = [], []

    # for i, book in enumerate(wishlist_books):
    #     card_html = generate_wishlist_card(
    #         book_title_url=f"https://cheaper99.com/{book['title'].replace(' ', '%20')}",
    #         title=book['title'],
    #         authors=book['authors'],
    #         description=book.get('summary', '')[:150],  # Limit description characters
    #         image_url=book.get('cover_url', ''),  # Assuming 'cover_url' column for image URLs
    #         published_year=book.get('published_year', 'N/A'),
    #         categories=', '.join(book['categories']) if isinstance(book['categories'], list) else book['categories']
    #     )
    #     if i % 2 == 0:
    #         column1.append(card_html)
    #     else:
    #         column2.append(card_html)

    # st.markdown("<div class='wishlist-column'>" + "".join(column1) + "</div>", unsafe_allow_html=True)
    # st.markdown("<div class='wishlist-column'>" + "".join(column2) + "</div>", unsafe_allow_html=True)
    
    # st.markdown("</div>", unsafe_allow_html=True)

####################################################################################
####################################################################################


            # st.markdown("<div class='book-item'>", unsafe_allow_html=True)
            # cover_url = book.get('cover_url')
            # if cover_url:
            #     st.image(cover_url, use_column_width=True)
            # book_title_url = f"https://cheaper99.com/{book['title'].replace(' ', '%20')}"
            # st.markdown(f"""
            # <div class='book-details'>
            #     <h4><a href="{book_title_url}" target="_blank">{book['title']}</a></h4>
            #     <p>Author(s): {book['authors']}</p>
            #     <p>Published Year: {book.get('published_year', 'N/A')}</p>
            # </div>
            # """, unsafe_allow_html=True)
            # st.markdown("</div>", unsafe_allow_html=True)

    # st.markdown("</div>", unsafe_allow_html=True)

# def display_wishlist(user_pseudo):
#     wishlist_books = fetch_wishlist_books(user_pseudo)
#     if not wishlist_books:
#         st.write("Your wishlist is empty.")
#         return
    
#     st.write("## Your Wishlist")
    
#     cols = st.columns(3)
#     for idx, book in enumerate(wishlist_books):
#         with cols[idx % 3]:
#             isbn = book['isbn'][0]
#             # cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"
#             cover_url = book.get('cover_url')
#             st.image(cover_url, use_column_width=True)
#             book_title_url = f"https://cheaper99.com/{book['title'].replace(' ', '%20')}"
#             st.markdown(f"[**{book['title']}**]({book_title_url})", unsafe_allow_html=True)
#             st.write(f"**Author(s):** {book['authors']}")
#             st.write(f"**Published Year:** {book.get('published_year', 'N/A')}")
#########################################
# def show_library(user_pseudo):
#     user_pseudo = st.session_state['current_user']
#     st.markdown("<link rel='stylesheet' href='styles/library.css'>", unsafe_allow_html=True)
    
#     st.header(f"{user_pseudo}'s Library")
    
#     display_wishlist(user_pseudo)
        
    # books_read = get_books_read_by_user(user_pseudo)
    
    # if not books_read:
    #     st.write("You haven't read any books yet.")
    #     return
    
    # # st.markdown("<div class='book-container'>", unsafe_allow_html=True)
    
    # readB_display = set()
    
    # st.write(f" ## read books by {user_pseudo}")
    # for book in books_read:
    #     if book['_id'] not in readB_display:
    #         readB_display.add(book['_id'])
    #         display_readBook_details(book)
            
    # st.markdown("</div>", unsafe_allow_html=True)
    
    # Display recommendations
    # st.markdown("<div class='recommendations-section'><h2>Recommended Books</h2></div>", unsafe_allow_html=True)
    # recommended_books = content_based_recommendations(user_pseudo, user_ids, item_ids, interaction_matrix, combined_features)
    # for book in recommended_books:
    #     display_readBook_details(book, user_pseudo, recommendation=True)
################################################################################## 

    
# def display_wishlist(user_pseudo):
#     wishlist_books = fetch_wishlist_books(user_pseudo)
    
#     st.write("## Your Wishlist")
    
#     if not wishlist_books:
#         st.write("Your wishlist is empty.")
#         return
    
#     st.markdown("<div class='book-container'>", unsafe_allow_html=True)
    
#     for book in wishlist_books:
#         book_image = book.get('image_url')
#         title = book.get('title')
#         authors = (book.get('authors', [])[:3])
#         published_year = book.get('published_year')
#         # buy_link = book.get('buy_link')
#         book_title_url = f"https://cheaper99.com/{book['title'].replace(' ', '%20')}"
#     #         st.markdown(f"[**{book['title']}**]({book_title_url})", unsafe_allow_html=True)

#         st.markdown(f"""
#         <div class="book-item">
#             <img src="{book_image}" alt="{title}">
#             <div class="book-details">
#                 <h4>{title}</h4>
#                 <p>Author(s): {authors}</p>
#                 <p>Published Year: {published_year}</p>
#                 <a href="{book_title_url}" target="_blank">Buy Now</a>
#             </div>
#         </div>
#         """, unsafe_allow_html=True)
    
#     st.markdown("</div>", unsafe_allow_html=True)

# def fetch_read_books(user_pseudo):
#     user_pseudo = st.session_state['current_user']
    
#     read_books = interactions.find({"user_id": interactions['user_id'], "interaction_type": "read"})
#     book_ids = [(book['book_id']) for book in read_books]
#     books_info = books.find({"_id": {"$in": book_ids}})
    
#     return books_info


#############################################################################
# ##############################################################################
# def display_readBook_details(book):
#     title = book.get('title', 'No Title Available')
#     authors = book.get('authors', ['Unknown Author'])
#     published_year = book.get('published_year', 'Unknown')
    
#     isbn = book.get('isbn', 'N/A')
#     cover_url = book.get('cover_url', r"frontE\styles\defaultimg.png")
#     ratings_average = book.get('ratings_average', 0)
#     ratings_count = book.get('ratings_count', 0)
#     already_read_count = book.get('already_read_count', 0)
    
#     # st.markdown("<div class='read-books-section'><h2>Books You've Read</h2></div>", unsafe_allow_html=True)
#     cols = st.columns(3)
    
#     user_pseudo = st.session_state.get('current_user', 'guest')
#     with cols[0]:
#         st.image(cover_url, width=120)
#         st.markdown(f"**{title}**")
#         st.markdown(f"Authors: {authors}")
#         st.markdown(f"Published Year: {published_year}")
#         st.markdown(f"ISBN: {isbn}")
#         st.markdown(f"Average rating: {ratings_average}")
#         st.markdown(f"Ratings count: {ratings_count}")
#         st.markdown(f"Read by: {already_read_count}")
        
#         review_pop = st.popover("## Leave a review ?")
#         with review_pop:
#             review_text = st.text_area(f"Leave a review for {title}", key=f"review_{user_pseudo}_{book['_id']}")
#             rating = st.slider(f"Rate {title}", 1, 5, key=f"rating_{user_pseudo}_{book['_id']}")
#             if st.button(f"Submit review for {title}", key=f"submit_review_{user_pseudo}_{book['_id']}"):
#                 add_review_and_update(user_pseudo, book['_id'], review_text, rating)
#                 st.success("Review submitted!")
            
#         st.write("### Reviews:")
#         reviews = get_reviews_for_book(book['_id'])
#         users_rev = st.popover("## Other user's reviews")
#         with users_rev :
#             for review in reviews:
#                 st.write(f"- {review['user_pseudo']} rated this book {review['rating']} stars")
#                 st.write(f"  {review['user_pseudo']}'s review : \n > {review['review_text']}")
#                 st.write("-----------")
#         # st.markdown("</div>", unsafe_allow_html=True)

#     st.write("-----------")


   



# def show_library(user_pseudo):
#     # if 'current_user' not in st.session_state:
#     #     st.session_state['current_user'] = user_pseudo

#     user_pseudo = st.session_state['current_user']
#     st.markdown("<link rel='stylesheet' href='/mnt/data/library.css'>", unsafe_allow_html=True)
    
#     st.header(f"{user_pseudo}'s Library")
    
#     display_wishlist(user_pseudo)
        
#     books_read = get_books_read_by_user(user_pseudo)
    
#     if not books_read:
#         st.write("You haven't read any books yet.")
#         return
    
#     st.markdown("<div class='book-container'>", unsafe_allow_html=True)
    
#     readB_display = set()
    
#     for book in books_read:
#         if book['_id'] not in readB_display:
#             readB_display.add(book['_id'])
#             display_readBook_details(book, user_pseudo)
            
#     st.markdown("</div>", unsafe_allow_html=True)
    


# def update_interaction_matrix(new_interactions, interaction_matrix, user_ids, item_ids):
#     rows, cols, data = interaction_matrix.row.tolist(), interaction_matrix.col.tolist(), interaction_matrix.data.tolist()
#     for interaction in new_interactions:
#         user_index = np.where(user_ids == interaction['user_id'])[0][0]
#         book_index = np.where(item_ids == interaction['book_id'])[0][0]
#         rows.append(user_index)
#         cols.append(book_index)
#         data.append(1)  # Assuming interaction value of 1
#     updated_matrix = coo_matrix((data, (rows, cols)), shape=(len(user_ids), len(item_ids)))
#     return updated_matrix

# def collect_new_interactions():
#     interaction_collection = db['interactions']
#     new_interactions = list(interaction_collection.find())
#     return [{'user_id': interaction['user_id'], 'book_id': interaction['book_id']} for interaction in new_interactions]

# def update_model():
#     global interaction_matrix, model, user_ids, item_ids
#     new_interactions = collect_new_interactions()
#     if new_interactions:
#         interaction_matrix = update_interaction_matrix(new_interactions, interaction_matrix, user_ids, item_ids)
#         model = AlternatingLeastSquares(factors=50, regularization=0.01, iterations=15)
#         model.fit(interaction_matrix.tocsr())
#         print("Model updated with new interactions")




# Ensure `current_user` is initialized
# if 'current_user' not in st.session_state:
#     st.session_state['current_user'] = 'reda'

# Example of how to show the library for the current user
# show_library(st.session_state['current_user'])






        # review_pop = st.expander("Leave a review?")
        # with review_pop:
        #     review_text = st.text_area(f"Leave a review for {title}", key=f"review_{user_pseudo}_{book['_id']}")
        #     rating = st.slider(f"Rate {title}", 1, 5, key=f"rating_{user_pseudo}_{book['_id']}")
        #     if st.button(f"Submit review for {title}", key=f"submit_review_{user_pseudo}_{book['_id']}"):
        #         add_review_and_update(user_pseudo, book['_id'], review_text, rating)
        #         st.success("Review submitted!")
            
        # st.write("### Reviews:")
        # reviews = get_reviews_for_book(book['_id'])
        # users_rev = st.expander("Other user's reviews")
        # with users_rev:
        #     for review in reviews:
        #         st.write(f"- {review['user_pseudo']} rated this book {review['rating']} stars")
        #         st.write(f"  {review['user_pseudo']}'s review : \n > {review['review_text']}")
        #         st.write("-----------")