from flask import app, redirect
import streamlit as st
import requests
from data.models import  get_mongo_client, is_book_in_favs, check_or_add_book_to_db
from data.models import add_review_to_book, submit_review, toggle_favorite
from machineL import recommend_books, load_and_prepare_data
from datetime import datetime
import time
import requests


# Initialize session state for favorites and search results
if 'favorites' not in st.session_state:
    st.session_state['favorites'] = {}


if 'search_results' not in st.session_state:
    st.session_state['search_results'] = None
    

if 'current_book' not in st.session_state:
    st.session_state['current_book'] = None



#function to perform a search query from the open library APi 
def search_openAPI_lib(search, limit=9, page=1):
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
    

def redirect_to_cheaper99(isbn):
    return redirect(f"https://cheaper99.com/{isbn}")


                
                

            
# Function to handle the search form 
def search_book_form(search_query):
    
    search_query = st.text_input("what book we reading today !")
    submitt_search = st.button(label="search")
    
    if submitt_search and search_query : 
        search_results = search_openAPI_lib(search_query, limit=9, page=1)
        if search_results:
            st.session_state['search_results'] = search_results
            print(f'new books found for you : \n ')
            show_search_result( st.session_state['current_user'],search_results)
            return search_results
        else :
            print("cannot fetch the result : ")
        
        

# displaying the books as cards with a link to an axternal website
def generate_card(title,authors ,description ):
    """Generate HTML content for a single book card."""
    card_html = f"""
    <div style="margin: 10px; float: left; width: 300px; border: 1px solid #ccc; border-radius: 5px; padding: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <h3>{title}</h3>
        <h4>{authors}</h4>   
        <p>{description}</p>
    </div>
    """
    return card_html

def show_books_as_cards(books_df):
    # Start of the HTML block for cards
    st.write("<div style='display: flex; flex-wrap: wrap;'>", unsafe_allow_html=True)
    
    # Generate a card for each book
    for _, row in books_df.iterrows():
        # Assuming you have columns titled 'Title', 'Author', and 'Description' in your DataFrame
        card_html = generate_card(
            title=row['Title'],
            authors=row['Authors'],
            description=row['Description'][:150] + "..."  # Limit description characters
        )
        st.markdown(card_html, unsafe_allow_html=True)
    
    # Close the HTML block
    st.write("</div>", unsafe_allow_html=True)
              
            
            
                        
def display_book_details(books):
    if isinstance(books, dict):
        # Assuming 'books' is a dictionary containing book details
        title = books.get('title', 'No Title')
        authors = books.get('author_name', ['Unknown'])
        published_year = books.get('first_publish_year', 'Not Available')
        isbn = books.get('isbn', [''])[0] if books.get('isbn', []) else 'N/A'
        cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg" if isbn != 'N/A' else None

        # Display details
        if cover_url:
            st.image(cover_url, caption=title, width=100)
        if isbn != 'N/A':
            url = f"https://cheaper99.com/{isbn}"
            title_link = f"<a href='{url}' target='_blank'>{title}</a>"
            st.markdown(title_link, unsafe_allow_html=True)
        else:
            st.write(f"**Title:** {title} ")
        st.write(f"**Author:** {', '.join(authors)}")
        st.write(f"**First Published Year:** {published_year}")
        st.write(f"**ISBN:** {isbn}")
        
        
    else:
        st.error("Data format not recognized, expected a dictionary.")
        
        
        

def review_form(user_pseudo, book_id):
    with st.form(key='review_form'):
        review_text = st.text_area("Review Text", placeholder="Enter your review here...")
        rating = st.slider("Rating", min_value=1, max_value=5, value=3)
        submit_button = st.form_submit_button("Submit Review")
        
        if submit_button:
            success = submit_review(user_pseudo, book_id, review_text, rating)
            if success:
                st.success("thanks for leaving a review !")
                return user_pseudo, book_id, review_text, rating
            else:
                st.error("failed to add your review")
        
 
 
def show_search_result(user_pseudo, search_results):
    if search_results and 'docs' in search_results:
        books = search_results['docs']  
        
        for index, book in enumerate(books[:9]):  # Limiting to display only the first 9 books
            isbn = book.get('isbn', [])[0] if book.get('isbn', []) else 'N/A'
            unique_key = f"fav_{index}_{isbn}"
            
            # Check if the book is in the database and add if not
            book_in_db = check_or_add_book_to_db(book)
            book_id = book_in_db.get('_id') if book_in_db else None
            cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg" if isbn else None
            
            book_details = {
                        'title': book.get('title'),
                        'author': ', '.join(book.get('author_name')),
                        'isbn': isbn,
                        'published_year': book.get('first_publish_year'),
                        'cover_url': cover_url,
                        'reviews' : []
                    }
            print(f"book found : \n {book_details} \n ")
            # Check if the book is already a favorite
            is_favorite = is_book_in_favs(user_pseudo, book_id) if book_id else False


            print(f"book type : \n {type(book)} \n ")
            # print(f"book from open Lib : \n {book}")
            # Display book details
            display_book_details(book)
            # print(f"book : {book_details}")
            
            if 'favorites' not in st.session_state:
                st.session_state['favorites'] = []

            fav_checked = st.checkbox("❤️ Add to favorites", value=isbn in st.session_state['favorites'], key=unique_key)
            if fav_checked:
                toggle_favorite(isbn, add=True)
            else:
                toggle_favorite(isbn, add=False)

            if book_id:
                with st.expander("Leave a Review"):
                    with st.form(key=f'review_form_{index}'):
                        review_text = st.text_area("Review Text", placeholder="Enter your review here...")
                        rating = st.slider("Rating", min_value=1, max_value=5, value=3)
                        submit_button = st.form_submit_button("Submit Review")

                        if submit_button:
                            add_review_to_book(user_pseudo, book_id, review_text, rating)
                            success = submit_review(user_pseudo, book_id, review_text, rating)
                            if success:
                                st.success("Your review has been added!")
                            else:
                                st.error("Failed to add your review.")
                

        return search_results
    else:
        st.error("No valid search results available to display.")


# Function to display the homepage
def show_user_homepage(user):
    st.header(f"{user}'s Home Page")
    st.write(f"Hi {user}, welcome to your home page.")
    
    
    search_book_form(search_query = st.text_input("Search for a new book here!"))
       



# def main():
#     # Check login state
#     if st.session_state.get('logged_in', False):
#         show_user_homepage(pseudo=st.session_state['current_user'])  # Show the homepage if the user is logged in
#     else:
#         st.write("Please log in.")  # Or redirect them to the login page

# if __name__ == "__main__":
#     main()











