from flask import Flask, Response, render_template
from flask_cors import CORS
import os

# Template klasörünü client olarak ayarla
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'client'))
app = Flask(__name__, template_folder=template_dir, static_folder=template_dir)
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