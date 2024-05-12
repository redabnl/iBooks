import streamlit as st
from frontE.login import login
from frontE.register import register
from frontE.homePage import show_user_homepage
from frontE.library import show_library
from frontE.explorer import show_explorer_page
def main():
    # Initialize session states if they don't exist
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'current_user' not in st.session_state:
        st.session_state['current_user'] = None

    st.sidebar.title('Navigation')

    # User is not logged in, redirect to register or login
    if not st.session_state['logged_in']:
        user_choice = st.sidebar.radio("Choose an option:", ['Login', 'Register'])
        if user_choice == 'Login':
            user = login()
            if user is not None:
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = user
        elif user_choice == 'Register':
            register()
    else:
        # Navigation menu
        choice = st.sidebar.radio("Navigate to:", ['Home', 'Library', 'Explorer'])
        if choice == 'Home':
            show_user_homepage(st.session_state['current_user'])
        elif choice == 'Library':
            show_library(st.session_state['current_user'])
        elif choice == 'Explorer':
            show_explorer_page()

if __name__ == "__main__":
    main()
