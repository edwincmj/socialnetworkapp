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

#for date
import datetime

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

def getTagnames():
	cursor = conn.cursor()
	cursor.execute("""
	SELECT 
    *
	FROM
		tags t,
		tagged tg
	WHERE
		t.tag_id = tg.tag_id;
	""")
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getAllPhotos():
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id, caption FROM photos")
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def getUserIdFromPhoto(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Photos WHERE photo_id = '{0}'".format(pid))
	return cursor.fetchone()[0]

def getUsersFriends(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT U.first_name, U.last_name FROM Users as U, Friends as F WHERE U.user_id = (SELECT F.user_id2 WHERE F.user_id1 = '{0}')".format(uid))
	return cursor.fetchall()

#def getTopUsers():
#	cursor = conn.cursor()
#	cursor.execute("SELECT U.first_name, U.last_name FROM,  Users as U, Friends as F WHERE U.user_id = (SELECT F.user_id2 WHERE F.user_id1 = '{0}')".format(uid))
#	return cursor.fetchall()

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
	#print(flask_login.current_user.id)
	tags = getTagnames()
	user_photos = getUsersPhotos(flask_login.current_user.id)
	photoids = [lis[1] for lis in user_photos]
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile", photos=user_photos, comments=getComment(photoids), tags=tags, photoLikes=getLikes(photoids),topUsers=topUsers() ,base64=base64)

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
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == "POST":
		friendvar = request.form['friend_ser']
		friendvar = friendvar.split(" ")

		cursor.execute("SELECT U.first_name, U.last_name, U.user_id FROM Users as U WHERE U.first_name LIKE %s OR U.last_name LIKE %s", (friendvar[0], friendvar[0]))
		data = cursor.fetchall()
		if(len(friendvar) > 1):
			cursor.execute("SELECT U.first_name, U.last_name, U.user_id FROM Users as U WHERE U.last_name LIKE %s", friendvar[1])
			data = data + cursor.fetchall()
			print(data)

		conn.commit()
		return render_template('search.html', findFriendData = data)
	return render_template('search.html', recommendFriends = recommendFriends(uid))

@app.route('/friend', methods=['POST'])
@flask_login.login_required
def friend():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	friend_uid = request.form.get('fuid')
	cursor = conn.cursor()
	
	if (cursor.execute("SELECT user_id1  FROM Friends WHERE user_id1 = '{0}' AND user_id2 = '{1}'".format(uid, friend_uid))):
		return render_template('search.html')
	cursor.execute("INSERT INTO Friends (user_id1, user_id2) VALUES ('{0}', '{1}')".format(uid, friend_uid))
	conn.commit()
	cursor.execute("INSERT INTO Friends (user_id1, user_id2) VALUES ('{0}', '{1}')".format(friend_uid, uid))
	conn.commit()
	return render_template('hello.html', name=flask_login.current_user.id, message="Friend Added", friends=getUsersFriends(uid))


@app.route("/deletePhoto", methods=['POST'])
@flask_login.login_required
def deletePhoto():
	photoid = request.args.get('photo_id')
	cursor = conn.cursor()
	cursor.execute("DELETE FROM photos WHERE photo_id = {0};".format(photoid))
	user_photos = getUsersPhotos(flask_login.current_user.id)
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile", photos=user_photos,base64=base64)


@app.route('/addtag',methods=['POST'])
@flask_login.login_required
def addtag():
	cursor = conn.cursor()
	tag = request.form.get('tag')
	photo = request.form.get('photo')
	print("tag ",tag)
	print("photo ",photo)
	all_tags = getTagnames()
	if (tag) not in all_tags:
		print("yes")
		cursor.execute("""
		INSERT INTO tags (name)
		VALUES ('{0}');
		""".format(tag))
		conn.commit()
		print(cursor.fetchall())
	cursor.execute("""
	SELECT 
		tag_id
	FROM
		tags
	WHERE
		name = '{0}';
	""".format(tag))
	tag_id=cursor.fetchall()[0][0]
	print("tag_id ",tag_id)
	cursor.execute("""
	insert into tagged VALUES ({0},{1});
	""".format(photo,tag_id))	
	conn.commit()
	print(cursor.fetchall())
	return render_template('hello.html')

@app.route('/getUserPhotosByTagName')
@flask_login.login_required
def getUserPhotosByTagName():
	tagname = request.args.get('tagname')
	email = flask_login.current_user.id
	cursor = conn.cursor()
	cursor.execute("""
	SELECT 
		*
	FROM
		photos p,
		tagged tg,
		tags t
	WHERE
		p.photo_id = tg.photo_id
			AND tg.tag_id = t.tag_id
			AND t.name = '{0}'
			AND user_id = (SELECT 
				user_id
			FROM
				users
			WHERE
				email = '{1}')
	""".format(tagname,email))	
	return cursor.fetchall()

@app.route('/getPhotosByTagName', methods=['POST'])
@flask_login.login_required
def getPhotosByTagName():
	tagname = request.form.get('tagname')
	cursor = conn.cursor()
	cursor.execute("""
	SELECT 
		p.data,p.caption
	FROM
		photos p,
		tagged tg,
		tags t
	WHERE
		p.photo_id = tg.photo_id
			AND tg.tag_id = t.tag_id
			AND t.name = '{0}'
	""".format(tagname))	
	tagphotos = cursor.fetchall()
	return render_template('hello.html', message='Photos with '+tagname, tagphotos=tagphotos, base64=base64)


@app.route('/mostpopulartags')
@flask_login.login_required
def mostpopulartags():
	cursor = conn.cursor()
	cursor.execute("""
	SELECT 
		*
	FROM
		tags t,
		tagged tg
	WHERE
		t.tag_id = tg.tag_id
	GROUP BY tg.tag_id
	ORDER BY COUNT(*) DESC
	""")	
	return cursor.fetchall()

@app.route('/photosearch', methods=['POST'])
@flask_login.login_required
def photoSearch():
	cursor = conn.cursor()
	tags = request.form.get('tags').split(' ')
	query = """
	SELECT 
    	p.photo_id, p.caption, p.data
	FROM
		photos p,
		tagged tg,
		tags t
	WHERE
		p.photo_id = tg.photo_id
			AND tg.tag_id = t.tag_id
			AND (t.name='{0}'
	""".format(tags[0])
	for i in range(1,len(tags)):
		query += "OR t.name='"+tags[i]+"' "
	query+=');'
	print(query)
	cursor.execute(query)
	return cursor.fetchall()


#Comments
@app.route("/leaveComment", methods=['POST', 'GET'])
def leaveComment():
	if request.method == 'POST':
		pid = request.form.get('photo_id')
		#print(pid)
		pid = int(pid)
		text = request.form.get('comment_text')
		date = datetime.date.today()
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cid = genCommentIdFromPhoto(pid)
		photo_user = getUserIdFromPhoto(pid)

		if photo_user is uid:
			return flask.redirect(flask.url_for('hello'))

		#print(cid, uid, pid, text, date)
		cursor.execute("INSERT INTO Comments (comment_id, user_id, photo_id,text , date) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}')".format(cid, uid, pid, text, date))
		conn.commit()
		return flask.redirect(flask.url_for('hello'))
	return flask.redirect(flask.url_for('hello'))

def genCommentIdFromPhoto(pid):
	cursor = conn.cursor()
	#if cursor.execute("SELECT COALESCE(MAX(C.comment_id), 0)  FROM Photos P, Comments C WHERE C.photo_id = '{0}'".format(pid)):
	if cursor.execute("SELECT COALESCE(MAX(C.comment_id), 0)  FROM Comments C"):
		data = cursor.fetchone()[0]
		#print(data)
		return int(data) + 1
	return 0

def getComment(pid):
	cursor = conn.cursor()
	C = []
	for ind_pid in pid:
		cursor.execute("SELECT C.text, C.date, C.comment_id, C.user_id, U.first_name, U.last_name FROM Comments C inner join Users U on C.user_id = U.user_id WHERE C.photo_id = '{0}'".format(ind_pid))
		data = []
		data = cursor.fetchall()
		C.append(data)
	#print(C)
	return C


@app.route("/searchComment", methods=['POST', 'GET'])
def searchComment():
	if request.method == 'POST':
		#pid = request.form.get('photo_id')
		#print(pid)
		#pid = int(pid)
		text = request.form.get('comment_text_search')
		#date = datetime.date.today()
		#uid = getUserIdFromEmail(flask_login.current_user.id)
		#cid = genCommentIdFromPhoto(pid)
		#photo_user = getUserIdFromPhoto(pid)

		#if photo_user is uid:
		#	return flask.redirect(flask.url_for('hello'))

		print(text)
		data = []
		cursor.execute("SELECT C.text, U.first_name, U.last_name, COUNT(C.text) FROM Comments C, Users U WHERE C.user_id = U.user_id and C.text LIKE %s Group By U.user_id ORDER BY COUNT(*) DESC", text)
		conn.commit()
		data.append(cursor.fetchall())
		print(data)
		return render_template('search.html', searchComments = data)
	return flask.redirect(flask.url_for('search.html'))



#Likes
@app.route("/like", methods=['POST', 'GET'])
def addLike():
	if request.method == 'POST':
		pid = request.form.get('photo_id')
		pid = int(pid)
		uid = getUserIdFromEmail(flask_login.current_user.id)

		if cursor.execute("SELECT user_id FROM Likes L WHERE user_id = '{0}' AND photo_id = '{1}'".format(uid, pid)):
			return flask.redirect(flask.url_for('hello'))

		cursor.execute("INSERT INTO Likes (photo_id, user_id) VALUES ('{0}', '{1}')".format(pid, uid))
		conn.commit()
		return flask.redirect(flask.url_for('hello'))
	return flask.redirect(flask.url_for('hello'))

def getLikes(pid):
	cursor = conn.cursor()
	C = []
	for ind_pid in pid:
		data = []
		cursor.execute("SELECT COUNT(L.user_id) FROM Likes L WHERE L.photo_id = '{0}'".format(ind_pid))
		data.append(cursor.fetchall()[0][0])
		#print(data)

		cursor.execute("SELECT U.first_name, U.last_name FROM Likes L inner join Users U on L.user_id = U.user_id WHERE L.photo_id = '{0}'".format(ind_pid))
		
		data_names = [item for item in cursor.fetchall()]
		#print(data_test)
		data.append(data_names)
		#print(data)
		C.append(data)
	#print(C)
	return C

def getUserIdFromComment(cid):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Comments WHERE comment_id = '{0}'".format(cid))
	return cursor.fetchone()[0]

#Popular users
def topUsers():
	cursor = conn.cursor()
	cursor.execute("SELECT NU.first_name, NU.last_name , SUM(T.num_photos) FROM Users NU , (SELECT U.user_id, COUNT(P.photo_id) AS num_photos FROM Users U, Photos P WHERE P.user_id = U.user_id GROUP BY U.user_id UNION (SELECT U.user_id, COUNT(C.comment_id) AS num_photos FROM Users U, Comments C WHERE C.user_id = U.user_id GROUP BY U.user_id)) AS T WHERE T.user_id = NU.user_id GROUP BY T.user_id ORDER BY SUM(T.num_photos) DESC LIMIT 10")
	#print(cursor.fetchall())
	data = cursor.fetchall()

	return data

#Recommended Friends
def recommendFriends(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT U.first_name, U.last_name, F.user_id2, COUNT(*) FROM Friends F, Users U WHERE F.user_id1 IN (SELECT Fl.user_id2 FROM Friends Fl WHERE Fl.user_id1 = '{0}' and Fl.user_id2 <> '{0}') and F.user_id2 <> '{0}' and F.user_id2 = U.user_id GROUP BY F.user_id2 ORDER BY COUNT(*) DESC".format(uid))
	data = cursor.fetchall()
	print(uid)
	return data


#default page
@app.route("/", methods=['GET'])
def hello():
	all_photos = getAllPhotos()
	photoids = [lis[1] for lis in all_photos]
	return render_template('hello.html', message='Welcome to Photoshare', photos=all_photos, comments=getComment(photoids), tags=getTagnames(), photoLikes=getLikes(photoids), base64=base64, topUsers = topUsers())


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
