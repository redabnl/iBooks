import streamlit as st
import requests
from data.models import get_mongo_client
from data.book_model import  fetch_book_by_id
from model_training_user_interc import train_user_model, fetch_user_data, recommend_books
from PIL import Image
from io import BytesIO
# def show_library(user_pseudo):
#     user_pseudo = st.session_state.get('current_user', 'guest')
    
#     st.title(f"{user_pseudo}'s Library")
    
#     books_read = get_books_read_by_user(user_pseudo)
    
#     if not books_read:
#         st.write("You haven't read any books yet.")
#         return
    
#     st.markdown("<div class='book-container'>", unsafe_allow_html=True)
    
#     for book in books_read:
#         display_book_details(book)
            
#     st.markdown("</div>", unsafe_allow_html=True)
    
#     st.markdown("</div>", unsafe_allow_html=True)

        # with st.container():
        #     st.markdown("<div class='book'>", unsafe_allow_html=True)
        #     title = book.get('title', 'No Title Available')
        #     author = book.get('author', 'Unknown Author')
        #     published_year = book.get('published_year', 'Unknown Year')
        #     isbn = book.get('isbn', 'N/A')
        #     cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg" if isbn != 'N/A' else None

        #     if cover_url:
        #         st.image(cover_url, width=100, caption=title)
        #     else:
        #         st.write("No image found")
            
        #     st.image(cover_url, width=150)
        #     st.write(f"**Title:** {title}")
        #     st.write(f"**Author:** {author}")
        #     st.write(f"**First Published Year:** {published_year}")
        #     st.write(f"**ISBN:** {isbn}")
            
        #     st.write("### Reviews:")
        #     reviews = get_reviews_for_book(book['_id'])
        #     for review in reviews:
        #         st.write(f"- {review['user_pseudo']} rated {review['rating']} stars")
        #         st.write(f"  > {review['text']}")


# def show_library(user_pseudo):
#     user_pseudo = st.session_state['current_user']
    
#     st.title(f"{user_pseudo}'s Library")
    
#     books_read = get_books_read_by_user(user_pseudo)
    
#     if not books_read:
#         st.write("You haven't read any books yet.")
#         return
    
#     st.markdown("<div class='book-container'>", unsafe_allow_html=True)
    
#     for book in books_read:
#         display_book_details(book)
    
#     st.markdown("</div>", unsafe_allow_html=True)
    
def show_user_library():
    user_pseudo = st.session_state['current_user']
    read_books, user_reviews = fetch_user_data(user_pseudo)

    st.title("Your Library")
    for book_id in read_books:
        book = fetch_book_by_id(book_id)
        display_readBook_details(book)
        
        # st.markdown("### Reviews:")
        # for review in user_reviews:
        #     if review['book_id'] == book_id:
        #         st.write(f"{review['user_pseudo']}'s review :")
        #         st.write(review['text'])

    st.title("Recommended for You")
    recommended_books = recommend_books(user_pseudo)
    for book in recommended_books:
        display_readBook_details(book)  
    

# def show_custom_recom(user_pseudo):
#     user_pseudo = st.session_state['current_user']


#     ## train the user spec model
#     train_user_model(user_pseudo)
    
#     ## define candidate books
#     candidate_books = [book['_id'] for book in fetch_book_details([]) ]
    
    
#     recommendations = recommend_books(user_pseudo, candidate_books)
    
#     # Display recommendations
#     st.subheader("Recommended Books")
#     for recommendation in recommendations:
#         book = recommendation['book']
#         predicted_rating = recommendation['predicted_rating']
#         st.write(f"**Title:** {book['title']}")
#         st.write(f"**Predicted Rating:** {predicted_rating}")
#         st.write("---")

        # with st.container():
        #     st.markdown("<div class='book'>", unsafe_allow_html=True)
        #     title = book.get('title', 'No Title Available')
        #     author = book.get('author', 'Unknown Author')
        #     published_year = book.get('published_year', 'Unknown Year')
        #     isbn = book.get('isbn', 'N/A')
        #     cover_url = book.get('cover_url', 'images/default_book_cover.png')
            
        #     st.image(cover_url, width=150)
        #     st.write(f"**Title:** {title}")
        #     st.write(f"**Author:** {author}")
        #     st.write(f"**First Published Year:** {published_year}")
        #     st.write(f"**ISBN:** {isbn}")
            
        #     st.write("### Reviews:")
        #     reviews = get_reviews_for_book(book['_id'])
        #     for review in reviews:
        #         st.write(f"- {review['user_pseudo']} rated {review['rating']} stars")
        #         st.write(f"  > {review['text']}")
            
        #     st.markdown("</div>", unsafe_allow_html=True)
## GET THE BOOKS READ BY THE LOGED IN USER
def get_books_read_by_user(user_pseudo):
    with get_mongo_client() as client:
        db = client['ibooks']
        users_collection = db['users']
        user = users_collection.find_one({"pseudo": user_pseudo})
        if user:
            read_books_ids = user.get('already_read', [])
            books_collection = db['books']
            return list(books_collection.find({"_id": {"$in": read_books_ids}}))
        return []
    
## GET THE REVIEWS LEFT BY USERS FOR LOGGED USER'S READ BOOKS 
def get_reviews_for_book(book_id):
    with get_mongo_client() as client:
        db = client['ibooks']
        reviews_collection = db['reviews']
        return list(reviews_collection.find({"book_id": book_id}))

def display_readBook_details(book):
    with st.container():
        title = book.get('title', 'No Title Available')
        author = ' '.join(book.get('authors', ['Unknown Author']))
        published_year = book.get('first_publish_year', 'Unknown')
        isbn_list = book.get('isbn', [])
        isbn = isbn_list[0] if isbn_list else 'N/A'
        cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg" if isbn != 'N/A' else None
        ratings_average = book.get('ratings_average', 0)
        ratings_count = book.get('ratings_count', 0)
        already_read_count = book.get('already_read_count',0)
        

        # Check if cover URL is valid
        def is_valid_url(url):
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content))
                    return True
            except Exception as e :
                print(f"URL error {e}")
                return False
            return False

        if cover_url and is_valid_url(cover_url):
            st.image(cover_url, width=100)
        else:
            st.image('images/default_book_cover.png', width=100)

        st.write(f"**Title:** {title}")
        st.write(f"**Author:** {author}")
        st.write(f"**Published Year:** {published_year}")
        st.write(f"**ISBN:** {isbn}")
        st.write(f"**Average rating :** {ratings_average}")
        st.write(f"**Ratings count :** {ratings_count}")
        st.write(f"**Read by :** {already_read_count} for now ")
        

        if isbn != 'N/A':
            purchase_url = f"https://cheaper99.com/{isbn}"
            link_html = f'<a href="{purchase_url}" target="_blank">Buy this book</a>'
            st.markdown(link_html, unsafe_allow_html=True)
        else:
            st.write("No purchase link available.")
            
        st.write("### Reviews:")
        reviews = get_reviews_for_book(book['_id'])
        for review in reviews:
            st.write(f"- {review['user_pseudo']} rated this book {review['rating']} stars")
            st.write(f"  {review['user_pseudo']}'s review : \n > {review['text']}")
        st.markdown("</div>", unsafe_allow_html=True)
            

        st.write("-----------")  # A separator line for clarity
        

            
            
            
# displaying the books as cards with a link to an axternal website
def generate_card(title,authors ,description ):
    """Generate HTML content for a single book card."""
    card_html = f"""
    <div style="margin: 10px; float: left; width: 300px; border: 1px solid #ccc; border-radius: 5px; padding: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <h3>{title}</h3>
        <h4>{authors}</h4>   
        <p>{description}</p>
    </div>
    """
    return card_html

def show_books_as_cards(books_df):
    # Start of the HTML block for cards
    st.write("<div style='display: flex; flex-wrap: wrap;'>", unsafe_allow_html=True)
    
    # Generate a card for each book
    for _, row in books_df.iterrows():
        # Assuming you have columns titled 'Title', 'Author', and 'Description' in your DataFrame
        card_html = generate_card(
            title=row['Title'],
            authors=row['Authors'],
            description=row['Description'][:150] + "..."  # Limit description characters
        )
        st.markdown(card_html, unsafe_allow_html=True)
    
    # Close the HTML block
    # Example of a card layout for book details
        st.markdown(
            """
            <div class="card">
                <div class="card-title">Empires Ascendant: Time Frame 400 Bc-Ad 200</div>
                <div class="card-author">By Time-Life Books</div>
                <div class="card-description">examines the different cultures that were emerging between 400 bc and 200...</div>
            </div>
            <div class="card">
                <div class="card-title">The Holy Land (Lost Civilizations)</div>
                <div class="card-author">By Time-Life Books</div>
                <div class="card-description">looks at the history geography and ancient cultures of the holy land...</div>
            </div>
            """, unsafe_allow_html=True
        )
    
    
    
    
    
    
           
# def show_search_form(user_pseudo):
#     search_query = st.text_input("Search for a new book here!", key="search_query")
#     submit_search = st.button("search")
#     # user_pseudo = "poutit"
    
#     if submit_search and search_query:
#         search_results = search_openAPI_lib(search_query)
#         if search_results:
#             show_search_results(user_pseudo, search_results)
#         else:
#             st.error("No search results found or an error occurred during the search.")

# def search_openAPI_lib(search_query, limit=9, page=1):
#     search_url = f"https://openlibrary.org/search.json?q={search_query}&limit={limit}&page={page}"
#     response = requests.get(search_url)
#     if response.ok:
#         return response.json()
#     return None












# from data.models import get_mongo_client
# from frontE.homePage import display_book_details
# from frontE.homePage import show_books_as_cards
# import streamlit as st


# if 'current_user' not in st.session_state:
#     st.session_state['current_user'] = None

# #library function where user's favbooks gonna be displayed

            
            
            
# def main():
#     # Check login state
#     if st.session_state.get('logged_in', False):
#         show_library(pseudo=st.session_state['current_user'])  # Show the homepage if the user is logged in
#     else:
#         st.write("Please log in.")  # Or redirect them to the login page

# if __name__ == "__main__":
#     main()