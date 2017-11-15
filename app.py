from flask import Flask, request, render_template, jsonify
from flaskext.mysql import MySQL

mysql = MySQL()
app = Flask(__name__)
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'python1root!'
app.config['MYSQL_DATABASE_DB'] = 'ipdata'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

@app.route('/')
def index():

	return "Index Page"

@app.route('/hello')
def hello():
	requestip = request.remote_addr
	conn = mysql.connect()
	cursor = conn.cursor()
	cursor.execute("INSERT INTO iplist (ip) VALUES ('" + requestip + "')")
	conn.commit()
	cursor.execute("SELECT iplist.ip, iplist.access_time FROM iplist order by id desc limit 10;")
	ip_list = cursor.fetchall()
	conn.close()

	return render_template('hello.html', ip_list=ip_list)

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=4999, debug=True)