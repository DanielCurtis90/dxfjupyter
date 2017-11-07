from flask import Flask, request, render_template
app = Flask(__name__)

@app.route('/')
def index():
    return 'Index Page'

@app.route('/hello')
def hello():
    """Returns the html template index.html in 
    the templates folder"""
    return render_template('hello.html')

if __name__ == '__main__':
	app.run(host='0.0.0.0')