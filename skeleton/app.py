######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'root'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register/error", methods=['GET'])
def registererror():
	return render_template('register.html')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password) VALUES ('{0}', '{1}')".format(email, password)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		return flask.redirect(flask.url_for('registererror'))

def getUsersPhotos(email):
	cursor = conn.cursor()
	cursor.execute("""
	SELECT 
		data, photo_id, caption, u.user_id
	FROM
		users u,
		photos p
	WHERE
		u.user_id = p.user_id
			AND u.email = '{0}'
	""".format(email))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getAllPhotos():
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id, caption FROM photos")
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def getUsersFriends(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT U.first_name, U.last_name FROM Users as U, Friends as F WHERE U.user_id = (SELECT F.user_id2 WHERE F.user_id1 = '{0}')".format(uid))
	return cursor.fetchall()

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	print(flask_login.current_user.id)
	user_photos = getUsersPhotos(flask_login.current_user.id)
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile", photos=user_photos,base64=base64)

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		photo_data =imgfile.read()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO photos (data, user_id, caption, albums_id) VALUES (%s, %s, %s, %s)''' ,(photo_data,uid, caption,1))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid),base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')
#end photo uploading code


@app.route('/search', methods=['GET', 'POST'])
@flask_login.login_required
def search():
    if request.method == "POST":
        friendvar = request.form['friend_ser']
        friendvar = friendvar.split(" ", 1)
        cursor.execute("SELECT U.first_name, U.last_name, U.email FROM Users as U WHERE U.first_name LIKE %s OR U.last_name LIKE %s", (friendvar[0], friendvar[0]))
        conn.commit()
        data = cursor.fetchall()
        # all in the search box will return all the tuples
        #if len(data) == 0 and book == 'all': 
        #    cursor.execute("SELECT name, author from Book")
        #    conn.commit()
        #    data = cursor.fetchall()
        #return render_template('hello.html', data=findFriends)
        return render_template('search.html', findFriendData = data)
    return render_template('search.html')

@app.route('/friend', methods=['POST'])
@flask_login.login_required
def friend():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	name_last = request.form.get('last')
	name_first = request.form.get('last')
	#cursor.execute("SELECT U.first_name, U.last_name, U.email FROM Users as U WHERE U.first_name LIKE %s OR U.last_name LIKE %s", (friendvar[0], friendvar[0]))
    #conn.commit()

	print("test: %s \n",name_last)
	print(name_last)
	return render_template('hello.html', name=flask_login.current_user.id, message="Friend Added", friends=getUsersFriends(uid))


@app.route("/deletePhoto", methods=['POST'])
@flask_login.login_required
def deletePhoto():
	photoid = request.args.get('photo_id')
	cursor = conn.cursor()
	cursor.execute("DELETE FROM photos WHERE photo_id = {0};".format(photoid))
	user_photos = getUsersPhotos(flask_login.current_user.id)
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile", photos=user_photos,base64=base64)

#default page
@app.route("/", methods=['GET'])
def hello():
	all_photos = getAllPhotos()
	return render_template('hello.html', message='Welcome to Photoshare', photos=all_photos,base64=base64)


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
