from flask import redirect
import streamlit as st
from data.book_model import  get_mongo_client, check_or_add_book_db, is_book_in_AR, add_book_to_already_read, add_review_to_book
from frontE.explorer import show_explorer_page
from bson.objectid import ObjectId

from PIL import Image
from io import BytesIO
import requests
import os

# client = get_mongo_client()
# db = client['ibooks']
# book_collection = db['books']
# users_collection = db['users']

# Initialize session state for favorites and search results

# if 'favorites' not in st.session_state:
#     st.session_state['favorites'] = []

# if 'search_results' not in st.session_state:
#     st.session_state['search_results'] = None
    

# if 'current_book' not in st.session_state:
#     st.session_state['current_book'] = None
    
# if 'current_user' not in st.session_state:
#     st.session_state['current_user'] = None
    
# if 'button_clicked' not in st.session_state:
#     st.session_state['button_clicked'] = {}



def show_user_homepage():
    user_pseudo = st.session_state['current_user']
    # explorer_page_link =st.page_link(show_explorer_page)
    st.header(f"{user_pseudo}'s Home Page")
    st.write(f"Hi {user_pseudo}, welcome to your home page.")
    
    search_query = st.text_input("What book are we reading today!", "")
    search_button = st.button("Search")
    if search_button and search_query:
         # Fetch book details from Open Library API
            search_results = fetch_book_details(search_query, limit=9, page=1)
            if search_results :
                st.session_state['search_results'] = search_results
                show_search_result(search_results)
                # display_book_details(book)
            
            else:
                st.error("Cannot fetch the result.")  
    elif st.session_state['search_results']:
        show_search_result(st.session_state['search_results'])    
    # else:
    #     st.write("Looking for a specific book ? ")
    #     st.write("If you don't have anything on your mind rn, Our trained model can help you find what you might be interested with :")
    #     if st.button("explore new books :"):
        
    #         show_explorer_page()
        
        


##########################################################
## OPEN LIBRARY SEARCH API FUNCTION
def fetch_book_details(search_query, limit=9, page=1):
    search_url = f"https://openlibrary.org/search.json?q={search_query}&limit={limit}&page={page}"
    try:
        response = requests.get(search_url)
        data = response.json()
        books = data['docs']
        filtered_books = []

        for book in books:
            if 'ratings_average' in book and 'ratings_count' in book:
                filtered_books.append(book)

        # Sort books by ratings_average in descending order
        sorted_books = sorted(filtered_books, key=lambda x: x['ratings_average'], reverse=True)

        return sorted_books
    except Exception as e:
        print(f"An error occurred while fetching data: {e}")
        return []



## FILTER THE BOOKS FETCHED FROM THE OPEN LIBRAY API
def filter_books(search_results):
    filtered_books = []
    for book in search_results:
        try:
            ratings_average = book.get('ratings_average', 0)
            ratings_count = book.get('ratings_count', 0)
            if ratings_average > 0 and ratings_count > 0:
                filtered_books.append(book)
        except KeyError:
            continue
    # Sort books  in descending order
    filtered_books.sort(key=lambda x: x.get('ratings_count', 0), reverse=True)
    return filtered_books


def show_search_result(search_result):
    filtered_books = filter_books(search_result)
    if not filtered_books:
        st.error(f"cannot fetch the books ")
        return
    st.write(f"we have found {len(filtered_books)} book for you !")
    for book in filtered_books :
        display_book_details(book)    
        
        

    
    
    
def display_book_details(book):
    # Check or add book to database
    book_id = check_or_add_book_db(book)
    title = book.get('title', 'No Title Available')
    author = ' '.join(book.get('authors', ['Unknown Author']))
    published_year = book.get('first_publish_year', 'Unknown')
    isbn_list = book.get('isbn', [])
    isbn = isbn_list[0] if isbn_list else 'N/A'
    cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg" if isbn != 'N/A' else None
    ratings_average = book.get('ratings_average', 0)
    ratings_count = book.get('ratings_count', 0)
    already_read_count = book.get('already_read_count',0)
    user_pseudo = st.session_state.get('current_user', 'guest')

    # Check if cover URL is valid
    def is_valid_url(url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                return True
        except Exception as e :
            print(f"URL error {e}")
            return False
        return False

    if cover_url and is_valid_url(cover_url):
        st.image(cover_url, width=100)
    else:
        st.image('images/default_book_cover.png', width=100)

    st.write(f"**Title:** {title}")
    st.write(f"**Author:** {author}")
    st.write(f"**Published Year:** {published_year}")
    st.write(f"**ISBN:** {isbn}")
    st.write(f"**Average rating :** {ratings_average}")
    st.write(f"**Ratings count :** {ratings_count}")
    st.write(f"**Read by :** {already_read_count} for now ")
    

    if isbn != 'N/A':
        purchase_url = f"https://cheaper99.com/{isbn}"
        link_html = f'<a href="{purchase_url}" target="_blank">Buy this book</a>'
        st.markdown(link_html, unsafe_allow_html=True)
    else:
        st.write("No purchase link available.")

    if book_id:
        st.write(f"**ID:** {book_id}")
    else:
        st.write("No ID found")
        
    book_check = is_book_in_AR(user_pseudo, book_id)
    if book_check : 
        st.write("this book is already in your favs")
        with st.form(key=f'review_form_{book_id}'):
            review_text = st.text_area("Leave a review:")
            rating = st.slider("Rate the book:", 1, 5, 3)
            submit_button = st.form_submit_button("Submit Review")
            if submit_button:
                if add_review_to_book(book_id, user_pseudo, review_text, rating):
                    st.success("Review submitted successfully!")
    else :
        fav_check_key = f"alreadu_read_{book_id}"
        book_coll_check = st.button('add to your read books collection', key=fav_check_key ) # , on_click=add_book_to_already_read, args=(user_pseudo, book_id)
        if book_coll_check :
            add_book_to_already_read(user_pseudo, book_id) 
            st.session_state['already_read'].append(book_id)
            st.session_state['button_clicked'][book_id] = True  
            st.success(f"Added {title} to 'Already Read'")
            
            # Display form for review and rating
            with st.form(key=f'review_form_{book_id}'):
                review_text = st.text_area("Leave a review:")
                rating = st.slider("Rate the book:", 1, 5, 3)
                submit_button = st.form_submit_button("Submit Review")
                if submit_button:
                    if add_review_to_book(book_id, user_pseudo, review_text, rating):
                        st.success("Review submitted successfully!")
        
    
    # if st.checkbox(f"Add to 'Already Read'", key=f'already_read_{book_id}'):
    #     if is_book_in_AR(user_pseudo, book_id) :
    #         with st.form(key=f'review_form_{book_id}'):
    #             review_text = st.text_area("Leave a review:")
    #             rating = st.slider("Rate the book:", 1, 5, 3)
    #             submit_button = st.form_submit_button("Submit Review")
    #             if submit_button:
    #                 if add_review_to_book(book_id, user_pseudo, review_text, rating):
    #                     st.success("Review submitted successfully!")
    #     else :
    #         add_book_to_already_read(user_pseudo, book_id)
    #         st.success(f"Added {title} to 'Already Read'")
    #         with st.form(key=f'review_form_{book_id}'):
    #             review_text = st.text_area("Leave a review:")
    #             rating = st.slider("Rate the book:", 1, 5, 3)
    #             submit_button = st.form_submit_button("Submit Review")
    #             if submit_button:
    #                 if add_review_to_book(book_id, user_pseudo, review_text, rating):
    #                     st.session_state['already_read'].append(book_id)
    #                     st.session_state['button_clicked'][book_id] = True
    #                     st.success("Review submitted successfully!")
    # user_pseudo = st.session_state['current_user']
    # # st.write(f"We have found {len(search_results)} books for you!")
    # if search_results and 'docs' in search_results :
    #     books = search_results['docs']
        
    # for book in books:
        
    #     book_id = check_or_add_book_db(book)
    #     title = book.get('title', 'No Title Available')
    #     author = book.get('author_name', [])
    #     published_year = book.get('first_publish_year', 'Unknown')
    #     isbn_list = book.get('isbn', [])
    #     isbn = isbn_list[0] if isbn_list else 'N/A'
    #     cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg" if isbn != 'N/A' else None
        # ratings_average = book.get('ratings_average', 0)
        # ratings_count = book.get('ratings_count', 0)
        # already_read_count = book.get('already_read_count',0)
        
    #     ## checking if the book is added to the user's collection
        
        
    #     if book_id == 'N/A':
    #         print(f"error getting book ID {SyntaxError}")
    #     elif book_id != 'N/A' :
        
    #         col1, col2 = st.columns([1, 2])
    #         with col1:
    #             if cover_url:
    #                 st.image(cover_url, width=150)
    #             else:
    #                 st.write("No image found")
    #         with col2:
    #             if book_id:
    #                 st.markdown(f"**ID:** {book_id}")
    #             else:
    #                 st.markdown("**ID:** No ID found")
    #             st.markdown(f"**Title:** {title}")
    #             st.markdown(f"**Author:** {author}")
    #             st.markdown(f"**Published Year:** {published_year}")
    #             st.markdown(f"**ISBN:** {isbn}")
    #             if isbn != 'N/A':
    #                 purchase_url = f"https://cheaper99.com/{isbn}"
    #                 link_html = f'<a href="{purchase_url}" target="_blank">Buy this book</a>'
    #                 st.markdown(link_html, unsafe_allow_html=True)
    #             else:
    #                 st.warning("No purchase link available.")

    #             st.markdown(f"**AVG RATING:** {ratings_average} \n (Based on {ratings_count} user's ratings)")
    #             st.markdown(f"**Read by:** {already_read_count} users.")
    #             st.markdown("Did you read it already too?")
                
                
                # book_check = is_book_in_AR(user_pseudo, book_id)
        
                # if book_check :
                    # st.write("this book is already in your favs")
                    # with st.form(key=f'review_form_{book_id}'):
                    #     review_text = st.text_area("Leave a review:")
                    #     rating = st.slider("Rate the book:", 1, 5, 3)
                    #     submit_button = st.form_submit_button("Submit Review")
                    #     if submit_button:
                    #         if add_review_to_book(book_id, user_pseudo, review_text, rating):
                    #             st.success("Review submitted successfully!")
                # else :
                #     button_key = f"already_read_{book_id}"
                    # book_collection_btn = st.button('add to your read books collection', key=button_key ) # , on_click=add_book_to_already_read, args=(user_pseudo, book_id)
                    # if book_collection_btn :
                    #     add_book_to_already_read(user_pseudo, book_id) 
                    #     st.session_state['already_read'].append(book_id)
                    #     st.session_state['button_clicked'][book_id] = True  
                    #     st.success(f"Added {title} to 'Already Read'")
                        
                    #     # Display form for review and rating
                    #     with st.form(key=f'review_form_{book_id}'):
                    #         review_text = st.text_area("Leave a review:")
                    #         rating = st.slider("Rate the book:", 1, 5, 3)
                    #         submit_button = st.form_submit_button("Submit Review")
                    #         if submit_button:
                    #             if add_review_to_book(book_id, user_pseudo, review_text, rating):
                    #                 st.success("Review submitted successfully!")
                
                    
                    
                    





            
                # add_book_to_already_read(user_pseudo, book_id)
                # 
        #st.write("**********************************************************")
            # if cover_url:
            #     st.image(cover_url, width=150)
            # else:
            #     st.write("No image found")
            # st.write(f"**Title:** {book.get('title', 'No Title Available')}")
            # st.write(f"**Author:** {', '.join(book.get('authors', ['Unknown Author']))}")
            # st.write(f"**Published Year:** {book.get('first_publish_year', 'Unknown Year')}")
            # st.write(f"[Buy this book](https://cheaper99.com/{isbn})" if isbn != 'N/A' else "No purchase link available.")
            
                # Additional fields and checks
            
                
                
                # if st.checkbox(f"Add to 'Already Read'", key=f'already_read_{book_id}'):
                #     user_pseudo = st.session_state['current_user']
                #     add_book_to_already_read(user_pseudo, book_id)
                #     st.success(f"Added {book.get('title', 'this book')} to 'Already Read'")
    # if search_results and 'docs' in search_results:
    #     books = search_results['docs']
    #     for book in books:
    #         print(f" ********************** \n fetching book {book}")
    #         display_book_details(book)
    
    # elif not search_results:
    #     st.write("No results found.")
    #     return

        
        
# def display_book_details(book):
#     book_id = book.get('_id', 'N/A')
    
    
    # title = book.get('title', 'No Title Available')
    # author = book.get('author_name', [])
    # published_year = book.get('first_publish_year', 'Unknown')
#     isbn_list = book.get('isbn', [])
#     isbn = isbn_list[0] if isbn_list else 'N/A'
#     cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg" if isbn != 'N/A' else None
    # ratings_average = book.get('ratings_average', 0)
    # ratings_count = book.get('ratings_count', 0)
    # already_read_count = book.get('already_read_count',0)
    
    # if book_id == 'N/A':
    #     print(f"error getting book ID {SyntaxError}")
    # elif book_id != 'N/A' :
    
    #     col1, col2 = st.columns([1, 2])
    #     with col1:
    #         if cover_url:
    #             st.image(cover_url, width=150)
    #         else:
    #             st.write("No image found")
    #     with col2:
    #         if book_id:
    #             st.markdown(f"**ID:** {book_id}")
    #         else:
    #             st.markdown("**ID:** No ID found")
    #         st.markdown(f"**Title:** {title}")
    #         st.markdown(f"**Author:** {author}")
    #         st.markdown(f"**Published Year:** {published_year}")
    #         st.markdown(f"**ISBN:** {isbn}")
    #         if isbn != 'N/A':
    #             purchase_url = f"https://cheaper99.com/{isbn}"
    #             link_html = f'<a href="{purchase_url}" target="_blank">Buy this book</a>'
    #             st.markdown(link_html, unsafe_allow_html=True)
    #         else:
    #             st.warning("No purchase link available.")

    #         st.markdown(f"**AVG RATING:** {ratings_average} \n (Based on {ratings_count} user's ratings)")
    #         st.markdown(f"**Read by:** {already_read_count} users.")
    #         st.markdown("Did you read it already too?")
    
    
    # if cover_url:
    #     st.image(cover_url, width=100)
    # else:
    #     st.write("No image found")
    # st.write(f"**Title:** {title}")
    # st.write(f"**Author:** {author}")
    # st.write(f"**Published Year:** {published_year}")
    # st.write(f"**ISBN:** {isbn}")
    # if isbn != 'N/A':
    #     purchase_url = f"https://cheaper99.com/{isbn}"
    #     link_html = f'<a href="{purchase_url}" target="_blank">Buy this book</a>'
    #     st.markdown(link_html, unsafe_allow_html=True)
    # else:
    #     st.write("No purchase link available.")

    # if book_id:
    #     st.write(f"**ID:** {book_id}")
    # else:
    #     st.write("No ID found")
        
    # st.write(f"**AVG RATING :** : {ratings_average}")
    # st.write(f"Based on {ratings_count} user's ratings")

    # st.write(f"Read by {already_read_count} users.")
    # st.write("Did you read it already too ?")
    
    # btn_key = book_id if book_id else f'Unv ID'
    # if st.button(f"Add to 'Already Read'", key=btn_key):
    #     try:
    #         add_book_to_already_read(book_id)
    #         st.success(f"Added {title} to 'Already Read'")
            
    #     except Exception as e:
    #         print(f"an error occured : \n {e}")
    #         return False

# function to perform a search query from the open library APi 
# def search_openAPI_lib(search, limit=9, page=1):
#     search_url = f"https://openlibrary.org/search.json?q={search}&limit={limit}&page={page}"
    # try:
    #     response = requests.get(search_url)
    #     if response.ok:
    #         results = response.json()
    #         books = results.get('docs', [])
            
    #         unique_books = []
    #         seen_isbns = set()
    #         for book in books:
                
    #             isbn_list = book.get('isbn', [])
    #             if isbn_list:
    #                 isbn = isbn_list[0]
    #                 if isbn not in seen_isbns:
    #                     seen_isbns.add(isbn)
    #                     unique_books.append(book)
    #             if len(unique_books) >= limit:
    #                 break
            
    #         return {'docs': unique_books}
    #     else:
    #         st.error('Failed to retrieve data from Open Library')
    #         return None
    # except requests.RequestException as e:
    #     st.error(f"An error occurred while fetching data: {e}")
#         return None


# def show_search_result(search_results):
    # if search_results and 'docs' in search_results:
    #     books = search_results['docs']
        
#         # Create rows of books, three books per row
#         rows = [books[i:i + 3] for i in range(0, len(books), 3)]
#         for row in rows:
#             cols = st.columns(3)  # Create three columns
#             for idx, book in enumerate(row):
#                 with cols[idx]:
#                     # check_or_add_book_to_db(book)
#                     display_book_details(book)
    

    


# def redirect_to_cheaper99(isbn):
#     return redirect(f"https://cheaper99.com/{isbn}")
    
# def display_book_details(book):
#     book_id = check_or_add_book_db(book)
#     title = book.get('title', 'No Title Available')
#     author = ', '.join(book.get('authors', ['Unknown Author']))
#     published_year = book.get('first_publish_year', 'Unknown')
#     isbn_list = book.get('isbn', [])
#     isbn = isbn_list[0] if isbn_list else 'N/A'
#     cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg" if isbn != 'N/A' else None

#     user_pseudo = st.session_state.get('current_user', 'guest')

#     if cover_url:
#         st.image(cover_url, width=100)
#     else:
#         st.write("No image found")

#     st.write(f"**Title:** {title}")
#     st.write(f"**Author:** {author}")
#     st.write(f"**Published Year:** {published_year}")
#     st.write(f"**ISBN:** {isbn}")

#     if isbn != 'N/A':
#         purchase_url = f"https://cheaper99.com/{isbn}"
#         link_html = f'<a href="{purchase_url}" target="_blank">Buy this book</a>'
#         st.markdown(link_html, unsafe_allow_html=True)
#     else:
#         st.write("No purchase link available.")

#     if book_id:
#         st.write(f"**ID:** {book_id}")
#     else:
#         st.write("No ID found")

#     if st.checkbox(f"Add to 'Already Read'", key=f'already_read_{book_id}'):
#         add_book_to_already_read(user_pseudo, book_id)
#         st.success(f"Added {title} to 'Already Read'")
# def get_open_library_data(title):
#     url = f"https://openlibrary.org/search.json?title={title}"
#     response = requests.get(url)
#     if response.status_code == 200:
#         data = response.json()
#         return data['docs']
#     else:
#         st.error("Error fetching data from Open Library API")
#         return []
    




            
# Function to handle the search form 
# def search_book_form():
    
#     search_query = st.text_input("what book we reading today !")
#     submitt_search = st.button(label="search")
    
#     if submitt_search and search_query : 
#         search_results = search_openAPI_lib(search_query, limit=9, page=1)
#         if search_results:
#             st.session_state['search_results'] = search_results
#             print(f'new books found for you : \n ')
#             # show_search_result( st.session_state['current_user'],search_results)
#             show_search_result(search_results)
#             return search_results
#         else :
#             print("cannot fetch the result : ")
##################### CHATGPT CODE :
# def search_book_form():
#     search_query = st.text_input("What book are we reading today!")
#     submitt_search = st.button(label="Search")
    
#     if submitt_search and search_query:
#         search_results = search_openAPI_lib(search_query)
        
        
#         st.session_state['search_results'] = search_results
#         show_search_result(search_results)
#         return search_results
#     else:
#             st.write("Cannot fetch the result.")
        
        
###############################
# def show_search_result(search_results):
#     if search_results and 'docs' in search_results:
#         books = search_results['docs']
#         # Create rows of books, three books per row
#         rows = [books[i:i + 3] for i in range(0, len(books), 3)]
#         for row in rows:
#             cols = st.columns(3)  # Create three columns
#             for idx, book in enumerate(row):
#                 # check_or_add_book_to_db(book)
#                 with cols[idx]:
#                     # check_or_add_book_to_db(book)
#                     display_book_details(book)
############################ CHATGOT CODE :
# def show_search_result(search_results):
#     if search_results and 'docs' in search_results:
#         books = search_results['docs']
        
#         rows = [books[i:i + 3] for i in range(0, len(books), 3)]
#         for row in rows:
#             cols = st.columns(3)
#             for idx, book in enumerate(row):
#                 book_id = check_or_add_book_db(book)
#                 book['_id'] = book_id
#                 with cols[idx]:
#                     display_book_details(book)
                    
                    
# def display_book_details(book, user_pseudo):
#     book_id = book.get('_id', 'No ID found')
#     title = book.get('title', 'No Title Available')
#     author = ', '.join(book.get('author_name', ['Unknown Author']))
#     published_year = book.get('first_publish_year', 'Unknown Year')
#     isbn_list = book.get('isbn', [])
#     isbn = isbn_list[0] if isbn_list else 'N/A'
#     cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg" if isbn != 'N/A' else None
    # ratings_average = book.get('ratings_average', 0)
    # ratings_count = book.get('ratings_count', 0)
    
#     st.write(f"**Title:** {title}")
#     st.write(f"**Author:** {author}")
#     st.write(f"**Published Year:** {published_year}")
#     st.write(f"**ISBN:** {isbn}")
#     if cover_url:
#         st.image(cover_url, width=100)
#     else:
#         st.write("No image found")
#     st.write(f"**ID:** {book_id}")
#     st.write(f"**Average Rating:** {ratings_average}")
#     st.write(f"**Ratings Count:** {ratings_count}")
    
#     if st.checkbox(f"Add to 'Already Read'", key=f"{book_id}_checkbox"):
#         add_to_already_read(book_id, user_pseudo)
#         st.success(f"Added {title} to 'Already Read'")
        
        
# def main():
#     st.title("Book Finder")
#     st.write("Hi poutil, welcome to your home page.")
#     book_title = st.text_input("What book are we reading today?", "")
#     user_pseudo = st.text_input("Enter your pseudo:", "")
#     if st.button("Search"):
#         books = search_openAPI_lib(book_title)
#         if books:
#             for book in books:
                # book_id = check_or_add_book_db(book)
                # book['_id'] = book_id
                # display_book_details(book, user_pseudo)
#         else:
#             st.write("No books found")

# if __name__ == "__main__":
#     main()

    # checkbox_key = f"checkbox_{book_id}"
    # already_read = st.checkbox("Add to 'Already Read'", key=checkbox_key)
    # if already_read:
    #     add_to_already_read(user_pseudo, book_id)
    #     st.success(f"Added {title} to 'Already Read'")

        
    # Handling add to favorites without refresh
    # if st.button(f"Add to Favorites {book_id}", key=f"fav_{book_id}"):
    #     add_to_favorites(user_pseudo, book_id)
    #     st.success(f"Added {title} to favorites")
                    

# def display_book_details(book):
#     book_id = check_or_add_book_db(book)
#     title = book.get('title', 'No Title Available')
#     author = book.get('author_name', ['Unknown Author'])[0]
#     published_year = book.get('first_publish_year', 'Unknown Year')
#     isbn_list = book.get('isbn', [])
#     isbn = isbn_list[0] if isbn_list else 'N/A'
#     cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg" if isbn != 'N/A' else None
    
#     user_pseudo = st.session_state['current_user']

#     if cover_url:
#         st.image(cover_url, width=100)
#     else:
#         st.write("No image found")

#     st.write(f"**Title:** {title}")
#     st.write(f"**Author:** {author}")
#     st.write(f"**Published Year:** {published_year}")
#     st.write(f"**ISBN:** {isbn}")

#     if isbn != 'N/A':
#         purchase_url = f"https://cheaper99.com/{isbn}"
#         link_html = f'<a href="{purchase_url}" target="_blank">Buy this book</a>'
#         st.markdown(link_html, unsafe_allow_html=True)
#     else:
#         st.write("No purchase link available.")
        
    
#     if book_id != None :
#         st.write(f"**ID :** {book_id}")
#     else :
#         st.write("No ID found")
        
#     if st.button("Add to Favorites", key=book_id):
#             add_to_favorites(st.session_state['current_user'] , book_id)
    # if st.button("Leave a Review", key=book['isbn'] + "_review"):
    #         st.text_input("Enter your review")
    #         st.slider("Rating", 1, 5)
    

    

# def add_to_favorites(user_pseudo, book_id):
#     user = users_collection.find_one({"pseudo": user_pseudo})
#     if user:
#         users_collection.update_one(
#             {"pseudo": user_pseudo}, 
#             {"$addToSet": {"favBooks": ObjectId(book_id)}}
#         )






# def check_if_favorite(user_pseudo, book_id):
#     # Implement a check to see if the book_id is in the user's favBooks list
#     with get_mongo_client() as client:
#         db = client['ibooks']
#         users_collection = db['users']
#         user = users_collection.find_one({'pseudo': user_pseudo})
#         return book_id in user.get('favBooks', [])





# def add_to_favorites(user_pseudo, book_id):
#     # Add book_id to the user's favBooks list
#     with get_mongo_client() as client:
#         db = client['ibooks']
#         users_collection = db['users']
#         users_collection.update_one({'pseudo': user_pseudo}, {'$addToSet': {'favBooks': book_id}})
#         st.success("Added to favorites!")





# def remove_from_favorites(user_pseudo, book_id):
#     # Remove book_id from the user's favBooks list
#     with get_mongo_client() as client:
#         db = client['ibooks']
#         users_collection = db['users']
#         users_collection.update_one({'pseudo': user_pseudo}, {'$pull': {'favBooks': book_id}})
#         st.success("Removed from favorites!")






# def add_to_favorites_new(user_pseudo, book_id):
#     with get_mongo_client() as client:
#         db = client['ibooks']
#         users_collection = db['users']
        
#         # Ensure book_id is in a correct format
#         if not ObjectId.is_valid(book_id):
#             print("Invalid book ID")
#             return False

#         # book_id_str = str(ObjectId(book_id))  # Ensure the book ID is a string format
#         user = users_collection.find_one({'pseudo': user_pseudo})
#         if user:
#             fav_books_ids = user.get('favBooks', [])
#             if book_id not in fav_books_ids:
#                 fav_books_ids.append(book_id)
#                 users_collection.update_one(
#                     {'pseudo': user_pseudo},
#                     {'$set': {'favBooks': fav_books_ids}}
#                 )
#                 return True
#             else:
#                 return False
#         return False

# def display_book_details(book):
#     title = book.get('title', 'No Title Available')
#     author = book.get('author_name', ['Unknown Author'])[0]
#     published_year = book.get('first_publish_year', 'Unknown Year')
#     isbn_list = book.get('isbn', [])
#     isbn = isbn_list[0] if isbn_list else 'N/A'
#     cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg" if isbn != 'N/A' else None

#     if cover_url:
#         st.image(cover_url, width=100)
#     else:
#         st.write("No image found")

#     st.write(f"**Title:** {title}")
#     st.write(f"**Author:** {author}")
#     st.write(f"**Published Year:** {published_year}")
#     st.write(f"**ISBN:** {isbn}")

#     if isbn != 'N/A':
#         purchase_url = f"https://cheaper99.com/{isbn}"
#         link_html = f'<a href="{purchase_url}" target="_blank">Buy this book</a>'
#         st.markdown(link_html, unsafe_allow_html=True)
#     else:
#         st.write("No purchase link available.")

#     # Generate a unique key for the button using the book ID
#     fav_button_key = f"fav_{isbn}"  # Ensure the key is unique
#     button_pressed = st.button("Add to Favorites", key=fav_button_key)

#     # Manage button press
#     if button_pressed:
#         st.session_state[f'pressed_{fav_button_key}'] = True

#     # Handle after button press
#     if st.session_state.get(f'pressed_{fav_button_key}'):
#         user_pseudo = st.session_state.get('current_user', 'default_user')
#         book_id = str(book['_id'])  # Assuming book['_id'] is stored correctly
#         if add_to_favorites_new(user_pseudo, book_id):
#             st.success("Book added to favorites!")
#             # Optionally reset the button state after handling
#             st.session_state[f'pressed_{fav_button_key}'] = False
#         else:
#             st.error("Failed to add book to favorites or already in favorites.")
#             # Optionally reset the button state after handling
#             st.session_state[f'pressed_{fav_button_key}'] = False
            
            
# # Dummy function for adding a book to favorites, replace with actual function call
# def add_to_favorites_new(user_pseudo, book_id):
#     with get_mongo_client() as client:
#         db = client['ibooks']
#         users_collection = db['users']
#         book_collection = db['books']
        
#         # Make sure the book_id is a valid ObjectId
#         if not ObjectId.is_valid(book_id):
#             print("Invalid book ID")
#             return False

#         # Convert book_id to string format to store in favBooks as per your database schema
#         book_id_str = book_collection.find_one(book_id)
#         user = users_collection.find_one({'pseudo': user_pseudo})
#         if user:
#             fav_books_ids = user.get('favBooks', [])
#             if book_id_str not in fav_books_ids:
#                 fav_books_ids.append(book_id_str)
#                 users_collection.update_one(
#                     {'pseudo': user_pseudo},
#                     {'$set': {'favBooks': fav_books_ids}}
#                 )
#                 print("Book added to favorites")  # Debug message
#                 return True
#             else:
#                 print("Book already in favorites")  # Debug message
#                 return False
#         else:
#             print("User not found")  # Debug message
#             return False
#         # print(f"Attempting to add book {book_id} for user {user_pseudo}")
#         # return True

# def display_book_details(book):
#     db = with get_mongo_client
#     user_pseudo = st.session_state['current_user']  # Example user, replace with st.session_state.get('current_user') if set
#     book_collection = db['books']
#     book_id = str(book.get(''))  # Assume book['_id'] is already a string or convert as needed

#     # Display book details
#     st.write(f"Title: {book.get('title', 'No Title Available')}")
#     if st.button(f"Add to Favorites", key=f"fav-{book_id}"):
#         st.write("Button pressed")  # Immediate feedback
#         if add_to_favorites_new(user_pseudo, book_id):
#             st.success("Book added to favorites!")
#         else:
#             st.error("Failed to add book to favorites or already in favorites.")

# Example book data
# book_example = {
#     '_id': '662aacb2d290c293abf7f519',
#     'title': "The Adventures of Sherlock Holmes"
#}

# Call the display function
# display_book_details(book_example)
                
            
                        
# def display_book_details(book):
#     if isinstance(book, dict):
#         # Assuming 'books' is a dictionary containing book details
#         title = book.get('title', 'No Title')
#         author = book.get('author', ['Unknown'])
#         published_year = book.get('published_year', 'Not Available')
#         isbn_list = book.get('isbn', [])
#         if isbn_list:
#                 isbn = isbn_list[0] 
#         cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg" if isbn != 'N/A' else None

#         # Display details
#         if cover_url:
#             st.image(cover_url, caption=title, width=100)
#         url = f"https://cheaper99.com/{isbn}" if isbn != 'N/A' else "#"
#         title_link = f"<a href='{url}' target='_blank'>{title}</a>"
#         st.markdown(title_link, unsafe_allow_html=True)
        
#         st.write(f"**Title:** {title}")
#         st.write(f"**Author:** {author}")
#         st.write(f"**First Published Year:** {published_year}")
#         st.write(f"**ISBN:** {isbn}")
        
        
#     else:
#         st.error("Data format not recognized, expected a dictionary.")
        
        
        

# def review_form(user_pseudo, book_id):
#     with st.form(key='review_form'):
#         review_text = st.text_area("Review Text", placeholder="Enter your review here...")
#         rating = st.slider("Rating", min_value=1, max_value=5, value=3)
#         submit_button = st.form_submit_button("Submit Review")
        
#         if submit_button:
#             success = submit_review(user_pseudo, book_id, review_text, rating)
#             if success:
#                 st.success("thanks for leaving a review !")
#                 return user_pseudo, book_id, review_text, rating
#             else:
#                 st.error("failed to add your review")
                
                


# def show_search_result(user_pseudo, search_results):
#     if search_results and 'docs' in search_results:
#         books = search_results['docs']  
        
#         for index, book in enumerate(books[:9]):  # Limiting to display only the first 9 books
#             isbn = book.get('isbn') 
#             unique_key = f"fav_{index}_{isbn}"
            
#             # Check if the book is in the database and add if not
#             book_in_db = check_or_add_book_to_db(book)
#             book_id = book_in_db.get('_id') if book_in_db else None
            
#             if isinstance(book, dict):
#                 title = book.get('title')
#                 author = book.get('author_name')
#                 published_year = book.get('first_publish_year'),
#                 isbn_list = book.get('isbn', [])
#                 if isbn_list:
#                         isbn = isbn_list[0] 
#                 cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg" if isbn != 'N/A' else None

#                 # Display details
#                 if cover_url:
#                     st.image(cover_url, caption=title, width=100)
#                 url = f"https://cheaper99.com/{isbn}" if isbn != 'N/A' else "#"
#                 title_link = f"<a href='{url}' target='_blank'>{title}</a>"
#                 st.markdown(title_link, unsafe_allow_html=True)
                
#                 st.write(f"**Title:** {title}")
#                 st.write(f"**Author:** {author}")
#                 st.write(f"**First Published Year:** {published_year}")
#                 st.write(f"**ISBN:** {isbn}")
                
#                 # is_favorite = is_book_in_favs(user_pseudo, isbn) if isbn else False

        
     
#                 fav_checked = st.checkbox("Add to favorites", value=book_id in st.session_state['favorites'], key=unique_key)
#                 try :
#                     # fav_checked = st.checkbox("Add to favorites", value=is_favorite , key=unique_key)
#                     if fav_checked and is_book_in_favs == True:
#                         print(f"book {book_id} is already in favs ")
#                         # success = add_book_to_favorites(user_pseudo, book_id)  # Your function to add to DB
#                         # if success:
#                         #       # Update session state
#                         #     st.session_state['favorites'].append(book_id)
#                         #     st.success("Book added to favorites successfully.")
#                     elif fav_checked and is_book_in_favs == False :
#                         print(f"book {title} to be added to favorites <3")
#                         success = add_book_to_favorites(user_pseudo, book_id)
#                         if success :
#                             # Update session state
#                             st.session_state['favorites'].append(book_id)
#                             st.success(f"book's id {book_id} is added successfully !!")
#                     else :
#                         print(f"error adding the book !")
#                 except KeyError as e:
#                     st.error(f"Error occurred: {e}")
                
                    



# def show_search_results(user_pseudo, search_results):
#     if search_results is None or 'docs' not in search_results:
#         st.error("No valid search results available to display.")
#         return

#     books = search_results['docs']
#     for index, book in enumerate(books[:9]):  # Limiting to display only the first 9 books
#         isbn_list = book.get('isbn', [])
#         isbn = isbn_list[0] if isbn_list else 'N/A'
#         unique_key = f"fav_{index}_{isbn}"

#         # Initialize session state for each book's favorite button
#         if unique_key not in st.session_state['button_clicked']:
#             st.session_state['button_clicked'][unique_key] = False

#         # Check if the book is in the database and add if not
#         book_in_db = check_or_add_book_to_db(book)
#         book_id = book_in_db.get('_id') if book_in_db else None

#         # Extract book details
#         title = book.get('title', 'No Title')
#         author = ', '.join(book.get('author_name', ['Unknown Author']))
#         published_year = book.get('first_publish_year', 'Not Available')
#         cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg" if isbn != 'N/A' else None

#         # Display details
#         if cover_url:
#             st.image(cover_url, caption=title, width=100)
#         url = f"https://cheaper99.com/{isbn}" if isbn != 'N/A' else "#"
#         title_link = f"<a href='{url}' target='_blank'>{title}</a>"
#         st.markdown(title_link, unsafe_allow_html=True)
        
#         st.write(f"**Title:** {title}")
#         st.write(f"**Author:** {author}")
#         st.write(f"**First Published Year:** {published_year}")
#         st.write(f"**ISBN:** {isbn}")
#         is_fav = is_book_in_favs(user_pseudo, book_id)


#         add_fav = st.checkbox("Add this book to your favorites", key=unique_key, value=is_fav)
#         # Execute logic based on checkbox state
#         if add_fav and add_fav== True:
            
#             st.write(f"Book with ID {book_id} is already in your favorites.")
#         elif add_fav and add_fav== False:
#                 if add_book_to_favorites(user_pseudo, book_id):
#                     st.write(f"Book with ID {book_id} has been added to your favorites.")
#                 else:
#                     st.write("Failed to add the book to your favorites.")
#         else:
#             st.write("Check the box to add this book to your favorites.")
        
        
        
            
            
        # if st.session_state['button_clicked'][unique_key]:
        #     try:
        #         book_details = {
        #             'title': title,
        #             'author': author,
        #             'published_year': published_year,
        #             'isbn': isbn
        #         }
        #         check_booksFav = is_book_in_favs(user_pseudo, isbn)
        #         if check_booksFav == True :
        #             st.warning("This book is already in your favorites list!")
        #         elif check_booksFav == False :
        #             handle_add_to_favorites(user_pseudo, book_details)
            # except KeyError as e:
            #     st.error(f"Error occurred: {e}")
            # finally:
            #     st.session_state['button_clicked'][unique_key] = False 

# def show_search_result(user_pseudo, search_results):
#     if search_results and 'docs' in search_results:
#         books = search_results['docs']
        
#         for index, book in enumerate(books[:9]):  # Limiting to display only the first 9 books
#             isbn_list = book.get('isbn', [])
#             isbn = isbn_list[0] if isbn_list else 'N/A'
#             unique_key = f"fav_{index}_{isbn}"
            
#             # Initialize session state for each book's favorite button
#             if unique_key not in st.session_state['button_clicked']:
#                 st.session_state['button_clicked'][unique_key] = False

#             # Check if the book is in the database and add if not
#             book_in_db = check_or_add_book_to_db(book)
#             book_id = book_in_db.get('_id') if book_in_db else None

#             # Extract book details
#             title = book.get('title', 'No Title')
#             author = ', '.join(book.get('author_name', ['Unknown Author']))
#             published_year = book.get('first_publish_year', 'Not Available')
#             cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg" if isbn != 'N/A' else None

#             # Display details
#             if cover_url:
#                 st.image(cover_url, caption=title, width=100)
#             url = f"https://cheaper99.com/{isbn}" if isbn != 'N/A' else "#"
#             title_link = f"<a href='{url}' target='_blank'>{title}</a>"
#             st.markdown(title_link, unsafe_allow_html=True)
            
#             st.write(f"**Title:** {title}")
#             st.write(f"**Author:** {author}")
#             st.write(f"**First Published Year:** {published_year}")
#             st.write(f"**ISBN:** {isbn}")

#             add_fav_btn = st.button("Add this book to your favorites", key=unique_key)

#             if add_fav_btn:
#                 st.session_state['button_clicked'][unique_key] = True
#                 st.write("Button clicked")  # Debug info
#             else:
#                 st.write("Button not clicked")  # Debug info

#             if st.session_state['button_clicked'][unique_key]:
#                 try:
#                     book_details = {
#                         '_id' : book_id,
#                         'title': title,
#                         'author': author,
#                         'published_year': published_year,
#                         'isbn': isbn
#                     }
#                     added = handle_add_to_favorites(user_pseudo, book_details)
#                     if added:
#                         st.success(f"Book (ISBN: {isbn}) added to your favorites.")
#                     else:
#                         st.warning("This book is already in your favorites.")
#                 except KeyError as e:
#                     st.error(f"Error occurred: {e}")
#                 finally:
#                     st.session_state['button_clicked'][unique_key] = False 
        
        
        

    
    
    # search_book_form(search_query = st.text_input("Search for a new book here!"))
        

# def show_search_result(user_pseudo, search_results):
#     if search_results and 'docs' in search_results:
        
        
#         books = search_results['docs']
        
#         for index, book in enumerate(books[:9]):  # Limiting to display only the first 9 books
#             isbn_list = book.get('isbn', [])
#             isbn = isbn_list[0] if isbn_list else 'N/A'
#             print(f"book's isbn : {isbn} \n")
            
            
#             # Check if the book is in the database and add if not
#             book_in_db = check_or_add_book_to_db(book)
#             book_id = book_in_db.get('_id') if book_in_db else None
#             unique_key = f"fav_{index}_{isbn}"
#             title = book.get('title')
#             author = ', '.join(book.get('author_name', ['Unknown Author']))
#             published_year = book.get('first_publish_year')
#             cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg" if isbn != 'N/A' else None

#                 # Display details
#             if cover_url:
#                 st.image(cover_url, caption=title, width=100)
                    
#             book_details = {
#                 'title': book.get('title'),
#                 'author': book.get('author_name'),
#                 'isbn': isbn,
#                 'published_year': book.get('first_publish_year'),
#                 'cover_url': cover_url,
#                 'reviews' : []
#                     }    
                
#             url = f"https://cheaper99.com/{isbn}" if isbn != 'N/A' else "#"
#             title_link = f"<a href='{url}' target='_blank'>{title}</a>"
#             st.markdown(title_link, unsafe_allow_html=True)
                
#             st.write(f"**Title:** {title}")
#             st.write(f"**Author:** {author}")
#             st.write(f"**First Published Year:** {published_year}")
#             st.write(f"**ISBN:** {isbn}")
                
#             # print(f"book details : {book_details}")
                
#             add_fav_btn = st.button("add this book to your favorites", key=unique_key)
#             if add_fav_btn :
#                 try :
#                     added = handle_add_to_favorites(user_pseudo, book_details)
#                     if added :
#                         st.success("book added yazaabiiiii")
#                 except(KeyError) as e :
#                     print(f"error occured : \n {e}")
                    
                
                
            # if fav_check :
            #     print("fav clicked")
            #     if book_id : 
            #         handle_add_to_favorites(user_pseudo, book_details)
            #         print(f"book's id : {book_id} added ")   
            #     else :
            #         print(f"book's id : {book_id} not added ")
                    
                    
                    


       

# def main():
#     user_pseudo = "user123"
#     search_query = st.text_input("Search for a new book here!", key="search_query")
#     submit_search = st.button("search")
    
#     if submit_search and search_query:
#         search_results = search_openAPI_lib(search_query)
#         if search_results:
#             show_search_result(user_pseudo, search_results)
#         else:
#             st.error("No search results found.")

# if __name__ == "__main__":
#     main()


            # if isinstance(book, dict):
                
                   
                                
                
                
            # else:
            #     st.error("No valid search results available to display.")
                
            # fav_checked = st.checkbox("Add to favorites", value=book_id in st.session_state['favorites'], key=unique_key)
            # if fav_checked and book_id not in st.session_state['favorites']:
            #     success = add_to_favs(user_pseudo, book_details)  # Your function to add to DB
            #     if success:
            #         st.session_state['favorites'].append(book_id)  # Update session state
            #         st.success("Book added to favorites successfully.")
            #     else:
            #         st.error("Failed to add book to favorites.")
            # elif not fav_checked and book_id in st.session_state['favorites']:
            #     success = remove_for_favs(user_pseudo, book_id)  # Your function to remove from DB
            #     if success:
            #         st.session_state['favorites'].remove(book_id)  # Update session state
            #         st.success("Book removed from favorites successfully.")

            # if book_id:
            #     with st.expander("Leave a Review"):
            #         form_key = f"{unique_key}_form"
            #         with st.form(form_key):
            #             review_text = st.text_area("Review Text", placeholder="Enter your review here...", key=f'review_text_{isbn}')
            #             rating = st.slider("Rating", min_value=1, max_value=5, key=f'rating_{isbn}')
            #             submit_button = st.form_submit_button("Submit Review")

            #             if submit_button:
                            
            #                 add_review_to_book(user_pseudo, isbn, review_text, rating)
            #                 print("adding you review ...")
            #                 if add_review_to_book() != False:
                                
            #                     st.success("Your review has been added!")
            #                 else:
            #                     st.error("Failed to add your review.")
    
    


# def main():
#     user_pseudo = "user123"
#     search_query = st.text_input("Search for a new book here!", key="search_query")
#     submit_search = st.button("search")
    
#     if submit_search and search_query:
#         search_results = search_openAPI_lib(search_query)
#         if search_results:
#             show_search_result(user_pseudo, search_results)
#         else:
#             st.error("No search results found.")

# if __name__ == "__main__":
#     main()

            
                # fav_checked = st.checkbox("❤️ Add to favorites", key=unique_key)
                
                # if fav_checked : 
                #     book_details = {}
                #     handle_add_to_favorites(user_pseudo, book_details)
                    
                        
                

                # if fav_checked and is_book_in_favs == True:
                #     success = add_to_favs(user_pseudo, book_id)
                #     if success : 
                #         print (f"book added to favorites collection with id : {book_id}")
                #         st.success("book added succesfully !")
                # elif fav_checked == False:
                #     success = remove_for_favs(user_pseudo, book_id)
                #     if success : 
                #         print (f"book removed from favorites collection with id : {book_id}")
                #         st.success("book removed succesfully !")
                    
                    
                    # if not st.session_state[unique_key]:  # Only handle the logic once when the checkbox is checked
                    #     st.session_state[unique_key] = True
                    #     if not any(book['isbn'] == isbn for book in st.session_state['favorites']):
                    #         book_details = {
                    #             'title': book.get('title', 'No Title'),
                    #             'author': author,
                    #             'published_year': published_year,
                    #             'isbn': isbn
                    #         }
                    #         st.session_state['favorites'].append(book_details)
                    #         handle_add_to_favorites(user_pseudo, isbn)
                    #         st.success(f"Book (ISBN: {isbn}) added to your favorites.")
                    #     else:
                    #         st.warning("This book is already in your favorites.")
                
                


 
 

#             # cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg" if isbn else None
            
#             # book_details = {
#             #             'title': book.get('title'),
#             #             'author': book.get('author_name'),
#             #             'isbn': isbn,
#             #             'published_year': book.get('first_publish_year'),
#             #             'cover_url': cover_url,
#             #             'reviews' : []
#             #         }
#             # print(f"book found : \n {book_details} \n ")
            
            
#             # Check if the book is already a favorite


#             # print(f"book type : \n {type(book)} \n ")
#             # Display book details

#                 # else:
#                 #     handle_book_selection(user_pseudo=st.session_state['current_user'], search_results=st.session_state['search_results'])
                    

#                 if book_id:
#                     with st.expander("Leave a Review"):
#                         with st.form(key=f'review_form_{index}'):
#                             review_text = st.text_area("Review Text", placeholder="Enter your review here...")
#                             rating = st.slider("Rating", min_value=1, max_value=5, value=3)
#                             submit_button = st.form_submit_button("Submit Review")

#                             if submit_button:
#                                 add_review_to_book(user_pseudo, book_id, review_text, rating)
#                                 success = submit_review(user_pseudo, book_id, review_text, rating)
#                                 if success:
#                                     st.success("Your review has been added!")
#                                 else:
#                                     st.error("Failed to add your review.")
                

#         return search_results
#     else:
#         st.error("No valid search results available to display.")


# Function to display the homepage


# def main():
#     # Check login state
#     if st.session_state.get('logged_in', False):
#         show_user_homepage(pseudo=st.session_state['current_user'])  # Show the homepage if the user is logged in
#     else:
#         st.write("Please log in.")  # Or redirect them to the login page

# if __name__ == "__main__":
#     main()











