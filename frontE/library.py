from data.models import get_mongo_client
from frontE.homePage import display_book_details
import streamlit as st


if 'current_user' not in st.session_state:
    st.session_state['current_user'] = None

#library function where user's favbooks gonna be displayed
def show_library(user_pseudo = st.session_state['current_user']):
    with get_mongo_client() as client:
        db = client['ibooks']
        users_collection = db['users']
        books_collection = db['books']

        user_doc = users_collection.find_one({'pseudo': user_pseudo})
        fav_books_ids = user_doc.get('favBooks', [])

        # Fetch the books' details using their ObjectIds
        fav_books = books_collection.find({'_id': {'$in': fav_books_ids}}) if fav_books_ids else []
        

        for book in fav_books:
            book_details = {
                        'title': book.get('title'),
                        'author': book.get('author'),
                        'isbn': book.get('ISBN'),
                        'published_year': book.get('first_publish_year'),
                        'cover_url': book.get('cover_url'),
                        'reviews' : []
                    }
            
            # display_book_details(book)
            print(book_details)
            st.write("-----------")
            
        if not fav_books:
            st.write('No favorites boooks added yet. Here is some you can like : ')