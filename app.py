from flask import Flask,render_template, request, redirect, session
from bs4 import BeautifulSoup
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import urllib2
import re
import json

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:root@localhost/angelhack"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.secret_key = 'oxoa'
app.config['DEBUG'] = True 
db=SQLAlchemy(app)

class user(db.Model):
	u_id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String(100))
	email = db.Column(db.String(100))
	password = db.Column(db.String(100))

	def __init__(self,name,email,password):
		self.name = name
		self.email = email
		self.password = password

class handles(db.Model):
	handel_id = db.Column(db.Integer, primary_key = True)
	codechef = db.Column(db.String(40))
	codeforces = db.Column(db.String(40))
	hackerrank = db.Column(db.String(40))
	user_id = db.Column(db.Integer, db.ForeignKey(user.u_id))

	def __init__(self, codechef, codeforces, hackerrank, user_id):
		self.codechef = codechef
		self.codeforces = codeforces
		self.hackerrank = hackerrank
		self.user_id=user_id

db.create_all()

@app.route('/login',methods = ['POST','GET'])
def login():
	if request.method == 'GET':
		if session.get('userID') is not None:
			temp = user.query.filter_by(u_id = session ['userID']).first()
			loggedinuser = temp.name
			return redirect('profile/' + loggedinuser)
		else:
			return render_template('login.html')
	elif request.method == 'POST':
		loginuser = request.form['username']
		loginpassword = request.form['password']
		currentuser = user.query.filter_by(name = loginuser).first()

		if currentuser is not None:
			if currentuser.password == loginpassword:
				session['userID'] = currentuser.u_id
				return redirect('profile/' + loginuser)
			else:
				return render_template('login.html')
		else:
			return render_template('login.html',success = 'User does not exist')

@app.route('/register',methods = ['POST','GET'])
def register():
	if request.method == 'GET':
		return render_template('register.html')
	elif request.method == 'POST':
		tempuser = user(request.form['username'],request.form['emailid'],request.form['password'])
		tempusername = request.form['username']
		alreadyexisting = user.query.filter_by(name=tempusername).count()

		if(alreadyexisting > 0):
			return render_template('register.html',alreadyexists = 'This username is already taken')
		else:
			db.session.add(tempuser)
			db.session.commit()
			render_template('login.html',success = 'You have successfully registered')
			return redirect('/login')

@app.route('/profile/<username>', methods = ['GET','POST'])
def profile(username):
	if session.get('userID') is not None:
		if request.method == 'GET':
			current_user = user.query.filter_by(u_id = session.get('userID')).first()
			return render_template('profile.html',user=current_user.name)
		elif request.method == 'POST':
			tempuserhandles = handles(request.form['title'],request.form['content'],session['userID'])
			db.session.add(tempuserhandles)
			db.session.commit()

			# userposts = handles.query.filter_by(user_id = session['userID'])
	else:
		return redirect('/')

@app.route('/profile/<user>/logout')
def logout(user):
	session.pop('userID', None)
	return redirect('/login') 

@app.route('/')
def index():
	if session.get('userID') is not None:
		temp = user.query.filter_by(u_id = session ['userID']).first()
		loggedinuser = temp.name
		return redirect('profile/' + loggedinuser)
	else:
		return render_template('index.html')


@app.route('/user/<ch>/<cf>/<hr>')
def get_data(cf,ch, hr):
	url = 'https://www.codechef.com/users/' + ch
	response = urllib2.urlopen(url).read()
	p_res = BeautifulSoup(response,'html.parser')
	ratings = p_res.find_all('a',{'class':'rating'})
	res = []
	for x in ratings:
		res.append(re.sub("[\(\[].*?[\)\]]", "", str(x)))
	codechef = res[0].split('>')[1].split('<')[0]
	url = 'http://www.codeforces.com/api/user.info?handles=' + cf
	response = urllib2.urlopen(url).read()
	p_res = json.loads(response)
	if "rating" in p_res["result"][0]:
		codeforces = int(p_res["result"][0]["rating"])
	else:
		codeforces=0

	url = "https://www.hackerrank.com/" + hr + "?hr_r=1"
	response = urllib2.urlopen(url).read()
	arr = response.split('%22')
	arr_i = 0
	count = 0
	for ele in arr:
		count += 1
		if "score" in ele:
			arr_i += 1
		if arr_i == 16:
			hackerrank = arr[count]
			break
	hackerrank = hackerrank[3:-3]

	out = {}
	out["codechef"] = codechef
	out["codeforces"] = codeforces
	out["hackerrank"] = hackerrank
	hands = {}
	hands["codechef"] = ch
	hands["codeforces"] = cf
	hands["hackerrank"] = hr
	return render_template('angelHack.html',res=out,handles=hands)

if __name__=='__main__':
	app.run(debug=True)