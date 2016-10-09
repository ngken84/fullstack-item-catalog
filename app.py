from flask import Flask, render_template, make_response, request
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


def generate_forgery_token():
	""" generates and returns a 32 character string of letters and numbers to
	be used as an anti forgery token"""
	return ''.join(random.choice(string.ascii_uppercase + string.digits)
		for x in range(32))


@app.route('/')
def MainPage():
	token = generate_forgery_token()
	login_session['state'] = token
	is_logged_in = 'credentials' in login_session
	return render_template('index.html',
							logged_in=is_logged_in,
							client_id=CLIENT_ID,
							forgery_token=token)

@app.route('/gconnect', methods=['POST'])
def GoogleConnect():
	"""Method called that in the authorization path for signing in using google
	plus"""
	# Ensure that the state token matches to prevent cross scripting attacks
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	code = request.data
	# Upgrade authorization cod into credentials object
	try:
		oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
		oauth_flow.redirect_uri = 'postmessage'
		credentials = oauth_flow.step2_exchange(code)
	except FlowExchangeError:
		response = make_response(json.dumps(
			'Failed to upgrade the authorization code'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	access_token = credentials.access_token
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
		% access_token)
	h = httplib2.Http()
	result = json.loads(h.request(url, 'GET')[1])
	# If there was an error in the access token info, abort
	if result.get('error') is not None:
		response = make_response(json.dumps(result.get('error')), 50)
		response.headers['Content-Type'] = 'application/json'
		return response
	gplus_id = credentials.id_token['sub']
	# Verify that the access token is for the intended user
	if result['user_id'] != gplus_id:
		response = make_response(
			json.dumps("Token's user ID doesn't match given user ID."), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	# Verify that the access token is valid for this app
	if result['issued_to'] != CLIENT_ID:
		response = make_response(
			json.dumps("Token's client ID does not match app!"), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	stored_credentials = login_session.get('credentials')
	stored_gplus_id = login_session.get('gplus_id')
	# Check to see if the user is already logged in
	if stored_credentials is not None and gplus_id == stored_gplus_id:
		response = make_response(
			json.dumps('Current user is already connected.'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response

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

	response = make_response(json.dumps('Success'), 200)
	response.headers['Content-Type'] = 'application/json'
	return response






app.secret_key = "A980KJSasdkc9834KAXI9dfm32198D98cs8MDF0"

if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0', port=5000)