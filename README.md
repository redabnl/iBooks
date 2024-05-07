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
