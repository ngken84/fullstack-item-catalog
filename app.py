from flask import Flask, render_template
from flask import session as login_session
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, CategorySubItem
import random
import string


engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

def generate_forgery_token():
	""" generates and returns a 32 character string of letters and numbers to
	be used as an anti forgery token"""
	return ''.join(random.choice(string.ascii_uppercase + string.digits)
		for x in range(32))


@app.route('/')
def MainPage():
	token = generate_forgery_token()
	is_logged_in = 'credentials' in login_session
	return render_template('index.html', logged_in=is_logged_in)


if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0', port=5000)