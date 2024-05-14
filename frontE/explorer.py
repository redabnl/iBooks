import streamlit as st 
from machineL import load_and_prepare_data, recommend_books
from frontE.homePage import show_books_as_cards



def show_explorer_page():
    pseudo = st.session_state['current_user']
    
    data, tfidf_matrix, tfidf_vectorizer = load_and_prepare_data('data/dataSetCleaned.csv')

    st.write("Welcome to the explorer page.")
    user_description = st.text_input("Describe the book you're interested in:", '')

    if st.button("Find Books", key='explorer_search_btn'):
        recommended_books = recommend_books(user_description, data, tfidf_vectorizer, tfidf_matrix)
        if recommended_books.empty:
            st.error("No books found. Please try again.")
        else:
            print(recommended_books.columns)
            st.write(f"here's our recommensations for : {pseudo}")
            show_books_as_cards(recommended_books)


# def main():
#     # Check login state
#     if st.session_state.get('logged_in', False):
#         show_explorer_page()  
#     else:
#         st.write("Please log in.")  # Or redirect them to the login page

# if __name__ == "__main__":
#     main()