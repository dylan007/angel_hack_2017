from flask import Flask 
from bs4 import BeautifulSoup
import urllib2
import re
import json
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
	return "Hello World"

@app.route('/user/<ch>/<cf>/<hr>')
def get_data(cf,ch, hr):
	url = 'https://www.codechef.com/users/' + ch
	response = urllib2.urlopen(url).read()
	p_res = BeautifulSoup(response,'html.parser')
	ratings = p_res.find_all('a',{'class':'rating'})
	res = []
	for x in ratings:
		res.append(re.sub("[\(\[].*?[\)\]]", "", str(x)))
	codechef = res[0]
	url = 'http://www.codeforces.com/api/user.info?handles=' + cf
	response = urllib2.urlopen(url).read()
	p_res = json.loads(response)
	if "rating" in p_res["result"][0]:
		codeforces = int(p_res["result"][0]["rating"])
	else:
		codeforces=0

	proc = subprocess.Popen(["curl https://www.hackerrank.com/" + hr + "?hr_r=1", "~"], stdout=subprocess.PIPE, shell=True)
	(out, err) = proc.communicate()
	arr = out.split('%22')
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
	return json.dumps(out)

if __name__=='__main__':
	app.run(debug=True)