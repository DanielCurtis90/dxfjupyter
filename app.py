from flask import Flask, request, render_template, jsonify, redirect, flash
from werkzeug.utils import secure_filename
from flaskext.mysql import MySQL
from dxfparser import *
import boto3
import shutil


mysql = MySQL()
app = Flask(__name__)
app.config.from_object('config')
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'python1root!'
app.config['MYSQL_DATABASE_DB'] = 'ipdata'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

from helpers import *

ALLOWED_EXTENSIONS = set(['dxf', 'eps'])

s3 = boto3.resource(
	"s3",
	aws_access_key_id=S3_KEY,
	aws_secret_access_key=S3_SECRET
	)
bucket = s3.Bucket('dxfstorage')

def allowed_file(filename):
	return '.' in filename and \
		   filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

@app.route("/upload", methods=["GET", "POST"])
def upload_file():
	if request.method=='POST':
		print("Attempting Post")
		# Case A, check that the file input key is there
		if "user_file" not in request.files:
			return "No user_file key in request.files"

		# Case B, if the key is there, save it
		file = request.files["user_file"]

		# Case C, make sure there is a file
		if file.filename == "":
			return "Please select a file"

		# Case D, check if authorized
		if file and allowed_file(file.filename):
			file.filename = secure_filename(file.filename)
			output = upload_file_to_s3(file, app.config["S3_BUCKET"])
			file_loc = str("{}{}".format(app.config["S3_LOCATION"], file.filename))
			flash('Upload successful!')
			return redirect("/dxflist")
		else:
			return redirect("/upload")
	else:
		print(app.config["S3_LOCATION"])
		return render_template('upload.html')

@app.route("/dxflist", methods=["GET"])
def dxflist():
	return render_template('dxflist.html', bucket=bucket)

@app.route("/<dxffile>", methods=["GET"])
def dxf_report(dxffile):
	os.mkdir('tmp')
	#Download the file corresponding with the URL
	bucket.download_file(dxffile, f'tmp/{dxffile}')
	#Convert it to an eps/parse it
	convert_dxf(f'tmp/{dxffile}')
	eps_filename = os.path.splitext(dxffile)[0] + ".eps"
	bucket.upload_file(f'tmp/{eps_filename}', eps_filename)
	shutil.rmtree('tmp')

	return render_template('report.html', dxffile=dxffile)

if __name__ == '__main__':
	app.run(host='0.0.0.0',debug=True, port=4999)