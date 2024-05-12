import streamlit as st

from data.models import create_user
from streamlit import session_state


# def create_user(username, password):
#     
#     return True


def register():
    with st.container():
        st.write("CREATE A NEW USER")
        
        #registration form
        with st.form(key='register_form'):
            pseudo = st.text_input("choose a pseudo")
            pwd = st.text_input("create a password", type="password")
            password_confirmation = st.text_input("Confirm your password", type="password")
            submit_btn = st.form_submit_button(label="Register")
            browse_btn = st.form_submit_button(label="just browsing")
            loginP_btn = st.form_submit_button(label="already have an account ")
            
            if loginP_btn:
                st.session_state['navigate_to_login'] = True
                st.rerun()
            
            if submit_btn:
                if pwd != password_confirmation:
                    st.error("passwords do not match !")
                    return
                
                if create_user(pseudo, pwd):
                    st.success("account created succesfully")
                    ## session state var 
                    st.session_state['just_registered'] = True
                    st.rerun()
                    # st.experimental_rerun()
                    
                else: st.error("Registration can't be done")
                
                
if __name__== "__main__":
    register()