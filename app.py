from flask import Flask, render_template, make_response, request, redirect
from flask import session as login_session
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, CategorySubItem
import random
import string
import json
import httplib2
import requests
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

CLIENT_ID = json.loads(
	open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

def get_all_categories():
	"""Retrieves all categories in database"""
	return session.query(Category).all()

def get_category_by_id(id):
	"""Retrieves a category by id"""
	return session.query(Category).filter(id==id).first()

def get_user_details():
	""" Retrieves the user's details if they are logged in"""
	is_logged_in = 'credentials' in login_session
	if is_logged_in:
		return is_logged_in, login_session['name'], login_session['picture']
	return is_logged_in, None, None

def generate_forgery_token():
	""" generates and returns a 32 character string of letters and numbers to
	be used as an anti forgery token"""
	token = ''.join(random.choice(string.ascii_uppercase + string.digits)
		for x in range(32))
	login_session['state'] = token
	return token


def generate_json_response(text, code):
	""" generates and returns a json response with text and code"""
	response = make_response(json.dumps(text), code)
	response.headers['Content-Type'] = 'application/json'
	return response


@app.route('/')
def MainPage():
	token = generate_forgery_token()
	is_logged_in, name, picture = get_user_details()
	categories = get_all_categories()
	return render_template('index.html',
							picture=picture,
							name=name,
							logged_in=is_logged_in,
							client_id=CLIENT_ID,
							categories=categories,
							forgery_token=token)

@app.route('/gconnect', methods=['POST'])
def GoogleConnect():
	"""Method called that in the authorization path for signing in using google
	plus"""
	# Ensure that the state token matches to prevent cross scripting attacks
	if request.args.get('state') != login_session['state']:
		return generate_json_response('Invalid state', 401)
	code = request.data
	# Upgrade authorization cod into credentials object
	try:
		oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
		oauth_flow.redirect_uri = 'postmessage'
		credentials = oauth_flow.step2_exchange(code)
	except FlowExchangeError:
		return generate_json_response(
			'Failed to upgrade the authorization code', 401)
	access_token = credentials.access_token
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
		% access_token)
	h = httplib2.Http()
	result = json.loads(h.request(url, 'GET')[1])
	# If there was an error in the access token info, abort
	if result.get('error') is not None:
		return generate_json_response(result.get('error'), 50)
	gplus_id = credentials.id_token['sub']
	# Verify that the access token is for the intended user
	if result['user_id'] != gplus_id:
		return generate_json_response(
			"Token's user ID doesn't match given user ID", 401)
	# Verify that the access token is valid for this app
	if result['issued_to'] != CLIENT_ID:
		return generate_json_response("Token's client ID does not match app!",
			401)
	stored_credentials = login_session.get('credentials')
	stored_gplus_id = login_session.get('gplus_id')
	# Check to see if the user is already logged in
	if stored_credentials is not None and gplus_id == stored_gplus_id:
		return generate_json_response('Current user is already connected', 200)

	# logs the user in
	login_session['credentials'] = credentials.access_token
	login_session['gplus_id'] = gplus_id

	# get some more info from the server about the user
	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
	params = {'access_token': credentials.access_token, 'alt': 'json'}
	answer = requests.get(userinfo_url, params=params)
	data = json.loads(answer.text)

	login_session['username'] = data["name"]
	login_session['picture'] = data["picture"]
	login_session['email'] = data["email"]
	login_session['name'] = data["name"]

	user = session.query(User).filter(User.email==data["email"],
		User.service=='Google').first()
	if not user:
		new_user = User(email=data['email'], service='Google')
		session.add(new_user)
		session.commit()
		login_session['id'] = new_user.id
	else:
		login_session['id'] = user.id
	return generate_json_response('Success', 200)


@app.route("/gdisconnect")
def GoogleDisconnect():
	"""Method called to disconnect from Google Plus"""
	# Only disconnect if the user is logged in
	if 'credentials' not in login_session:
		return generate_json_response('Current user not connected.', 401)
	url = ('https://accounts.google.com/o/oauth2/revoke?token=%s'
		% login_session['credentials'])
	h = httplib2.Http()
	result = h.request(url, 'GET')[0]
	if result['status'] == '200':
		del login_session['credentials']
		del login_session['gplus_id']
		del login_session['username']
		del login_session['email']
		del login_session['picture']
		del login_session['name']
		return generate_json_response('Successfully disconnected', 200)
	else:
		return generate_json_response('Failed to revoke token for given user.',
			400)


@app.route("/newcategory", methods=['GET', 'POST'])
def NewCategory():
	if 'credentials' not in login_session:
		return redirect('/', 302)
	else:
		if request.method == 'GET':
			return render_template('newcategory.html',
								picture=login_session['picture'],
								name=login_session['name'],
								logged_in=True,
								client_id=CLIENT_ID,
								category_name='',
								category_description='',
								name_error=None)
		else:
			name = request.form['categoryname']
			desc = request.form['description']
			if not name:
				return render_template('newcategory.html',
								picture=login_session['picture'],
								name=login_session['name'],
								logged_in=True,
								client_id=CLIENT_ID,
								category_name='',
								category_description=desc,
								name_error='Please enter a name.')
			existing_cat = (session.query(Category)
				.filter(Category.name==name).first())
			if len(name) > 40:
				return render_template('newcategory.html',
								picture=login_session['picture'],
								name=login_session['name'],
								logged_in=True,
								client_id=CLIENT_ID,
								category_name=name,
								category_description=desc,
								name_error=
									'Category name must be under 40 characters')
			if existing_cat:
				return render_template('newcategory.html',
								picture=login_session['picture'],
								name=login_session['name'],
								logged_in=True,
								client_id=CLIENT_ID,
								category_name=name,
								category_description=desc,
								name_error='Category already exists')
			new_category = Category(name=name,
									description=desc,
									user_id=login_session['id'])
			session.add(new_category)
			session.commit()
			return redirect('/', 302)


@app.route('/category/<int:category_id>')
def CategoryPage(category_id):
	category = get_category_by_id(category_id)
	if category:
		is_logged_in, name, picture = get_user_details()
		categories = get_all_categories()
		return render_template('category.html',
								client_id=CLIENT_ID,
								picture=picture,
								name=name,
								forgery_token=generate_forgery_token(),
								logged_in=is_logged_in,
								curr_category=category,
								categories=categories)
	return redirect('/', 302)

app.secret_key = "A980KJSasdkc9834KAXI9dfm32198D98cs8MDF0"

if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0', port=5000)