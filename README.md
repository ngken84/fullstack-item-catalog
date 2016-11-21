# fullstack-item-catalog

## Project Description
An item catalog created for Udacity Full Stack Nanodegreee. It allows users:
- to create, edit or delete categories and items within categories
- sign into Google Plus
Created by Ken Ng

## Requirements to run the project
- Python 2.7 installed
- A Google Account

## How to run the project
1. Download zip file and extract it into a directory
2. Create a Google OAuth credentials file. 
  1. Log into you Google account
  2. Go to http://console.developers.google.com
  3. Select APIs & Auth
  4. Select Credentials
  5. Press Create new Client ID
  6. Select Web Application
  7. Configure your consent screen
  8. Click Create ID
  9. Click Javascript Origins
  10. Add http://localhost:5000 or where ever you will be hosting your site
  11. Click Update.
  12. Download the JSON file and save it to the project directory as client_secrets.json
3. Open the command line and navigate to the project directory
4. Run "python database_setup.py"
5. Run "python app.py"

## Potential Future Features
- more data for items
  * price
- allow users to purchase items
- add a shopping cart
