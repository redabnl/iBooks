import streamlit as st
from frontE.login import login
from frontE.register import register
from frontE.homePage import show_user_homepage, show_explorer_page
from frontE.library import show_library

def main():
    # Initializing session states if they don't exist
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'current_user' not in st.session_state:
        st.session_state['current_user'] = None

    st.sidebar.title('Navigation')






    # First check if the user is already logged in
    if st.session_state['logged_in']:
        # navigation menu
        choice = st.sidebar.radio("Navigate to:", ['Home', 'Library', 'Explorer'])
        if choice == 'Home':
            show_user_homepage(st.session_state['current_user'])
        elif choice == 'Library':
            # redirecting to library page
            show_library(st.session_state['current_user'])
        elif choice == 'Explorer':
            # Assuming you have a function to show the explorer pageredirectingto 'explorer' page
            show_explorer_page()
    else:
        # User is not logged in, redirect to register or login
        st.title("Welcome to the Virtual Library")
        user_choice = st.radio("Choose an option:", ['Register', 'Login'])

        if user_choice == 'Login':
            # user login func
            user = login()
            if user is not None:
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = user
                show_user_homepage(user)  # Redirect to home page after successful login
        else:
            # user registration func
            register()
            


if __name__ == "__main__":
    main()
