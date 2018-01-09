from flask import Flask, request, render_template, jsonify, redirect, flash, Response
from werkzeug.utils import secure_filename
from flaskext.mysql import MySQL
from dxfparser import *
import boto3
import shutil
import pickle
from helpers import *


mysql = MySQL()
app = Flask(__name__)
app.config.from_object('config')
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'python1root!'
app.config['MYSQL_DATABASE_DB'] = 'ipdata'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

ALLOWED_EXTENSIONS = set(['dxf', 'eps'])

s3 = boto3.resource(
	"s3",
	aws_access_key_id=S3_KEY,
	aws_secret_access_key=S3_SECRET
	)
bucket = s3.Bucket('dxfstorage')

client = boto3.client(
	"s3",
	aws_access_key_id=S3_KEY,
	aws_secret_access_key=S3_SECRET
	)

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
		return render_template('upload.html')

@app.route("/dxflist", methods=["GET"])
def dxflist():
	return render_template('dxflist.html', bucket=bucket)

@app.route("/reports/<dxffile>", methods=["GET"])
def dxf_report(dxffile):
	if not os.path.isdir("tmp"):
		os.mkdir('tmp')
	#Download the file corresponding with the URL
	bucket.download_file(dxffile, f'tmp/{dxffile}')
	#Convert it to an eps/parse it and save the dictionaries of insert and blocks
	#Note that the dictionaries are defined outside of this route so that this 
	#information is saved
	block_dict, insert_dict, base_entity_dict, layers = convert_dxf(f'tmp/{dxffile}')
	eps_filename = os.path.splitext(dxffile)[0] + ".eps"
	csv_filename = os.path.splitext(dxffile)[0] + ".csv"
	
	#upload the csv under the same name
	bucket.upload_file(f'tmp/{csv_filename}', csv_filename)

	#upload the eps under the same name
	#bucket.upload_file(f'tmp/{eps_filename}', eps_filename)
	#remove the tmp folder
	if os.path.isdir("tmp"):
		shutil.rmtree('tmp')

	#Store the dictonaries for later use
	if not os.path.isdir("objs"):
		os.mkdir('objs')
	#Setup file handlers and serialize(pickle) the object dictionaries
	blockfile = open(f'objs/{os.path.splitext(dxffile)[0]}' + '_block_dict.obj', 'wb')
	insertfile = open(f'objs/{os.path.splitext(dxffile)[0]}' + '_insert_dict.obj', 'wb')
	baseentityfile = open(f'objs/{os.path.splitext(dxffile)[0]}' + '_base_entity_dict.obj', 'wb')
	pickle.dump(block_dict, blockfile)
	pickle.dump(insert_dict, insertfile)
	pickle.dump(base_entity_dict, baseentityfile)
	return render_template('report.html', bucket=bucket, dxffile=dxffile, block_dict=block_dict, insert_dict=insert_dict, base_entity_dict=base_entity_dict, layers=layers)

@app.route("/reports/<dxffile>/<block>", methods=["GET"])
def block_info(dxffile, block):
	blockfile = open(f'objs/{os.path.splitext(dxffile)[0]}' + '_block_dict.obj', 'rb')
	block_dict = pickle.load(blockfile)
	blockref = block_dict[block]
	return render_template('block_info.html', block=blockref, dxffile=dxffile)

@app.route("/reports/<dxffile>/entity/<handle>", methods=["GET"])
def basic_entity(dxffile, handle):
	baseentityfile = open(f'objs/{os.path.splitext(dxffile)[0]}' + '_base_entity_dict.obj', 'rb')
	base_entity_dict = pickle.load(baseentityfile)
	entity = base_entity_dict[handle]
	return render_template('basic_entity.html', entity=entity, dxffile=dxffile)

@app.route("/reports/<dxffile>/<block>/<entity>", methods=["GET"])
def block_info_entity(dxffile, block, entity):
	
	blockfile = open(f'objs/{os.path.splitext(dxffile)[0]}' + '_block_dict.obj', 'rb')
	block_dict = pickle.load(blockfile)
	blockref = block_dict[block]
	return render_template('block_info_entity.html', block=blockref, dxffile=dxffile, entity=entity)

@app.route("/reports/<dxffile>/download", methods=["GET"])
def dxf_report_download(dxffile):
	csv_filename = os.path.splitext(dxffile)[0] + ".csv"
	download_file = client.get_object(Bucket=app.config["S3_BUCKET"], Key=csv_filename)
	return Response(
		download_file['Body'].read(),
		mimetype='text/csv',
		headers={"Content-Disposition": f"attachment;filename={csv_filename}"}
		)

if __name__ == '__main__':
	app.run(host='0.0.0.0',debug=True, port=4999)