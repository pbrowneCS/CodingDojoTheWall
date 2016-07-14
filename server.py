from flask import Flask, render_template, request, redirect, session, flash
from mysqlconnection import MySQLConnector
from flask.ext.bcrypt import Bcrypt
import re
NAME_REGEX = re.compile(r'^[a-zA-Z]*$')
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]*$')
CAPITAL_LETTER_REGEX = re.compile(r"[A-Z]")
NUMBER_REGEX = re.compile(r"\d")
SYMBOLS_REGEX =  re.compile(r'[!@#$%^&*]')
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = 'ThisIsSecret'
mysql = MySQLConnector(app, 'thewall')

@app.route('/')
def index():
	query = "SELECT * FROM users"
	emails = mysql.query_db(query)
	return render_template('index.html', allEmails = emails)


@app.route('/register', methods=['POST'])
def register():
	if len(request.form['userEmail']) < 1:
		flash("Email cannot be empty!")
		return redirect('/')
	elif not EMAIL_REGEX.match(request.form['userEmail']):
		flash("Invalid Email Address!")
		return redirect('/')
	if len(request.form['userPassword']) < 8:
		if len(request.form['userPassword']) < 1:
			flash("Password cannot be empty!")
			return redirect('/')
		else:
			flash("Password cannot be less than 8!")
			return redirect('/')
	if len(request.form['userPassword']) != len(request.form['userConfirm']):
		flash("Passwords must match identically!")
		return redirect('/')
	if not (CAPITAL_LETTER_REGEX.search(request.form['userPassword']) and NUMBER_REGEX.search(request.form['userPassword']) and SYMBOLS_REGEX.search(request.form['userPassword'])):
		flash("Password requires at least one capitalized letter/symbol/number!")
		return redirect('/')
	if len(request.form['userFirst']) < 1:
		flash("First Name cannot be empty!")
		return redirect('/')
	elif not NAME_REGEX.match(request.form['userFirst']):
		flash("Invalid First Name!")
		return redirect('/')
	if len(request.form['userLast']) < 1:
		flash("Last Name cannot be empty!")
		return redirect('/')
	elif not NAME_REGEX.match(request.form['userLast']):
		flash("Invalid Last Name!")
		return redirect('/')
	pw_hash = bcrypt.generate_password_hash(request.form['userPassword'])
	query_data = { 'userEmail': request.form['userEmail'], 'fName': request.form['userFirst'], 'lName': request.form['userLast'], 'pw_hash': pw_hash }
	insert_query = "INSERT INTO users (email, password, firstName, lastName, created_at, updated_at) VALUES (:userEmail, :pw_hash, :fName, :lName, NOW(), NOW())"
	friend = mysql.query_db(insert_query, query_data)
	return redirect('/wall')

@app.route('/login', methods=['POST'])
def login():
	if len(request.form['userEmail']) < 1:
		flash("Email cannot be empty!")
		return redirect('/')
	if len(request.form['userPassword']) < 1:
		flash("Password cannot be empty!")
		return redirect('/')
	inputEmail = request.form['userEmail']
	inputPassword = request.form['userPassword']
	login_query = "SELECT * FROM users WHERE email = :email LIMIT 1"
	query_data = { 'email': inputEmail }
	user = mysql.query_db(login_query, query_data)
	if not user:
		flash ("Email not found")
		return redirect('/')
	if bcrypt.check_password_hash(user[0]['password'], inputPassword):	
		session['id'] = user[0]['id']
		session['firstName'] = user[0]['firstName']
		session['lastName'] = user[0]['lastName']
		return redirect('/wall')
	else:
		flash("Invalid ID or PASSWORD!")
		return redirect('/')

@app.route('/wall')
def wall():
	message_query = "SELECT messages.id, messages.user_id, messages.message, users.firstName, users.lastName, messages.created_at FROM messages JOIN users ON messages.user_id = users.id"
	comment_query = "SELECT comments.users_id, comments.comment, comments.messages_id, comments.created_at, users.firstName, users.lastName from comments LEFT JOIN users on users.id = comments.users_id LEFT JOIN messages on messages.id = comments.users_id"
	messages = mysql.query_db(message_query)
	comments = mysql.query_db(comment_query)
	return render_template('wall.html', allMessages = messages, allComments = comments)

@app.route('/newMessage', methods=['POST'])
def newMessage():
	if len(request.form['newMessage']) < 1:
		flash("Message cannot be empty!")
		return redirect('/wall')
	if len(request.form['newMessage']) > 100:
		flash("Message cannot greater than 100 characters!")
		return redirect('/wall')
	query_data = {'currentSession': session['id'], 'userMessage': request.form['newMessage']}
	insert_query = "INSERT INTO messages (user_id, message, created_at, updated_at) VALUES (:currentSession, :userMessage, NOW(), NOW())"
	mysql.query_db(insert_query, query_data)
	return redirect('/wall')

@app.route('/newComment/<id>', methods=['POST'])
def newComment(id):
	if len(request.form['newComment']) < 1:
		flash("Comment cannot be empty!")
		return redirect('/wall')
	if len(request.form['newComment']) > 100:
		flash("Comment cannot greater than 100 characters!")
		return redirect('/wall')
	query_data = {'messageId': id, 'currentSession': session['id'], 'userComment': request.form['newComment']}
	insert_query = "INSERT INTO comments (messages_id, users_id, comment, created_at, updated_at) VALUES (:messageId, :currentSession, :userComment, NOW(), NOW())"
	mysql.query_db(insert_query, query_data)
	return redirect('/wall')

@app.route('/logout', methods=['POST'])
def logout():
	session.clear()
	return redirect('/')
app.run(debug=True)