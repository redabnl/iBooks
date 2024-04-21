# main.py
import streamlit as st
from frontE import register, login, homePage
from frontE.homePage import show_user_homepage

# Initialize session states if they don't exist
# if 'add_to_favs_works/OL262463W' not in st.session_state:
#     st.session_state['add_to_favs_works/OL262463W'] = False
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'current_user' not in st.session_state :
    st.session_state['current_user'] = None
if 'just_registered' not in st.session_state:
    st.session_state['just_registered'] = False
if 'navigate_to_login' not in st.session_state:
    st.session_state['navigate_to_login']= False    


# Define the navigation logic
def main():
    st.title("Welcome to the Virtual Library")
    if st.session_state['logged_in']:
        homePage.show_user_homepage(st.session_state['current_user'])
        print('current_user')
    
    #redirect to login page if user have an account
    if st.session_state['navigate_to_login']:
        login.login()

    # User is not logged in, show registration or login page
    if not st.session_state['logged_in']:
        # User has just registered, show the login page
        if st.session_state['just_registered']:
            login.login()
        else:
            # User is neither logged in nor just registered, show registration page
            register.register()
    
        
        
# Run the main function
if __name__ == '__main__':
    main()
