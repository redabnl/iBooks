import streamlit as st
import requests
from pymongo import MongoClient
from data.models import add_to_favs


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
def show_search_result(search_results):
    for book in search_results.get('docs', [])[:3]:
         with st.container():
                st.write(f"Title: {book.get('title', 'No Title')}")
                st.write(f"Author: {', '.join(book.get('author_name', []))}")
                st.write(f"First Published Year: {book.get('first_publish_year', 'Not Available')}")
                #unique key for each book to track the button
                unique_key = book.get('title', 'No title').replace("", "-")
                # Instead of creating a new form, use a button and check for its press after the main search form is submitted
                # add_button_key = f"add_to_favs_{book['key']}"
                #button to add the boook to user's favs
                if st.button("Add to favorites", key=unique_key):
                
                    add_button_key = f"add_to_favs_{book['key']}"
                    st.session_state[add_button_key] = False
                    if add_button_key not in st.session_state:
                        st.session_state[add_button_key] = False
                    elif st.session_state[add_button_key]: 
                        # Check if this specific button was pressed
                        # Perform the add to favorites action here
                        book_details = {
                            'title': book.get('title'),
                            'author': book.get('author_name', []),
                            'published_year': book.get('first_publish_year')
                        }
                        if add_to_favs(st.session_state['current_user'], book_details):
                            st.success('Book added to favorites')
                            # Reset the button state after handling
                            st.session_state[add_button_key] = False
                        else:
                            st.error("Failed to add the book to favorites")
                            # Reset the button state after handling
                            st.session_state[add_button_key] = False
                
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
                show_search_result(search_results)
                
                # After displaying search results, check if any add to favorites button was pressed
                
    
    



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
