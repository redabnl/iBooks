from flask import redirect
import streamlit as st
from data.book_model import fetch_book_subjects, fetch_books_by_title, get_mongo_client, add_book_to_already_read, add_book_to_wishlist, fetch_most_popular_articles, fetch_book_details,  update_reading_goal
# from data.models import log_interaction
from frontE.explorer import show_explorer_page
from bson.objectid import ObjectId
from PIL import Image
from io import BytesIO
import requests
import os
from datetime import datetime
import logging
import hashlib
import streamlit.components.v1 as components
import urllib.parse as urlparse
from urllib.parse import parse_qs


logging.basicConfig(level=logging.INFO)

client = get_mongo_client()
db = client['ibooks']
book_collection = db['books']
users_collection = db['users']
reviews_collection = db['reviews']


# Delete books with missing or empty author names
# result = book_collection.delete_many({'authors': {'$in': [None, '']}})

# # Fetch all book IDs
# book_ids = set(book['_id'] for book in book_collection.find({}, {'_id': 1}))

# # Function to clean a user's collection
# def clean_user_collection(collection_name, user_field):
#     users = users_collection.find({collection_name: {'$exists': True}})
#     for user in users:
#         original_count = len(user.get(collection_name, []))
#         cleaned_collection = [book_id for book_id in user.get(collection_name, []) if book_id in book_ids]
#         if len(cleaned_collection) != original_count:
#             users_collection.update_one({'_id': user['_id']}, {'$set': {collection_name: cleaned_collection}})
#             print(f"Cleaned {collection_name} for user {user['pseudo']}. Removed {original_count - len(cleaned_collection)} missing book(s).")

# # Clean the user's collections
# clean_user_collection('wishlist', 'wishlist')
# clean_user_collection('already_read', 'already_read')

# # Clean the reviews collection
# reviews = reviews_collection.find()
# for review in reviews:
#     if review['book_id'] not in book_ids:
#         reviews_collection.delete_one({'_id': review['_id']})
#         print(f"Deleted review for missing book ID {review['book_id']} by user {review['user_pseudo']}.")

# print("cleaned all users collections")


# Initialize session state for pagination
if 'page' not in st.session_state:
    st.session_state.page = 1
if 'title_query' not in st.session_state :
    st.session_state.title_query = ""

# Function to update the page number
def change_page(new_page):
    st.session_state.page = new_page

def search_book_by_title(title):
    st.session_state.title_query = title
    st.experimental_rerun()


def inject_js():
    js_code = """
    <script>
    function searchBook(title) {
        const streamlitDoc = window.parent.document;
        const input = streamlitDoc.querySelector("input[aria-label='Search by title input']");
        const button = streamlitDoc.querySelector("button[aria-label='Search']");
        input.value = title;
        const event = new Event('input', { bubbles: true });
        input.dispatchEvent(event);
        button.click();
    }
    </script>
    """
    st.components.v1.html(js_code)
inject_js()

from streamlit.components.v1 import html

# def make_clickable_title(title):
#     # JavaScript to trigger a search with the clicked title
#     js_code = f"""
#     <script>
#     function searchTitle(title) {{
#         window.parent.document.querySelectorAll('input')[0].value = title;
#         window.parent.document.querySelectorAll('button')[0].click();
#     }}
#     </script>
#     <a href="javascript:searchTitle('{title}');">{title}</a>
#     """
#     return js_code
def make_clickable_title(title):
    return f'<a href="javascript:void(0);" onclick="window.location.href = \'?sub_search_query={title}\'">{title}</a>'

def display_sidebar():
    user_data = load_user_data(st.session_state['current_user'])
    st.sidebar.title('Trending Articles')
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
        
    st.sidebar.write("")
    st.sidebar.title('Reading Goal')
    current_goal = user_data['reading_goals'].get('goal', 'Not set')
    books_read = len(user_data.get('already_read', []))

    st.sidebar.write(f"You have read {books_read} book(s)")
    st.sidebar.write("Set your reading goal:")
    new_goal = st.sidebar.radio("Select goal:", [0, 25, 50, 100, 125, 150], index=[0, 25, 50, 100, 125, 150].index(current_goal))
    st.session_state['reading_goal'] = new_goal

    progress = (books_read / new_goal) * 100 if new_goal > 0 else 0
    st.sidebar.write(f"Current Reading Goal: {new_goal} books")
    st.sidebar.write(f"Books Read: {books_read}")

    # Vertical progress bar
    st.sidebar.markdown("""
    <style>
        .progress-container {
            width: 100%;
            background-color: #f3f3f3;
            border-radius: 25px;
        }
        .progress-bar {
            width: 100%;
            height: 30px;
            background-color: #4caf50;
            border-radius: 25px;
            text-align: center;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)

    st.sidebar.markdown(f"""
    <div class="progress-container" style="height: 200px;">
        <div class="progress-bar" style="height: {progress}%; width: 100%;">
            {int(progress)}%
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("Save Goal"):
        st.session_state['reading_goal'] = new_goal


def load_user_data(user_pseudo):
    client = get_mongo_client()
    db = client['ibooks']
    user = db.users.find_one({"pseudo": user_pseudo})
    return user

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def fetch_personalized_recommendations(user_pseudo):
    response = requests.get(f'http://localhost:5000/recommendations/{user_pseudo}')
    return response.json().get('recommendations', [])

def show_user_homepage(user_pseudo):
    local_css("frontE/styles/homePage.css")

    user_pseudo = st.session_state.get('current_user', 'default_user')
    user_data = load_user_data(user_pseudo)

    st.markdown("""
    <style>
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #f8f9fa;
            padding: 10px;
        }
        .nav-links {
            display: flex;
            gap: 15px;
        }
        .nav-links a {
            text-decoration: none;
            color: #000;
            font-weight: bold;
        }
    </style>
    
    """, unsafe_allow_html=True)

    # Sidebar
    # st.sidebar.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
    # st.sidebar.markdown("<h2>Trending Articles</h2>", unsafe_allow_html=True)
    # trending_articles = fetch_most_popular_articles(os.getenv('NYT_API_KEY'))

    # if trending_articles:
    #     if 'article_index' not in st.session_state:
    #         st.session_state['article_index'] = 0
        
    #     article_index = st.session_state['article_index']
    #     article = trending_articles[article_index]
    #     title = article['title']
    #     url = article['url']
    #     media = article.get('media', [])
    #     cover_url = media[0]['media-metadata'][0]['url'] if media else "frontE/styles/defaultimg.png"
    #     st.sidebar.image(cover_url, width=100)
    #     st.sidebar.write(f"[{title}]({url})")

    #     if st.sidebar.button("Previous Article", key='previous_article'):
    #         st.session_state['article_index'] = (article_index - 1) % len(trending_articles)
    #         st.rerun()
    #     if st.sidebar.button("Next Article", key='next_article'):
    #         st.session_state['article_index'] = (article_index + 1) % len(trending_articles)
    #         st.rerun()
    # else:
    #     st.sidebar.write("No trending articles found.")
    # st.sidebar.markdown("</div>", unsafe_allow_html=True)

    # st.sidebar.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
    # st.sidebar.markdown("<h2>Reading Goal</h2>", unsafe_allow_html=True)
    # if 'reading_goals' in user_data:
        # current_goal = user_data['reading_goals'].get('goal', 'Not set')
        # books_read = user_data.get('already_read', [])
    #     st.sidebar.markdown(f"<p>You have read {len(books_read)} book(s)</p>", unsafe_allow_html=True)
    # else:
    #     current_goal = 'Not set'
    #     books_read = []

    # reading_goal = st.sidebar.radio(
    #     "Set your reading goal:", 
    #     [0, 25, 50, 100, 125, 150], 
    #     index=[0, 25, 50, 100, 125, 150].index(current_goal) if current_goal != 'Not set' else 0,
    #     key='reading_goal'
    # )
    # st.sidebar.markdown(f"<p>Current Reading Goal: {reading_goal} books</p>", unsafe_allow_html=True)
    # st.sidebar.markdown(f"<p>Books Read: {len(books_read)}</p>", unsafe_allow_html=True)
    
    # if st.sidebar.button("Save Goal", key='save_goal'):
    #     update_reading_goal(user_pseudo, reading_goal)
    #     st.rerun()
    # st.sidebar.markdown("</div>", unsafe_allow_html=True)
    ###
    display_sidebar()
    # Main content
    st.markdown("<div class='main-content'>", unsafe_allow_html=True)
    st.markdown("<div class='search-bar'>", unsafe_allow_html=True)
    st.write("What are we reading today?")
    
    search_query = st.text_input("Enter book title to search:")

    if st.button("Search"):
        if search_query:
            books = fetch_book_details(search_query, max_results=30)
            if books:
                st.session_state['searched_books'] = books
            else:
                st.write("No books found for the given title.")
        else:
            st.write("Please enter a search query.")
    if 'searched_books' in st.session_state:
        display_books_grid(st.session_state['searched_books'])

    # search_query = st.text_input("Enter Book Title:")

    # if st.button("Search"):
    #     if search_query:
    #         books = fetch_book_details(search_query)
    #         if books:
    #             st.session_state['searched_books'] = books
    #         else:
    #             st.write("No books found for the given title.")
    # if 'searched_books' in st.session_state:
    #     display_books_grid([st.session_state['searched_books']])

    query_params = st.experimental_get_query_params()
    sub_search_query = query_params.get('search_query', [None])[0]
    if sub_search_query:
        books = fetch_book_details(sub_search_query)
    
    #
    # Initializinf session state for pagination
    if 'page' not in st.session_state:
        st.session_state.page = 1
    SUBJECTS = [
        "art", "biographies", "children", "computers", "education", 
        "fiction", "history", "mathematics", "medicine", "philosophy", 
        "religion", "science", "technology"
    ]
    subject = st.selectbox("Select a subject", options=SUBJECTS, key='subject_multiselect')
    if st.button("Search by Subject", key='search_by_subject'):
        if subject:
            books = fetch_book_subjects(subject, page=st.session_state.page)
            if books:
                st.write(f"Subject: {subject}, Number of books fetched: {len(books)}")
                st.session_state['searched_books_sub'] = books
            else:
                st.write("No books for selected category! Try something else maybe.")
    
    if 'searched_books_sub' in st.session_state:
        display_books_grid_subject(st.session_state['searched_books_sub'])

    # Handle search by title if present in query parameters
    query_params = st.experimental_get_query_params()
    if 'title' in query_params:
        title = query_params['title'][0].replace('%20', ' ')
        st.write(f"Searching for books with title: {title}")
        books_by_title = fetch_book_details(title)
        if books_by_title:
            st.write(f"Found {len(books_by_title)} book(s) matching the title '{title}'")
            display_books_grid(books_by_title)
        else:
            st.write(f"No books found for title '{title}'")


    #####################################################################################
    # if 'searched_books_sub' in st.session_state:
    #     display_books_grid(st.session_state['searched_books'])
    # if st.button("Search by Subject", key='search_by_subject'):
    #     if subject:
    #         books = fetch_book_subjects(subject, limit=40 ,page=st.session_state.page)
    #         if books:
    #             st.write(f"Subject: {subject}, Number of books fetched: {len(books)}")
    #             st.session_state['searched_books_sub'] = books
    #         else:
    #             st.write("No books for selected category! Try something else maybe.")
    
    # if 'searched_books_sub' in st.session_state:
    #     display_books_grid_subject(st.session_state['searched_books_sub'])
    ###################################################################################
                # cols = st.columns(3)
                # for idx, book in enumerate(books):
                #     with cols[idx % 3]:
                #         st.image(book['cover_url'], use_column_width=True)
                #         title = book.get('title', 'N/A')
                #         st.markdown(f"<a href='#' onclick=\"searchBook('{title}')\">**Title: {title}**</a>", unsafe_allow_html=True)
                #         with st.popover(f"Show details for {book.get('title', 'N/A')}"):
                #             st.write(f"**Published Year:** {book.get('first_publish_year', 'N/A')}")
                #             st.write(f"**Publisher:** {', '.join(book.get('publisher', [])) if 'publisher' in book else 'N/A'}")
                #             st.write(f"**ISBN:** {', '.join(book.get('isbn', [])) if 'isbn' in book else 'N/A'}")
                #             st.write(f"**Summary:** {book.get('summary', 'None')}")
                #             st.write(f"**Subjects:** {', '.join(book.get('subject', [])) if 'subject' in book else 'N/A'}")
                #             st.write(f"**Ratings average:** {book.get('ratings_average', 0)}")
                    

                # Add pagination controls
    #             if st.session_state.page > 1:
    #                 st.button("Previous Page", on_click=change_page, args=(st.session_state.page - 1,))
    #             if len(books) == 9:  # Assuming 9 books per page
    #                 st.button("Next Page", on_click=change_page, args=(st.session_state.page + 1,))
    #         else:
    #             st.write("No books found for the selected subject.")
        
    # if st.session_state.title_query:
    #     books = fetch_book_details(st.session_state.title_query)
    #     if books:
    #         display_books_grid(books)
    #     else:
    #         st.write(f"no book found for the book : {st.session_state.title_query}")
        # all_books = []
        # for s in subject:
        #     books = fetch_book_subjects(s, limit=9, page=1)
        #     st.write(f"Subject: {s}, Number of books fetched: {len(books)}")
            
            # all_books.extend(books)

        # if all_books:
        #     for i in range(0, len(all_books), 3):
        #         cols = st.columns(3)
        #         for col, book in zip(cols, all_books[i:i+3]):
        #             col.image(book.get('cover_url', r"frontE\styles\defaultimg.png"), use_column_width=True)
        #             # col.image(f"https://covers.openlibrary.org/b/id/{book.get('cover_i')}-L.jpg" if 'cover_i' in book else r"frontE/styles/defaultimg.png", width=150)
        #             col.write(f"**Title**: {book['title']}")
        #             col.write(f"**Author(s)**: {', '.join(author['name'] for author in book['authors']) if 'authors' in book else 'N/A'}")
        #             with col.popover(f"Show details for {book['title']}"):
        #                 display_book_details(book)
        
    
    # if 'searched_books_sub' in st.session_state:
    #     all_books = st.session_state['searched_books_sub']
    #     display_books_grid_subject(all_books)
    # else:
    #     st.write("Search for books by title or subject to display them here.")
    
    st.markdown("</div>", unsafe_allow_html=True)

def display_books_grid(books):  
    displayed_ids = set()
    cols = st.columns(3)
    idx = 0
    
    for book in books:
        if book['_id'] not in displayed_ids:
            displayed_ids.add(book['_id'])
            print(f"book id : {book['_id']}")
            with cols[idx % 3]:
                st.image(book.get('cover_url', 'styles/defaultimg.png'), use_column_width=True)
                st.write(f"**Title:** {book.get('title', 'N/A')}")
                st.write(f"**Author(s):** {book.get('authors', ['N/A'])}")
                
                # Generate unique keys for each button
                read_button_key = f"read_{book['_id']}"
                wishlist_button_key = f"wishlist_{book['_id']}"

                # if st.button("Mark as Read", key=read_button_key):
                #     add_book_to_read(user_pseud, book['_id'], book)
                
                if st.button(f"Add to Wishlist", key=wishlist_button_key):
                    st.write(f"Clicked Add to Wishlist for book_id: {book['title']}")
                    if add_book_to_wishlist(st.session_state['current_user'], book['_id']):
                        st.success(f"{book.get('title', 'Book')} added to your wishlist")
                    else:
                        st.error("Failed to add the book to your wishlist")
                if st.button(f"add read books", key=read_button_key):
                    st.write(f"Clicked Add to Read for book_id: {book['title']}")
                    if add_book_to_already_read(st.session_state['current_user'], book['_id']):
                        st.success(f"{book.get('title', 'Book')} added to your read books")
                
                # st.write(f"Clicked Add to Wishlist for book_id: {book['_id']}")
                with st.popover(f"book details for {book['title']}"):
                    display_book_details(book)
            
            idx += 1
    


# Function to display book details

def display_book_details(book):
    st.write("## Book Details")

    #authors = book.get('authors', [])
    # if isinstance(authors, list):
    #     try:
    #         author_names = ', '.join([author.get('name', 'Unknown') for author in authors[:3]])
    #     except AttributeError:
    #         author_names = ', '.join(authors[:3]) if authors else 'N/A'
    # elif isinstance(authors, str):
    #     author_names = authors
    # else:
    #     author_names = 'N/A'

    col1, col2 = st.columns(2)
    with col1:
        st.image(book.get('cover_url', r"frontE\styles\defaultimg.png"), use_column_width=True)
    with col2:
        st.write(f"**Title:** {book.get('title', 'N/A')}", unsafe_allow_html=True, on_click=fetch_book_details, args=(book.get('title'),))
        st.write(f"**Author(s):** {book.get('authors', ['N/A'])}")
        st.write(f"**Published Year:** {book.get('published_year', 'N/A')}")
        st.write(f"**Publisher:** {book.get('publisher', ['N/A'])}")  # Take first three publishers
        st.write(f"**ISBN:** {book.get('isbn', 'N/A')}")
        st.write(f"**Summary:** {book.get('summary', 'N/A')}")
        st.write(f"**Subjects:** {book.get('categories', ['N/A'])}")  # Take first three subjects
        st.write(f"**Ratings average** {book.get('ratings_average', 'N/A')}")


def update_page_number(new_page):
    st.session_state.current_page = new_page
#######################################################################
########################################################################
## --------------- BOOKS SUBJECT DISPLAY FUNC
# def display_books_grid_subject(books):
#     books_per_page = 10  # Number of books to display per page
#     total_pages = (len(books) + books_per_page - 1) // books_per_page  # Calculate total number of pages

#     # Allow user to select the page number
#     page_numbers = list(range(1, total_pages + 1))
#     selected_page = st.selectbox('Select page', page_numbers)

#     # Display books for the selected page
#     start_idx = (selected_page - 1) * books_per_page
#     end_idx = start_idx + books_per_page
#     current_books = books[start_idx:end_idx]

#     cols = st.columns(3)
#     for idx,  book in enumerate( current_books):
#         with cols[idx % 3]:
#             # if 'cover_i' in book and book['cover_i']:
#             #     st.image(book['cover_i'], use_column_width=True)
#             # else:
#             #     st.image(r"frontE\styles\defaultimg.png", use_column_width=True)
#             st.image(book['cover_url'], r"frontE\styles\defaultimg.png", use_column_width=True)
#             st.markdown(make_clickable_title(book['title']), unsafe_allow_html=True)
#             authors = ', '.join([author['name'] for author in book['authors'] if 'name' in author])
#             st.write(f"**Author(s):** {authors}")

#     # Navigation buttons
#     col1, col2, col3 = st.columns(3)
#     with col1:
#         if selected_page > 1:
#             if st.button("Previous Page"):
#                 st.session_state.current_page = selected_page - 1
#                 st.experimental_rerun()
#     with col2:
#         st.write(f"Page {selected_page} of {total_pages}")
#     with col3:
#         if selected_page < total_pages:
#             if st.button("Next Page"):
#                 st.session_state.current_page = selected_page + 1
#                 st.experimental_rerun()
###########################################################################################
import streamlit as st

def display_books_grid_subject(books):
    books_per_page = 10  # Number of books to display per page
    total_pages = (len(books) + books_per_page - 1) // books_per_page  # Calculate total number of pages

    # Allow user to select the page number
    page_numbers = list(range(1, total_pages + 1))
    selected_page = st.selectbox('Select page', page_numbers)

    # Display books for the selected page
    start_idx = (selected_page - 1) * books_per_page
    end_idx = start_idx + books_per_page
    current_books = books[start_idx:end_idx]

    cols = st.columns(3)
    for idx, book in enumerate(current_books):
        with cols[idx % 3]:
            st.image(book['cover_url'], use_column_width=True)
            st.markdown(f"[**{book['title']}**](?title={book['title'].replace(' ', '%20')})", unsafe_allow_html=True)
            authors = book.get('authors', ['Unknown Author'])
            st.write(f"**Author(s):** {authors}")

    # Navigation buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if selected_page > 1:
            if st.button("Previous Page"):
                st.session_state.page = selected_page - 1
                st.experimental_rerun()
    with col3:
        if selected_page < total_pages:
            if st.button("Next Page"):
                st.session_state.page = selected_page + 1
                st.experimental_rerun()

    st.write(f"Page {selected_page} of {total_pages}")



##########################
    # cols = st.columns(3)
    # for idx, (col, book) in enumerate(zip(cols * (len(paginated_books) // 3 + 1), paginated_books)):
    #     with col : 
    #         if 'cover_url' in book and book['cover_url']:
    #             st.image(book['cover_url'], use_column_width=True)
    #         else:
    #             st.image(r"frontE\styles\defaultimg.png", use_column_width=True)
    #     col.markdown(make_clickable_title(book['title']), unsafe_allow_html=True)
    #     # col.image(book['cover_url'], use_column_width=True)
    #     # col.write(f"**Title:** {book['title']}")
    #     authors = ', '.join([author['name'] for author in book['authors'] if 'name' in author])
    #     # col.markdown(make_clickable_title(book['title']), unsafe_allow_html=True)
    #     col.write(f"**Author(s):** {authors}")
    #######################################
    # Pagination controls
    # prev_page, next_page = st.columns(2)

    # if prev_page.button("Previous Page"):
    #     change_page(-1)

    # if next_page.button("Next Page"):
    #     change_page(+1)
        # if st.session_state.current_page * books_per_page < len(books):
        #     st.session_state.current_page += 1
            # read_button_key = f"read_{book['_id']}"
            # wishlist_button_key = f"wishlist_{book['_id']}"

            # if col.button("Mark as Read", key=read_button_key):
            #     add_book_to_read_list(user_pseudo_id, book['_id'])
            # if col.button("Add to Wishlist", key=wishlist_button_key):
            #     add_book_to_wishlist(user_pseudo_id, book['_id'])
        # with col.popover(f"Show details for {book.get('title', 'N/A')}"):
        #     display_book_details(book)
                # col.write(f"**Published Year:** {book.get('published_year', 'N/A')}")
                # col.write(f"**Publisher:** {book.get('publisher', 'N/A')}")
                # col.write(f"**ISBN:** {book.get('isbn', 'N/A')}")
                # col.write(f"**Summary:** {book.get('summary', 'N/A')}")
                # col.write(f"**Categories:** {book.get('categories', 'N/A')}")
                # col.write(f"**Cover URL:** {book.get('cover_url', 'N/A')}")




# def display_books_grid(books):
#     displayed_books = set()
#     cols = st.columns(3)
#     for idx, (col, book) in enumerate(zip(cols, books)):
#         with col:
#             book_id = book['_id']
#             if book_id not in displayed_books:
#                 displayed_books.add(book_id)
            # cover_url = book.get('cover_url', r'styles/defaultimg.png')
            # col.image(cover_url, use_column_width=True)
            # col.write(f"**Title:** {book.get('title', 'N/A')}")
            # col.write(f"**Author(s):** {book.get('authors', 'N/A')}")
            # read_button_key = f"read_{book_id}"
            # if col.button("Mark as Read", key=read_button_key):
            #     add_book_to_already_read(st.session_state['current_user'], book_id)
            #     st.write(f"Marked as read: {book_id}")
            # # Add book to wishlist
            # wishlist_button_key = f"wishlist_{book_id}"
            # if col.button(f"Add to Wishlist", key=wishlist_button_key):
            #     st.write(f"Clicked Add to Wishlist for book_id: {book_id}")
            #     if add_book_to_wishlist(st.session_state['current_user'], book_id):
            #         st.success(f"{book.get('title', 'Book')} added to your wishlist")
            #     else:
            #         st.error("Failed to add the book to your wishlist")
            # with st.popover(f"Show details for {book.get('title')}"):
            #     display_book_details(book)
#             idx += 1
#                 st.write(f"**Published Year:** {book.get('published_year', 'N/A')}")
#                 st.write(f"**Publisher:** {book.get('publisher', 'N/A')}")
#                 st.write(f"**ISBN:** {book.get('isbn', 'N/A')}")
#                 st.write(f"**Summary:** {book.get('summary', 'N/A')}")
#                 st.write(f"**Categories:** {book.get('categories', 'N/A')}")
#                 st.write(f"**Cover URL:** {book.get('cover_url', 'N/A')}")
        # col.button(f"Leave a Review for {book.get('title', 'N/A')}", key=f"review_{book['_id']}")
        # col.selectbox(f"Show details for {book.get('title', 'N/A')}", options=["Summary", "ISBN", "Published Year", "Publisher"], key=f"details_{book['_id']}")

        #col.button("Add to Wishlist", key=f"wishlist_{book['_id']}")

# def display_books_grid(books):
#     cols = st.columns(3)
#     for idx, (col, book) in enumerate(zip(cols, books)):
#         with col:
#             book_id = book.get('_id')
#             cover_url = book.get('cover_url', r'styles/defaultimg.png')
#             col.image(cover_url, use_column_width=True)
#             col.write(f"**Title:** {book.get('title', 'N/A')}")
#             col.write(f"**Author(s):** {book.get('authors', 'N/A')}")
#             read_button_key = f"read_{book_id}_{idx}"
#             if col.button("Mark as Read", key=read_button_key):
#                 add_book_to_already_read(st.session_state['current_user'], book_id)
#                 st.write(f"Marked as read: {book_id}_{idx}")
#             # Add book to wishlist
#             wishlist_button_key = f"wishlist_{book_id}_{idx}"
#             if col.button(f"Add to Wishlist", key=wishlist_button_key):
#                 st.write(f"Clicked Add to Wishlist for book_id: {book_id}")
#                 if add_book_to_wishlist(st.session_state['current_uer'], book_id):
#                     st.success(f"{book.get('title', 'Book')} added to your wishlist")
#                 else:
#                     st.error("Failed to add the book to your wishlist")
#             with st.popover(f"Show details for {book.get('title')}"):
#                 st.write(f"**Published Year:** {book.get('published_year', 'N/A')}")
#                 st.write(f"**Publisher:** {book.get('publisher', 'N/A')}")
#                 st.write(f"**ISBN:** {book.get('isbn', 'N/A')}")
#                 st.write(f"**Summary:** {book.get('summary', 'N/A')}")
#                 st.write(f"**Categories:** {book.get('categories', 'N/A')}")
#                 st.write(f"**Cover URL:** {book.get('cover_url', 'N/A')}")
        # col.button(f"Leave a Review for {book.get('title', 'N/A')}", key=f"review_{book['_id']}")
        # col.selectbox(f"Show details for {book.get('title', 'N/A')}", options=["Summary", "ISBN", "Published Year", "Publisher"], key=f"details_{book['_id']}")



# def display_books_grid(books):
#     cols = st.columns(3)
#     for idx, (col, book) in enumerate(zip(cols, books)):
#         with col:
#             st.image(book.get("cover_url", "styles/defaultimg.png"), use_column_width=True)
#             st.write(f"**Title:** {book.get('title', 'N/A')}")
#             st.write(f"**Author(s):** {book.get('authors', 'N/A')}")
#             if st.button("Mark as Read", key=f"read_{book['_id']}"):
#                 st.write(f"Marked {book.get('title')} as read.")
            # # Add book to wishlist
            # wishlist_button_key = f"wishlist_{book['_id']}"
            # if col.button(f"Add to Wishlist", key=wishlist_button_key):
            #     st.write(f"Clicked Add to Wishlist for book_id: {book['_id']}")
            #     if add_book_to_wishlist(user_pseudo=st.session_state['current_uer'], book_id=book['_id']):
            #         st.success(f"{book.get('title', 'Book')} added to your wishlist")
            #     else:
            #         st.error("Failed to add the book to your wishlist")
#             # Popover to display book details
            # with st.popover(f"Show details for {book.get('title')}"):
            #     st.write(f"**Published Year:** {book.get('published_year', 'N/A')}")
            #     st.write(f"**Publisher:** {book.get('publisher', 'N/A')}")
            #     st.write(f"**ISBN:** {book.get('isbn', 'N/A')}")
            #     st.write(f"**Summary:** {book.get('summary', 'N/A')}")
            #     st.write(f"**Categories:** {book.get('categories', 'N/A')}")
            #     st.write(f"**Cover URL:** {book.get('cover_url', 'N/A')}")

# Updated display_books_grid function to handle book details
# def display_books_grid(books):
#     user_pseudo = st.session_state['current_user']
    # # for i in range(0, len(books), 3):
    # #     cols = st.columns(3)
    # #     for idx, (col, book) in enumerate(zip(cols, books[i:i+3])):
    # cols = st.columns(3)
#     for idx, (col, book) in enumerate(zip(cols, books)):
#         with col : 
#             # Ensure the book is stored in the database and has an _id field
#             book_id = check_or_add_book_db(book)
#             if book_id == 'N/A':
#                 st.error("Failed to get or add book to the database")
#                 continue
            
#             cover_url = book.get('cover_url', r"frontE\styles\defaultimg.png")
#             col.image(cover_url, width=150)
#             col.write(f"**Title:** {book.get('title', 'No Title')}")
            
#             authors = book.get('authors', [])
#             if isinstance(authors, list):
#                 try:
#                     author_names = ', '.join([author.get('name', 'Unknown') for author in authors]) if authors else 'N/A'
#                 except AttributeError:
#                     author_names = ', '.join(authors) if authors else 'N/A'
#             elif isinstance(authors, str):
#                 author_names = authors
#             else:
#                 author_names = 'N/A'
            
#             col.write(f"**Author(s):** {author_names}")
            
#             # Add book to already_read collection
#             read_button_key = f"read_{book_id}"  #_{i+idx}
#             if col.button(f"Mark as Read", key=read_button_key):
#                 st.write(f"Clicked Mark as Read for book_id: {book_id}")
#                 if add_book_to_already_read(user_pseudo, book_id):
#                     st.success(f"{book.get('title', 'Book')} added to your read books collection")
#                 else:
#                     st.error("Failed to add the book to your read books collection")

            # # Add book to wishlist
            # wishlist_button_key = f"wishlist_{book_id}"
            # if col.button(f"Add to Wishlist", key=wishlist_button_key):
            #     st.write(f"Clicked Add to Wishlist for book_id: {book_id}")
            #     if add_book_to_wishlist(user_pseudo, book_id):
            #         st.success(f"{book.get('title', 'Book')} added to your wishlist")
            #     else:
            #         st.error("Failed to add the book to your wishlist")

#             # Review book
#             with col.expander(f"Leave a Review for {book['title']}"):
#                 review_form_key = f"review_form_{book_id}"
#                 with st.form(key=review_form_key):
#                     review_text = st.text_area("Review:", key=f"review_text_{book_id}")
#                     rating = st.slider("Rating:", 1, 5, key=f"rating_{book_id}")
#                     submit_button = st.form_submit_button(label="Submit Review")
#                     if submit_button:
#                         st.write(f"Submitting review for book_id: {book_id}")
#                         if add_review_to_book(user_pseudo, book_id, review_text, rating):
#                             st.success("Review submitted successfully")
#                         else:
#                             st.error("Failed to submit review")

#             # Book details expanded with a popover widget
#             with col.popover(f"Show details for {book['title']}"):
#                 display_book_details(book)



