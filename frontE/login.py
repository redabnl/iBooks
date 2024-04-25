import streamlit as st
from data.models import login_user, get_user_details

def login():
    with st.container():
        st.write("Please login ")
        # Create the login form
        with st.form(key='login_form'):
            pseudo = st.text_input("Pseudo")
            pwd = st.text_input("PWD", type="password")
            submit_button = st.form_submit_button(label='Login')

            # When the user hits the submit button
            if submit_button:
                if login_user(pseudo,pwd):
                    # Set the session state to indicate that the user is logged in
                    st.session_state['logged_in'] = True
                    st.session_state['current_user'] = pseudo
                    print("Logged in:", st.session_state['logged_in'])
                    print("Current User:", st.session_state['current_user'])
                
                    st.session_state['user_id']= get_user_details(pseudo)    
                    st.success("You have successfully logged in!")
                    st.session_state['current_page'] = 'homePage'
                    st.rerun()
                else:
                    st.session_state['logged_in'] = False
                    st.error("Incorrect username or password")
                    
if __name__ == "__main__":
    login()