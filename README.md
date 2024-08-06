<!-- virtual library with open Library API instegration -->

## Virtual Library with Open Library API Integration

-- Table of Contents

1. Overview
2. Features
3. Installation
4. Usage
5. Database Structure
6. Use Cases
7. Recommendations System
8. Problems and Solutions
9. Future Improvements
10. Contributing
11. License
12. Contact

## Overview

This application is a virtual library that integrates with the Open Library API. It allows users to create accounts, log in, search for books, add books to their favorites collection, mark books as already read, leave reviews, and receive personalized book recommendations based on their interaction data.

## Features

User Authentication: Register, log in, and log out.
Book Search: Search for books using the Open Library API and view detailed information.
Favorites Collection: Add books to a favorites collection.
Read Books Management: Mark books as already read and view them in the library.
Reviews: Leave and view reviews for books.
Recommendations: Receive personalized book recommendations based on reading history and reviews.

## Installation

-- Prerequisites
Python 3.x
MongoDB
Flask  
Open Library API Key
-- Installation Steps

1. Clone the repository: `git clone https://github.com/redabnl/ibooks.git`
2. Install the required packages: `pip install -r requirements.txt`
3. Set up the MongoDB database: `mongodb` (start the MongoDB server)
4. Create a new file named `config.py` and add your Open Library API key: `
   API_KEY = 'ask for it lol'

## Usage

-- Home Page
Search for books using keywords.
View book details including title, author, published year, cover image, average rating, and summary.
Add books to your favorites collection.
Mark books as already read.
Leave reviews and ratings for books.

-- Library
View books added to your favorites collection.
View books marked as already read.
Receive personalized book recommendations.

-- Explorer page
The application uses user interaction data to provide personalized book recommendations.

## Recommendations:

Based on user interaction data (read books and reviews), the system provides personalized book recommendations.
Recommendations are generated using book subjects as features for the recommendation model.

## Database Structure

The database consists of three collections:

1. **users**: Stores user information, including username, password, and favorites collection.
   \_id: ObjectId
   pseudo: String
   pwd: String (hashed password)
   email: String
   role: String (user/admin)
   isPrivate: Boolean
   account_creation_date: Date
   already_read: Array of ObjectIds (Book references)
   read_books: Array of ObjectIds (Book references)
   user_reviews: Array of ObjectIds (Review references)

2. **Books**: stores books searched by users to enrich the databse including isbn, cover url, ratings details ...
   \_id: ObjectId
   isbn: String
   title: String
   author: String
   published_year: String
   summary: String
   cover_url: String
   ratings_average: Number
   ratings_count: Number
   already_read_count: Number

3. **Reviews**: stores reviews details including user leaving the review, the book reviewed, and text review (will be used for user's person. recommendations).
   \_id: ObjectId
   user_pseudo: String
   book_id: ObjectId (Reference to Book)
   rating: Number
   text: String
   date: Date

## Use Cases :

1. **User Registration**:

- Users can register by providing a pseudo, password, and email.
- Users can log in using their pseudo and password.
- Session management ensures users stay logged in across sessions.
- Users can log out.

2. **Book Search and Add to Favorites**:

- Users can search for books by title, author, or ISBN.
- Users can view book details, including title, author, published year, summary, and cover URL
- Users can add books to their favorites/read collection.
- Users can view their favorites/read collection.

3. **Mark as Already Read and Leave Reviews**:

- Users can mark books as already read.
- Users can leave reviews and ratings for books.
- Reviews are displayed for each book.

## Personalized Recommendations :

- Users receive personalized book recommendations based on their reading history and preferences.
- Recommendations are generated using a collaborative filtering algorithm.

## Problems and Solutions :

1. **Scalability**:

- Solution: Use a NoSQL database like MongoDB to handle large amounts of data and scale horizontally.

2. **Error Handling in Search and Display**:

Problem: Handling cases where the book details are incomplete.
Solution: Default cover images and placeholder text for missing details were used.

3. **User Session Management:**

- Problem: Managing user sessions for login/logout.
- Solution: Implemented session states to track user login status and provided a logout function.

4. **Recommendations System:**

- Problem: Generating meaningful book recommendations based on user data.
- Solution: Utilized book subjects as features for the recommendation model to predict similar books based on user interaction data.

5. **API Integration Issues:**

- Problem: Fetching book details using various identifiers (ISBN, book ID).
- Solution: Implemented a robust function to fetch book subjects from the Open Library API and utilized them for recommendations.

## Future Improvements :

- Implement more sophisticated machine learning models for recommendations.
- Enhance user interface with CSS for a better user experience.
- Integrate additional book information sources to enrich the database.

## FIRST APPLICATION'S GLANCE (:

# =========================================================================================

So far, the user is able to create an account, login and search for books.
After the search is done, the user can add the book he searched for to his favorites collection and/or leave a review about.

the favorite books and reviews will be helpfull in training the model the predict new books for the user based on his interaction with books

## Home Page

search book form that fetches data from open library search APi
-> each search function helps providing more data to the table so the model is well trained on personalized book predictions in the futur
-> the user can add a book to his favorites collection and if the book is not already in the collections it adds it.
-> the user can also leave a review about a specific book wich will be helpful on training our model for more accurate predictions based on the user preferences and interactions

## Library

Here the user can see the books he added to his favorites collection

## New Predictions

-> this is the part where we help the users find new books to read based on the description of the preferences
-> using the 'dataSetCleaned.csv' for now to train the model on predictions based on the book's description.

======================================================
-1 SEARCH FEATURE USING OPEN LIBRARY SEARCH API :
-function to query the open API with a given search tearm with similar books too that the user may be interested in.
-parse the response to extract the required book's informations and add a review array
-Display the result for the user

-2 MANAGE USER FAVORITES'S BOOKS
-Update "user" collection model to iinclude a "favBooks"attribute that stores an array of book Objects
-Implement functions to allow users to add or remove books from favs collection

3- ENABLE USERS TO LEAVE REVIEWS ABOUT BOOKS :
-Create a "reviews" collection where isers can store reviews for books
-each review references the books informations and the iser who wrote the review
