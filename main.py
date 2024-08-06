import streamlit as st
from frontE.login import login
from frontE.register import register
from frontE.explorer import show_explorer_page
from frontE.library import show_library
from frontE.homePage import  show_user_homepage
# from data.book_model import get_user_read_books
from data.models import logout
import os


def local_css(style):
    with open(style) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Load the main CSS file
# local_css(os.path.join('frontE', 'styles', 'main.css'))

def show_nav():
    st.markdown("""
    <style>
        .nav-links {
            display: flex;
            justify-content: space-around;
            background-color: #f8f9fa;
            padding: 10px 0;
        }
        .nav-links a {
            text-decoration: none;
            color: #000;
            font-weight: bold;
        }
        .nav-links a:hover {
            text-decoration: underline;
        }
    </style>
    <div class="nav-links">
        <a href="?page=home">Home</a>
        <a href="?page=library">Library</a>
        <a href="?page=explorer">Explorer</a>
        <a href="?page=logout">Logout</a>
    </div>
    """, unsafe_allow_html=True)

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

    if not st.session_state['logged_in']:
        user_choice = st.sidebar.radio("Choose an option:", ['Login', 'Register'])
        if user_choice == 'Login':
            user_pseudo = login()
            if user_pseudo is not None:
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = user_pseudo
                st.experimental_rerun()
        elif user_choice == 'Register':
            register()
            if register == True :
                login()
    elif st.session_state['logged_in'] == True:
        show_nav()
        
        user_pseudo= st.session_state['current_user']
        query_params = st.experimental_get_query_params()
        page = query_params.get('page', ['home'])[0]

        if page == 'home':
            local_css("frontE/styles/homePage.css")
            
            show_user_homepage(user_pseudo)
        elif page == 'library':
            show_library(st.session_state['current_user'])
        elif page == 'explorer':
            show_explorer_page()
        elif page == 'logout':
            st.session_state['logged_in'] = False
            st.session_state['current_user'] = None
            st.session_state['already_read'] = []
            st.session_state['button_clicked'] = {}
            st.session_state['search_results'] = []
            st.session_state['current_book'] = None
            st.experimental_set_query_params()
            st.experimental_rerun()

# def main():

#     # Initialize session states if they don't exist
#     if 'logged_in' not in st.session_state:
#         st.session_state['logged_in'] = False
#     if 'current_user' not in st.session_state:
#         st.session_state['current_user'] = None
#     if 'already_read' not in st.session_state:
#         st.session_state['already_read'] = []
#     if 'button_clicked' not in st.session_state:
#         st.session_state['button_clicked'] = {}
#     if 'search_results' not in st.session_state:
#         st.session_state['search_results'] = []

#     def show_nav():
#         st.markdown("""
#         <style>
#             .nav-links {
#                 display: flex;
#                 justify-content: space-around;
#                 background-color: #f8f9fa;
#                 padding: 10px 0;
#             }
#             .nav-links a {
#                 text-decoration: none;
#                 color: #000;
#                 font-weight: bold;
#             }
#             .nav-links a:hover {
#                 text-decoration: underline;
#             }
#         </style>
#         <div class="nav-links">
#             <a href="?page=home">Home</a>
#             <a href="?page=library">Library</a>
#             <a href="?page=explorer">Explorer</a>
#             <a href="?page=logout">Logout</a>
#         </div>
#         """, unsafe_allow_html=True)
    
#     if not st.session_state['logged in']:
#         user_choice = st.sidebar.radio("Choose an option:", ['Login', 'Register'])
#         if user_choice == 'Login':
#             user_pseudo = login()
#             if user_pseudo is not None:
#                 st.session_state['logged_in'] = True
#                 st.session_state['current_user'] = user_pseudo
#                 st.session_state['favorites'] = []
#         elif user_choice == 'Register':
#             register()
#     else:
#         show_nav()
        
#         query_params = st.experimental_get_query_params()
#         page = query_params.get('page', ['home'])[0]

#         if page == 'home':
#             user_pseudo = st.session_state['current_user']
#             local_css("frontE/styles/homePage.css")
#             show_user_homepage()
#         elif page == 'library':
#             local_css("frontE/styles/library.css")
#             # user_pseudo = st.session_state['current_user']
#             show_library(st.session_state['current_user'])
#         elif page == 'explorer':
#             user_pseudo = st.session_state['current_user']
#             show_explorer_page()
#         elif page == 'logout':
#             st.session_state['logged_in'] = False
#             st.session_state['current_user'] = None
#             st.session_state['already_read'] = []
#             st.session_state['button_clicked'] = {}
#             st.session_state['search_results'] = []
#             st.session_state['current_book'] = None
            
    
if __name__ == "__main__":
    main()
    # User is not logged in, redirect to register or login
    #     if not st.session_state['logged_in']:
    #         user_choice = st.sidebar.radio("Choose an option:", ['Login', 'Register'])
    #         if user_choice == 'Login':
    #             user_pseudo = login()
    #             if user_pseudo is not None:
    #                 st.session_state['logged_in'] = True
    #                 st.session_state['current_user'] = user_pseudo
    #                 st.session_state['favorites'] = []
    #         elif user_choice == 'Register':
    #             register()
    #     else:
    #         # Navigation menu
    #         choice = st.sidebar.radio("Navigate to:", ['Home', 'Library', 'Explorer'])
    # with st.container():
        
    #     if st.session_state['logged_in'] :
    #         if choice == 'Home':
    #             st.markdown('<div class="container">', unsafe_allow_html=True)
    #             show_user_homepage()
    #             st.markdown('</div>', unsafe_allow_html=True)
                
    #         elif choice == 'Library':
    #             show_user_library()
                
    #         elif choice == 'Explorer':
    #             show_explorer_page()
    #         st.sidebar.button("logout", on_click=logout)
    #     else :
    #         st.write("Please log in to use our app")
        

    
#     with st.sidebar:
#         st.title('Navigation')
#         if not st.session_state['logged_in']:
#             user_choice = st.radio("Choose an option:", ['Login', 'Register'])
#             if user_choice == 'Login':
#                 user_pseudo = login()
#                 if user_pseudo:
#                     st.session_state['logged_in'] = True
#                     st.session_state['current_user'] = user_pseudo
#             elif user_choice == 'Register':
#                 register()
#         else:
#             choice = st.radio("Navigate to:", ['Home', 'Library', 'Explorer'])
#             if st.button('Logout'):
#                 st.session_state['logged_in'] = False
#                 st.session_state['current_user'] = None

#     # Main content container
#     with st.container():
#         if st.session_state['logged_in']:
#             if choice == 'Home':
#                 show_user_homepage()
#             elif choice == 'Library':
#                 show_user_library()
#             elif choice == 'Explorer':
#                 show_explorer_page()
#         else:
#             st.write("Please log in to use the app.")

# if __name__ == '__main__':
#     main()
    
    



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

