import streamlit as st
from data.models import login_user, get_user_details

def login():
    with st.container():
        st.write("Please login ")
        # login for 
        with st.form(key='login_form'):
            user_pseudo = st.text_input("Pseudo")
            pwd = st.text_input("PWD", type="password")
            submit_button = st.form_submit_button(label='Login')

            # submitt btn function
            if submit_button:
                if login_user(user_pseudo,pwd):
                    # set the session state for the user logged in 
                    st.session_state['logged_in'] = True
                    st.session_state['current_user'] = user_pseudo
                    print("Logged in:", st.session_state['logged_in'])
                    print("Current User:", st.session_state['current_user'])
                
                    st.session_state['user_id']= get_user_details(user_pseudo)    
                    st.success("You have successfully logged in!")
                    st.session_state['current_page'] = 'homePage'
                    st.rerun()
                else:
                    st.session_state['logged_in'] = False
                    st.error("Incorrect username or password")
                    
if __name__ == "__main__":
    login()