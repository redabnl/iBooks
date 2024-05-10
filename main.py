import streamlit as st
from frontE.login import login
from frontE.register import register
from frontE.homePage import show_user_homepage, show_explorer_page
from frontE.library import show_library

def main():
    # Initialize session states if they don't exist
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'current_user' not in st.session_state:
        st.session_state['current_user'] = None

    st.sidebar.title('Navigation')






    # First check if the user is already logged in
    if st.session_state['logged_in']:
        # Display the navigation menu
        choice = st.sidebar.radio("Navigate to:", ['Home', 'Library', 'Explorer'])
        if choice == 'Home':
            show_user_homepage(st.session_state['current_user'])
        elif choice == 'Library':
            # Assuming you have a function to show the library page
            show_library(st.session_state['current_user'])
        elif choice == 'Explorer':
            # Assuming you have a function to show the explorer page
            show_explorer_page()
    else:
        # User is not logged in, show registration or login option
        st.title("Welcome to the Virtual Library")
        user_choice = st.radio("Choose an option:", ['Register', 'Login'])

        if user_choice == 'Login':
            # Function to handle user login
            user = login()
            if user is not None:
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = user
                show_user_homepage(user)  # Redirect to home page after successful login
        else:
            # Function to handle user registration
            register()
            # Optionally, you can directly log the user in after registration, or let them log in manually

# Execute the main function when the script is run
if __name__ == "__main__":
    main()
