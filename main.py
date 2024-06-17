import streamlit as st
from frontE.login import login
from frontE.register import register
from frontE.explorer import show_explorer_page
from frontE.library import show_user_library
from frontE.homePage import  show_user_homepage
from data.book_model import get_user_read_books
from data.models import logout

def local_css(filename):
    with open(filename) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Load the CSS file
local_css("frontE/styles/style.css")

def main():
    # Initialize session states if they don't exist
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'current_user' not in st.session_state:
        st.session_state['current_user'] = None
    if 'already_read' not in st.session_state:
        st.session_state['already_read'] = []
    if 'button_clicked' not in st.session_state:
        st.session_state['button_clicked'] = {}
    if 'search_results' not in st.session_state:
        st.session_state['search_results'] = []
    # if 'current_book' not in st.session_state:
    #     st.session_state['current_book'] = None

    st.sidebar.title('Navigation')
    
    
    # User is not logged in, redirect to register or login
    if not st.session_state['logged_in']:
        user_choice = st.sidebar.radio("Choose an option:", ['Login', 'Register'])
        if user_choice == 'Login':
            user_pseudo = login()
            if user_pseudo is not None:
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = user_pseudo
                st.session_state['favorites'] = []
        elif user_choice == 'Register':
            register()
    else:
        # Navigation menu
        choice = st.sidebar.radio("Navigate to:", ['Home', 'Library', 'Explorer'])
        if choice == 'Home':
            show_user_homepage()
            
        elif choice == 'Library':
            show_user_library()
            
        elif choice == 'Explorer':
            show_explorer_page()
        st.sidebar.button("logout", on_click=logout)

if __name__ == "__main__":
    main()


# def main():
#     st.sidebar.title("Navigation")
#     page = st.sidebar.radio("Navigate to:", ["Home", "Library", "Explorer"])

#     if page == "Home":
#         st.title("Home Page")
#         st.write("Search for a new book here!")
        
#         search_query = st.text_input("Enter book name or author:")
#         if st.button("Search"):
#             st.write(f"Searching for: {search_query}")
#             # Dummy book result for demonstration
#             search_results = {
#                 "cover_url": "https://example.com/cover.jpg",
#                 "title": "Soufi, mon amour",
#                 "author": "Elif Shafak, Dominique Letellier",
#                 "first_published_year": "2011",
#                 "isbn": "2264054069"  # This should be the unique ID from your database
#             }
#             user_pseudo = "poutit"  # Replace with the actual user pseudo
#             show_search_results(user_pseudo, search_results)

#     elif page == "Library":
#         st.title("Library")
#         st.write("Your favorite books will be listed here.")

#     elif page == "Explorer":
#         st.title("Explorer")
#         st.write("Explore new books and authors.")

# if __name__ == "__main__":
#     main()

