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
	requestip = request.remote_addr
	conn = mysql.connect()
	cursor = conn.cursor()
	cursor.execute("INSERT INTO iplist (ip) VALUES ('" + requestip + "')")
	conn.commit()
	cursor.execute("SELECT * FROM iplist order by id desc limit 10;")
	ip_list = cursor.fetchall()
	conn.close()
	return str(ip_list)

@app.route('/hello')
def hello():
	"""Returns the html template index.html in 
	the templates folder"""
	return render_template('hello.html')

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=4999, debug=True)