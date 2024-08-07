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
