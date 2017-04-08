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
	contact_no = db.Column(db.String(20))
	birthday = db.Column(db.String(20))
	about = db.Column(db.String(500))

	def __init__(self,name,email,password, contact_no, birthday, about):
		self.name = name
		self.email = email
		self.password = password
		self.contact_no = contact_no
		self.birthday = birthday
		self.about = about

class handles(db.Model):
	handle_id = db.Column(db.Integer, primary_key = True)
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
		tempuser = user(request.form['username'],request.form['emailid'],request.form['password'], request.form['contact'], request.form['birthday'], request.form['about'])
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
		current_user = user.query.filter_by(u_id = session.get('userID')).first()
		hands = {}
		user_ratings = {}
		account_handles = handles.query.filter_by(user_id=session.get('userID')).first()
		if account_handles is not None:
			hands["codechef"] = account_handles.codechef
			hands["codeforces"] = account_handles.codeforces
			hands["hackerrank"] = account_handles.hackerrank
			user_ratings = get_data(account_handles.codechef, account_handles.codeforces, account_handles.hackerrank)
		else:
			hands["codechef"] = "Set handle"
			hands["codeforces"] = "Set handle"
			hands["hackerrank"] = "Set handle"
			user_ratings["codechef"] = "0"
			user_ratings["codeforces"] = "0"
			user_ratings["hackerrank"] = "0"

		if request.method == 'GET':
			user_final_rating = calc_final_rating(user_ratings["codechef"], user_ratings["codeforces"], user_ratings["hackerrank"])
			return render_template('profile.html',user=current_user, handles=hands, ratings=user_ratings, final_rating=user_final_rating)
		elif request.method == 'POST':
			if account_handles is not None:
				account_handles.codechef = request.form['codechef']
				account_handles.codeforces = request.form['codeforces']
				account_handles.hackerrank = request.form['hackerrank']				
			else:
				tempuserhandles = handles(request.form['codechef'],request.form['codeforces'],request.form['hackerrank'],session['userID'])
				db.session.add(tempuserhandles)
			db.session.commit()
			account_handles = handles.query.filter_by(user_id=session.get('userID')).first()
			user_ratings = get_data(account_handles.codechef, account_handles.codeforces, account_handles.hackerrank)
			hands["codechef"] = account_handles.codechef
			hands["codeforces"] = account_handles.codeforces
			hands["hackerrank"] = account_handles.hackerrank
			user_final_rating = calc_final_rating(user_ratings["codechef"], user_ratings["codeforces"], user_ratings["hackerrank"])
			return render_template('profile.html',user=current_user, msg="added", handles=hands, ratings=user_ratings, final_rating=user_final_rating)
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

def calc_final_rating(ch, cf, hr):
	k1 = 2.0522
	k2 = 2.3795
	k3 = 6.5047
	ch, cf, hr = float(ch), float(cf), float(hr)
	final_rating = (k1*ch + k2*cf + k3*hr) / (k1+k2+k3)
	return final_rating


def get_data(ch,cf, hr):
	url = 'https://www.codechef.com/users/' + ch
	response = urllib2.urlopen(url).read()
	p_res = BeautifulSoup(response,'html.parser')
	ratings = p_res.find_all('a',{'class':'rating'})
	res = []
	for x in ratings:
		res.append(re.sub("[\(\[].*?[\)\]]", "", str(x)))
	codechef = float(res[0].split('>')[1].split('<')[0])
	url = 'http://www.codeforces.com/api/user.info?handles=' + cf
	response = urllib2.urlopen(url).read()
	p_res = json.loads(response)
	if "rating" in p_res["result"][0]:
		codeforces = float(p_res["result"][0]["rating"])
	else:
		codeforces=0.0

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
	hackerrank = float(hackerrank[3:-3])

	out = {}
	out["codechef"] = (codechef/2951.0)*1000
	out["codeforces"] = (codeforces/3534.0)*1000
	out["hackerrank"] = (hackerrank/2938.07)*1000
	return out

if __name__=='__main__':
	app.run(debug=True)