import streamlit as st
from pymongo import MongoClient
import os
import requests

# Function to get MongoDB client
def get_mongo_client():
    return MongoClient(os.getenv("MONGO_DB_URI"))

# Function to check if a book is in the user's favorites
def is_book_in_favs(user_pseudo, book_id):
    st.write(f"Checking if book {book_id} is in favorites for user {user_pseudo}")
    with get_mongo_client() as client:
        db = client['ibooks']
        users_collection = db['users']
        
        user = users_collection.find_one({'pseudo': user_pseudo})
        if user:
            fav_books_ids = user.get('favBooks', [])
            st.write(f"Favorite books IDs: {fav_books_ids}")
            if book_id in fav_books_ids:
                st.write(f"Book {book_id} is in favorites")
                return True
            else:
                st.write(f"Book {book_id} is not in favorites")
        else:
            st.write(f"User {user_pseudo} not found")
        
        return False
    
def search_openAPI_lib(search, limit=3, page=1):
    search_url = f"https://openlibrary.org/search.json?q={search}&limit={limit}&page={page}"
    try:
        response = requests.get(search_url)
        if response.ok:
            results = response.json()
            books = results.get('docs', [])
            
            unique_books = []
            seen_isbns = set()
            for book in books:
                isbn_list = book.get('isbn', [])
                if isbn_list:
                    isbn = isbn_list[0]
                    if isbn not in seen_isbns:
                        seen_isbns.add(isbn)
                        unique_books.append(book)
                if len(unique_books) >= limit:
                    break
            
            return {'docs': unique_books}
        else:
            st.error('Failed to retrieve data from Open Library')
            return None
    except requests.RequestException as e:
        st.error(f"An error occurred while fetching data: {e}")
        return None

# Function to add a book to the user's favorites
def add_book_to_favorites(user_pseudo, book_id):
    st.write(f"Adding book {book_id} to favorites for user {user_pseudo}")
    with get_mongo_client() as client:
        db = client['ibooks']
        users_collection = db['users']
        
        user = users_collection.find_one({'pseudo': user_pseudo})
        if user:
            fav_books_ids = user.get('favBooks', [])
            if book_id not in fav_books_ids:
                fav_books_ids.append(book_id)
                users_collection.update_one({'pseudo': user_pseudo}, {'$set': {'favBooks': fav_books_ids}})
                st.write(f"Book {book_id} has been added to favorites")
                return True
            else:
                st.write(f"Book {book_id} is already in favorites")
        else:
            st.write(f"User {user_pseudo} not found")
    
    st.write(f"Failed to add book {book_id} to favorites")
    return False

# Example function to show search results and handle favorites
def show_search_results(user_pseudo, book):
    # client = get_mongo_client()
    # db = client['ibooks']
    # book_collection = db['books']
    # user_collection = db['users']
    
    
    cover_url = book.get("cover_url", "")
    title = book.get("title", "Unknown Title")
    author = book.get("author", "Unknown Author")
    first_published_year = book.get("first_published_year", "Unknown Year")
    isbn = book.get("isbn", "Unknown ISBN")
    book_id = book.get("id")  # Assuming 'id' is the unique identifier

    if cover_url:
        st.image(cover_url, caption=title, use_column_width=True)
    
    st.write(f"**Title:** {title}")
    st.write(f"**Author:** {author}")
    st.write(f"**First Published Year:** {first_published_year}")
    st.write(f"**ISBN:** {isbn}")

    is_fav = is_book_in_favs(user_pseudo, book_id)
    st.write(f"is_fav: {is_fav}")
    
    add_fav = st.checkbox("Add this book to your favorites", value=is_fav)
    st.write(f"Checkbox state: {add_fav}")
    
    if add_fav:
        if is_fav:
            st.write(f"Book with ID {book_id} is already in your favorites.")
        else:
            st.write(f"Attempting to add book {book_id} to favorites")
            if add_book_to_favorites(user_pseudo, book_id):
                st.write(f"Book with ID {book_id} has been added to your favorites.")
            else:
                st.write("Failed to add the book to your favorites.")
    else:
        st.write("Check the box to add this book to your favorites.")

# Example Streamlit page layout
def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Navigate to:", ["Home", "Library", "Explorer"])

    if page == "Home":
        st.title("Home Page")
        st.write("Search for a new book here!")
        
        search_query = st.text_input("Enter book name or author:")
        if st.button(label='search') and search_query : 
            search_results = search_openAPI_lib(search_query, limit=3, page=1)
            if search_results:
                # st.session_state['search_results'] = search_results
                print(f'new books found for you : \n ')
                
                return search_results
            else :
                print("cannot fetch the result : ")
            
            for book in search_results:
                
            # Dummy book result for demonstration
                book = {
                    'title' : book.get('Title')
                    
                    # "_id": "662aacb2d290c293abf7f519"  # This should be the unique ID from your database
                }
            user_pseudo = "poutit"  # Replace with the actual user pseudo
            show_search_results(user_pseudo, book)

    elif page == "Library":
        st.title("Library")
        st.write("Your favorite books will be listed here.")

    elif page == "Explorer":
        st.title("Explorer")
        st.write("Explore new books and authors.")

if __name__ == "__main__":
    main()