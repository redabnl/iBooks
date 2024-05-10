import streamlit as st
import requests
from pymongo import MongoClient
from bson import ObjectId
from data.models import add_to_favs, get_mongo_client, handle_book_selection,remove_for_favs, is_book_in_favs, add_book_to_user_favs, check_or_add_book_to_db, add_review_to_book
from data.models import add_review_to_book
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


# Function to display the search results

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
    


                
                

            
# Function to handle the search form 
def search_book_form(search_query):
    
    search_query = st.text_input("search for a new book in here !")
    submitt_search = st.button(label="search")
    
    if submitt_search and search_query : 
        search_results = search_openAPI_lib(search_query, limit=9)
        if search_results:
            st.session_state['search_results'] = search_results
            print(f'new books found for you : \n ')
            show_search_result( st.session_state['current_user'],search_results)
            return search_results
        else :
            print("cannot fetch the result : ")
        
              
            
            
                        
def display_book_details(book):
    with st.container():
        # display_book_cards(book)
        
        title = book.get('title', 'No Title')
        authors = book.get('author_name', ['Unknown'])
        published_year = book.get('first_publish_year', 'Not Available')
        isbn = book.get('isbn', [])[0] if book.get('isbn', []) else 'N/A'
        cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg" if isbn != 'N/A' else None
        

            # Display the cover image if available
        if cover_url:
            st.image(cover_url, caption=title, width=100)
            
            # Display book details
            st.write(f"**Title:** {title}")
            st.write(f"**Author:** {', '.join(authors)}")
            st.write(f"**First Published Year:** {published_year}")
            st.write(f"**ISBN:** {isbn}")
        
        
        
        
        
        
# def display_book_cards(books):
#     cols = st.columns(3)
#     for index, book in enumerate(books.itertuples(), start=1):
#         with cols[(index-1) % 3]:
#             # st.image(book.cover_url, width=100)
#             st.write(book.title)
#             st.write(f"By {book.author}")

# def display_review_form(book_id):
#     with st.form(key=f"form_review_{book_id}"):  # Unique key for each form based on book_id
#         st.subheader("Leave a review")
#         review_text = st.text_area("Your Review", help="Write your review here.")
#         rating = st.text_input("your rating ")
#         submit_review = st.form_submit_button("Submit Review")

#     if submit_review :
#         add_review_to_book(st.session_state['current_user'], book_id, review_text, rating)
#         st.success("Your review has been added!")
#     else:
#             st.error("Failed to add your review.")
        

# def submit_review_form(user_pseudo, book_id, review_text, rating):
#     with st.form("book_review"):
#         review_text = st.text_area("leave a review")
#         rating = st.text_input("your rating ")
#         submit_review = st.form_submit_button("Submit Review")
        
#         if submit_review:
#             user_pseudo = st.session_state['current_user']
#             book_id = st.session['current_book']
#             save_review(user_pseudo, book_id, review_text, rating)
        
        
# def save_review(user_pseudo, book_id, review_text, rating):
#     client = get_mongo_client()
#     db = client['ibooks']
    
#     review_doc = {
#         "user_pseudo" : user_pseudo,
#         "book_id": book_id,
#         "rating" : rating,  
#         "text" :review_text,
#         "date" : datetime.now()
#         }
    
#     review_id = db.reviews.insert_one(review_doc).inserted_id
    
#     db.users.update_one(
#         {"pseudo" : user_pseudo},
#         {"$push":{"user_reviews" : review_id}}
        
        
#     )
#     st.success("review suvmitted succesfully !")


def submit_review(user_pseudo, book_id, review_text, rating):
    client = get_mongo_client()
    try :
        db = client['ibooks']
        review_doc = {
            "user_pseudo" : user_pseudo,
            "book_id": book_id,
            "rating" : rating,  
            "text" :review_text,
            "date" : datetime.now()
        }
        
        review_id = db.reviews.insert_one(review_doc).inserted_id
        #updating the user collection with the review left
        db.users.update_one(
            {"pseudo" : user_pseudo},
            {"$push":{"user_reviews" : review_id}}
        )
        #updating thebooks collection with the review left
        db.books.update_one(
            {"_id": book_id},
            {"$push": {"reviews": review_id}}
        )
        return True
    except Exception as e:
        print(f"mission failed vause of : \n {e}")
        return False
    
        
    

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
        
        for index, book in enumerate(books[:3]):  # Limiting to display only the first 3 books
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
            print(f"book found : \n {book_details}")
            # Check if the book is already a favorite
            is_favorite = is_book_in_favs(user_pseudo, book_id) if book_id else False

            # Display book details
            display_book_details(book)
            print(f"book : {book_details}")
            
            
            # Checkbox to add/remove from favorites
            fav_checked = st.checkbox("❤️ Add to favorites", value=is_favorite, key=unique_key)
            if fav_checked:
                if not is_favorite:
                    # Add to favorites if not already a favorite
                    success = add_to_favs(user_pseudo, book_details)
                    if success:
                        try :
                            st.success("Book added to favorites successfully.")
                            print(f"book added : {book_details}")
                        except :
                            print(f"error adding the book {NameError}")
                    else:
                        st.error("Failed to add book to favorites.")
                        print(f"error adding the book ")
            else:
                if is_favorite:
                    # Remove from favorites if it was a favorite
                    success = remove_for_favs(user_pseudo, book_id)
                    if success:
                        st.success("Book removed from favorites successfully.")
                    else:
                        st.error("Failed to remove book from favorites.")
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
    search_query = st.text_input("Search for a new book here!")
    if st.button('Search'):
        # Assume search_books returns DataFrame of books
        results = search_book_form(search_query)
        if results:
            show_search_result(user_pseudo=st.session_state['current_user'], search_results=results)
        else:
            st.write("No books found.")
       

# <img src="{image_url}" alt="Book Cover" style="width:100%; height: 150px; border-radius: 5px;">   image_url="https://via.placeholder.com/150"

    
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





def show_explorer_page():
    
    data, tfidf_matrix, tfidf_vectorizer = load_and_prepare_data('data/dataSetCleaned.csv')

    st.write("Welcome to the explorer page.")
    user_description = st.text_input("Describe the book you're interested in:", '')

    if st.button("Find Books", key='explorer_search_btn'):
        recommended_books = recommend_books(user_description, data, tfidf_vectorizer, tfidf_matrix)
        if recommended_books.empty:
            st.error("No books found. Please try again.")
        else:
            print(recommended_books.columns)
            show_books_as_cards(recommended_books)



def main():
    # Check login state
    if st.session_state.get('logged_in', False):
        show_user_homepage(pseudo=st.session_state['current_user'])  # Show the homepage if the user is logged in
    else:
        st.write("Please log in.")  # Or redirect them to the login page

if __name__ == "__main__":
    main()











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