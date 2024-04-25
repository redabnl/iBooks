import streamlit as st
import requests
from pymongo import MongoClient
from bson import ObjectId
from data.models import add_to_favs, get_mongo_client, is_book_in_favs, remove_for_favs




#function to perform a search query from the open library APi 
def search_openAPI_lib(search):
    search_url = f"https://openlibrary.org/search.json?q={search}"
    response = requests.get(search_url)
    if response.ok:
        return response.json()
    else:
        st.error('failed to retreive data from Open Library')
        return None
    
# Function to display the search result 
# def show_search_result(search_results):
    
    for book in search_results.get('docs', [])[:3] :
        unique_key = book.get('key', None)
        add_to_fav_btn = st.button("Add to favorites", key=f"add_fav_{unique_key}")
        with st.container():
                st.write(f"Title: {book.get('title', 'No Title')}")
                st.write(f"Author: {', '.join(book.get('author_name', []))}")
                st.write(f"First Published Year: {book.get('first_publish_year', 'Not Available')}")
                
                if unique_key:
                    if add_to_fav_btn:
                        book_details = {
                        'title': book.get('title'),
                        'author': book.get('author_name', []),
                        'published_year': book.get('first_publish_year')
                    }
                    if add_to_favs(st.session_state['current_user', book_details]):
                        st.success('book added to favorites !')
                    else:
                        st.error("Failed to add to favs")
                    
                
                
                
                # unique_key = book.get('title', 'No title').replace("", "-")
                # favs_btn = st.form_submit_button("add to favorites", unique_key)
                # # Instead of creating a new form, use a button and check for its press after the main search form is submitted
                # add_button_key = f"add_to_favs_{book['key']}"
                # #button to add the boook to user's favs
                # if favs_btn:
                #     book_details = {
                #             'title': book.get('title'),
                #             'author': book.get('author_name', []),
                #             'published_year': book.get('first_publish_year')
                #         }
                #     if add_to_favs(st.session_state['current_user'], book_details):
                #             st.success('Book added to favorites')
                #             # Reset the button state after handling
                #             st.session_state[add_button_key] = False
                
                    # add_button_key = f"add_to_favs_{book['key']}"
                    # st.session_state[add_button_key] = False
                    # if add_button_key not in st.session_state:
                    #     st.session_state[add_button_key] = False
                    # elif st.session_state[add_button_key]: 
                    #     # Check if this specific button was pressed
                    #     # Perform the add to favorites action here
                    #     book_details = {
                    #         'title': book.get('title'),
                    #         'author': book.get('author_name', []),
                    #         'published_year': book.get('first_publish_year')
                    #     }
                    #     if add_to_favs(st.session_state['current_user'], book_details):
                    #         st.success('Book added to favorites')
                    #         # Reset the button state after handling
                    #         st.session_state[add_button_key] = False
                    #     else:
                    #         st.error("Failed to add the book to favorites")
                    #         # Reset the button state after handling
                    #         st.session_state[add_button_key] = False
                
                # with st.form(key=f"fav_form_{unique_key}"):
                #     submit_button = st.form_submit_button(label="add to fav books")
                #     if submit_button :
                #         book_details = {
                #         'title': book.get('title'),
                #         'author': book.get('author_name', []),
                #         'published_year': book.get('first_publish_year')
                #     }
                #     if add_to_favs(st.session_state['current_user'], book_details):
                #         st.success('Book added to favorites')
                #     else:
                #         st.error("can't add the book to favs")
                        
                
                
                #     add_book_to_favorites(book)  # You would need to implement this function
                # if st.button("add to favs", key=book['key']):
                
                
                

            
# Function to handle the search form 
def search_book_form():
    with st.form("search form"):
        search_query = st.text_input("search for books here !")
        submitt_search = st.form_submit_button(label="search")
        
    if submitt_search and search_query : 
        search_results = search_openAPI_lib(search_query)
        if search_results:
            show_search_result(search_results, st.session_state['current_user'])
                
                # After displaying search results, check if any add to favorites button was pressed
                
    
def show_search_result(search_results, user_pseudo):
    user_pseudo = st.session_state['current_user']
    # Display only the first 3 search results
    for index, book in enumerate(search_results.get('docs', [])[:3]):
        with st.container():
            isbn_list = book.get('isbn', [])
            if isbn_list :
                isbn = isbn_list[0]
                coverURL = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"
            st.image(coverURL, caption=book.get('title'), width=100)
            st.write(f"Title: {book.get('title', 'No Title')}")
            st.write(f"Author: {', '.join(book.get('author_name', ['Unknown']))}")
            st.write(f"First Published Year: {book.get('first_publish_year', 'Not Available')}")
            

            # Generate a unique key for each book
            unique_key = book.get('key')
            # Define a key for the favorite checkbox
            fav_button_key = f"fav_{unique_key}"
            
            is_favorite = is_book_in_favs(user_pseudo, book)

            #user_pseudo = st.session_state['current_user']
            # defining book details 
            book_details = {
                    'title': book.get('title'),
                    'author': book.get('author_name'),
                    'published_year': book.get('first_publish_year'),
                    'author_key' : book.get('author_key'),
                    'ISBN' : isbn_list,
                    'cover_url' : coverURL
                }
            print(book_details)
            
            # Create a heart emoji button to toggle favorite status
            heart_emoji = "❤️" if is_favorite else "🖤"  # Red heart if favorite, black heart if not
            
            
            if st.button(heart_emoji, key = fav_button_key):
                if is_favorite:
                    # If it's already a favorite, remove it
                    if remove_for_favs(user_pseudo, book_details):
                        st.success(f"Book '{book['title']}' removed from favorites")
                        # st.experimental_rerun()  # Rerun the app to update the button status
                    else:
                        st.error(f"Failed to remove '{book['title']}' from favorites")
                else:
                    # If it's not a favorite, add it
                    if add_to_favs(user_pseudo, book_details):
                        print("book added to fav Collection")
                        st.success(f"Book '{book['title']}' added to favorites")
                        # st.experimental_rerun()  # Rerun the app to update the button status
                    else:
                        st.error(f"Failed to add '{book['title']}' to favorites")
                        print("failed to add the book to favs")
            st.write("-----------")
            
            
            # Display the checkbox and use it as an "add to favorites" toggle
            # if st.checkbox("❤️ Add to favorites", key=fav_button_key):
            #     # Here we check if the book is already in the user's favorites
            #     if not is_book_in_favs(st.session_state['current_user'], book_details):
            #         # Book is not in favorites, so add it
            #         if add_to_favs(st.session_state['current_user'], book_details):
            #             st.success(f"Book '{book.get('title')}' added to favorites")
            #         else:
            #             st.error(f"Failed to add '{book['title']}' to favorites")
            #             # Uncheck the checkbox if adding to favorites fails
            #             st.session_state[fav_button_key] = False
            # else:
            #     # Here we check if the book is in the user's favorites and the checkbox was just unchecked
            #     if is_book_in_favs(st.session_state['current_user'], book_details):
            #         # Book is in favorites and needs to be removed
            #         if remove_for_favs(st.session_state['current_user'], book_details):
            #             st.success(f"Book '{book.get('title')}' removed from favorites")
            #         else:
            #             st.error(f"Failed to remove '{book.get('title')}' from favorites")
            #             # Check the checkbox if removing from favorites fails
            #             st.session_state[fav_checkbox_key] = True
            # st.write("-----------")

    



#library function where user's favbooks gonna be displayed
def show_library(user_pseudo):
    with get_mongo_client() as client:
        db = client['ibooks']
        users_collection = db['users']
        books_collection = db['books']  # Assuming you have a separate collection for books

        user_doc = users_collection.find_one({"pseudo": user_pseudo})
        fav_books_ids = user_doc.get('favBooks', [])

        # If you're storing complete book details in favBooks, you can directly iterate over fav_books_ids
        # Otherwise, if favBooks contains ObjectIds, you'd need to retrieve the books from the books_collection
        # For example:
        fav_books = books_collection.find({"_id": {"$in": fav_books_ids}}) if fav_books_ids else []

        for book in fav_books:
            st.subheader(book['title'])
            st.write('Author:', ', '.join(book.get('author', 'Unknown')))
            st.write('Published Year:', book.get('published_year', 'Unknown'))
            

# Function to display the homepage
def show_user_homepage(pseudo):
    if pseudo:
        
        # Header
        st.header(f"{pseudo}'s Home page")
        # st.image('path_to_your_banner_image.jpg', use_column_width=True)  # Replace with your image path

        # Navigation bar (for simplicity, these could just be buttons or links)
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            if st.button('Library'):
                # Logic for showing the Library
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

        # You may also add more sections to display content based on the search or user profile
        st.write("Content based on user profile or search results will appear here.")
        
    else :
        st.error("Pseudo not found please try again")

# Main function to control the page layout
def main():
    # Check login state
    if st.session_state.get('logged_in', False):
        show_user_homepage()  # Show the homepage if the user is logged in
    else:
        st.write("Please log in.")  # Or direct them to the login page

if __name__ == "__main__":
    main()
