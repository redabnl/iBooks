virtual library with open Library API instegration
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
