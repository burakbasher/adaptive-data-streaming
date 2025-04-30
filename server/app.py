from flask import Flask, Response, render_template
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    # Video streaming endpoint will be implemented here
    pass

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 