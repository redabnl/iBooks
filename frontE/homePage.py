import streamlit as st
import requests
from pymongo import MongoClient
from bson import ObjectId
from data.models import add_to_favs, get_mongo_client, handle_book_selection,remove_for_favs, is_book_in_favs, add_book_to_user_favs, check_or_add_book_to_db
from datetime import datetime
import time
import requests


# Initialize session state for favorites and search results
if 'favorites' not in st.session_state:
    st.session_state['favorites'] = {}

if 'search_results' not in st.session_state:
    st.session_state['search_results'] = None

#function to perform a search query from the open library APi 
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
    
# Function to display the search result 

                
                

            
# Function to handle the search form 
def search_book_form():
    
    search_query = st.text_input("search for a new book in here !")
    submitt_search = st.button(label="search")
    
    if submitt_search and search_query : 
        search_results = search_openAPI_lib(search_query, limit=3)
        if search_results:
            st.session_state['search_results'] = search_results
            print('new books found for you : \n')
            # show_search_result( st.session_state['current_user'],search_results)
            return search_results
        else :
            print("cannot fetch the result : ")
        
              
            #return search_results
            
            
def display_book_details(book):
    title = book.get('title', 'No Title')
    authors = book.get('author_name', ['Unknown'])
    published_year = book.get('first_publish_year', 'Not Available')
    isbn = book.get('isbn', [])[0] if book.get('isbn', []) else 'N/A'
    cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg" if isbn != 'N/A' else None

    with st.container():
        # Display the cover image if available
        if cover_url:
            st.image(cover_url, caption=title, width=100)
        
        # Display book details
        st.write(f"**Title:** {title}")
        st.write(f"**Author:** {', '.join(authors)}")
        st.write(f"**First Published Year:** {published_year}")
        st.write(f"**ISBN:** {isbn}")
        
        
        
 
def show_search_result(user_pseudo, search_results):
    if search_results and 'docs' in search_results:
        books = search_results['docs']  # Assuming this is a list of book dictionaries

        for index, book in enumerate(books[:3]):  # Limiting to display only the first 3 books
            isbn = book.get('isbn', [])[0] if book.get('isbn', []) else 'N/A'
            unique_key = f"fav_{index}_{isbn}"
            
            # Check if the book is in the database and add if not
            book_in_db = check_or_add_book_to_db(book)
            book_id = book_in_db.get('_id') if book_in_db else None
            
            # Check if the book is already a favorite
            is_favorite = is_book_in_favs(user_pseudo, book_id) if book_id else False

            # Display book details
            display_book_details(book)
            
            # Checkbox to add/remove from favorites
            fav_checked = st.checkbox("❤️ Add to favorites", value=is_favorite, key=unique_key)
            if fav_checked:
                if not is_favorite:
                    # Add to favorites if not already a favorite
                    success = add_book_to_user_favs(user_pseudo, book_id)
                    if success:
                        st.success("Book added to favorites successfully.")
                    else:
                        st.error("Failed to add book to favorites.")
            else:
                if is_favorite:
                    # Remove from favorites if it was a favorite
                    success = remove_for_favs(user_pseudo, book_id)
                    if success:
                        st.success("Book removed from favorites successfully.")
                    else:
                        st.error("Failed to remove book from favorites.")
    else:
        st.error("No valid search results available to display.")

 
 
 
 ###############################################################
 ####################################################################
# def show_search_result(user_pseudo, search_results):
#     # Assuming search_results contains a dictionary with 'docs' being one of the keys
#     if search_results and 'docs' in search_results:
#         books = search_results['docs']  # Directly accessing the list of books
        
#         processed_isbns = set()
#         unique_books = []

#         for book in books:
#             if isinstance(book, dict):  # Make sure each book is a dictionary
#                 isbn_list = book.get('isbn', [])
#                 if isbn_list:
#                     isbn = isbn_list[0]
#                     if isbn not in processed_isbns:
#                         processed_isbns.add(isbn)
#                         unique_books.append(book)
#                 print(f"book's isbn: {isbn}")
                
#                 # Only process up to three unique books
#                 if len(unique_books) == 3:
#                     break

#         for index, book in enumerate(unique_books):
#             isbn = book.get('isbn', [None])[0]
#             unique_key = f"fav_{index}_{isbn}"
#             is_favorite = is_book_in_favs(user_pseudo, isbn)

#             #cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg" if isbn else None
            


#             book_in_db = check_or_add_book_to_db(book)
#             #is_favorite = is_book_in_favs(user_pseudo, book_in_db['_id'])

#             with st.container():
#                 fav_checked = st.checkbox("❤️ Add to favorites", value=is_favorite, key=unique_key)
#                 if fav_checked:
#                     if not is_favorite:
#                         add_book_to_user_favs(user_pseudo, book_in_db['_id'])

#                 display_book_details(book)  
#             # with st.container():
#             #     if cover_url:
#             #         st.image(cover_url, caption=book.get('title'), width=100)
#             #     st.write(f"Title: {book.get('title', 'No Title')}")
#             #     st.write(f"Author: {', '.join(book.get('author_name', ['Unknown']))}")
#             #     st.write(f"First Published Year: {book.get('first_publish_year', 'Not Available')}")

#             #     fav_checked = st.checkbox("❤️ Add to favorites", value=is_favorite, key=unique_key)
#             #     if fav_checked and not is_favorite:
#             #         handle_book_selection(user_pseudo, search_results)
#             #         st.rerun()
#             #     elif not fav_checked and is_favorite:
#             #         remove_for_favs(user_pseudo, isbn)
#             #         st.rerun()
#                     # #add the book to the favorites collection with book details (title, author, isbn, coverURL...)
#                     # book_details = {
#                     #     'title': book.get('title'),
#                     #     'author': ', '.join(book.get('author_name', ['Unknown'])),
#                     #     'isbn': isbn,
#                     #     'published_year': book.get('first_publish_year'),
#                     #     'cover_url': cover_url
#                     # }
#                     # # Add the book to the favorites if it's not already there
#                     # added_successfully = add_to_favs(st.session_state['current_user'], book_details)
#                     # if added_successfully:
#                     #     st.success("Book added to favorites!")
#                     # else:
#                     #     st.error("Failed to add book to favorites.")
                    
                    
#                 st.session_state['favorites'][unique_key] = fav_checked

#     else:
#         st.error("No valid search results available to display.")


#library function where user's favbooks gonna be displayed
# This function should be in your homePage.py file
def show_library(user_pseudo):
    with get_mongo_client() as client:
        db = client['ibooks']
        users_collection = db['users']
        books_collection = db['books']

        user_doc = users_collection.find_one({'pseudo': user_pseudo})
        fav_books_ids = user_doc.get('favBooks', [])

        # Fetch the books' details using their ObjectIds
        fav_books = books_collection.find({'_id': {'$in': fav_books_ids}}) if fav_books_ids else []

        for book in fav_books:
            st.subheader(book.get('title', 'No Title'))
            st.write('Author:', ', '.join(book.get('authors', ['Unknown'])))
            
            published_date = book.get('published_date')
            if isinstance(published_date, datetime):
                published_year = published_date.year
            else:
                published_year = 'Unknown'
            # st.write('Published Year:', book.get('published_date', 'Unknown').year)
            st.write('Published year : ', published_year)
            st.write('Summary:', book.get('summary', 'No Summary'))
            st.write("-----------")
        if not fav_books:
            st.write('No favorites boooks added yet. Here is some you can like : ')
            
            

# Function to display the homepage
def show_user_homepage(pseudo):
    pseudo = st.session_state['current_user']
    if pseudo:
        
        # Header
        st.header(f"{pseudo}'s Home page")
        # st.image('path_to_your_banner_image.jpg', use_column_width=True)  # Replace with your image path

        # Navigation bar (for simplicity, these could just be buttons or links)
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            if st.button('Library'):
                # Logic for showing the Library
                show_library(user_pseudo=st.session_state['current_user'])
                pass
        with col2:
            if st.button('Wish List'):
                # Logic for showing the Wish List
                pass
        with col3:
            if st.button('Swap List'):
                # Logic for showing the Swap List
                pass
        with col4:
            if st.button('Friends List'):
                # Logic for showing the Friends List
                pass
        with col5:
            if st.button('Logout'):
                # Logic for logging out
                pass

        search_book_form()
        
        if st.session_state['search_results']:
            show_search_result(pseudo, st.session_state['search_results'])


        # You may also add more sections to display content based on the search or user profile
        st.write("Content based on user profile or search results will appear here.")
        
    else :
        st.error("Pseudo not found please try again")

# Main function to control the page layout
def main():
    # Check login state
    if st.session_state.get('logged_in', False):
        show_user_homepage(pseudo=st.session_state['current_user'])  # Show the homepage if the user is logged in
    else:
        st.write("Please log in.")  # Or direct them to the login page

if __name__ == "__main__":
    main()
