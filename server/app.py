from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from flask_cors import CORS
import time
import logging

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:5173"]}})
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:5173", "*"])

# NetworkMonitor'u import et
from wifi_monitor import get_network_monitor

# Socket handler'ları kaydet
from socket_handlers import register_handlers
register_handlers(socketio)

# Sonra diğer modülleri import et
from stream_controller import StreamController
stream_controller = StreamController()

# Network monitoring imports
network_monitor = get_network_monitor()

@app.route('/')
def index():
    return render_template('index.html')


# Network metrikleri için REST API endpoint'i ekleyin
@app.route('/api/network-metrics', methods=['GET'])
def get_network_metrics():
    """API endpoint to get current network metrics"""
    metrics = network_monitor.get_metrics()
    quality = stream_controller.get_current_quality()
    
    response = {
        "bandwidth": metrics['bandwidth'],
        "latency": metrics['latency'],
        "packet_loss": metrics['packet_loss'],
        "current_quality": quality
    }
    
    return jsonify(response)


# Diğer API endpoint'leri
@app.route('/api/set-quality/<quality>', methods=['POST'])
def api_set_quality(quality):
    if quality in ['low', 'medium', 'high']:
        stream_controller.handle_set_quality({'quality': quality})
        return jsonify({'success': True, 'quality': quality})
    return jsonify({'success': False, 'error': 'Invalid quality'}), 400


@app.route('/api/set-source/<source>', methods=['POST'])
def api_set_source(source):
    if source in ['camera', 'video']:
        stream_controller.set_source(source)
        return jsonify({'success': True, 'source': source})
    return jsonify({'success': False, 'error': 'Invalid source'}), 400


@app.route('/api/set-control-mode/<mode>', methods=['POST'])
def api_set_control_mode(mode):
    if mode in ['manual', 'adaptive']:
        stream_controller.set_control_mode(mode)
        return jsonify({'success': True, 'mode': mode})
    return jsonify({'success': False, 'error': 'Invalid mode'}), 400


@app.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint for latency testing"""
    return jsonify({
        "status": "success",
        "message": "pong",
        "timestamp": time.time(),
        "seq": request.args.get('seq', '0')
    })


@app.route('/test-file', methods=['GET'])
def test_file():
    """Generate a test file for bandwidth measurement"""
    # Create a 10 MB test file for more accurate measurement
    test_data = b'0' * 10 * 1024 * 1024
    
    response = app.response_class(
        response=test_data,
        status=200,
        mimetype='application/octet-stream'
    )
    
    response.headers["Content-Length"] = len(test_data)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    
    return response


# SocketIO event handlers
@socketio.on('connect')
def on_connect():
    print("[SocketIO] Client connected")
    socketio.start_background_task(stream_controller.generate_frames, socketio)

@socketio.on('set_source')
def set_source(data):
    source = data.get('source')
    stream_controller.set_source(source)

@socketio.on('set_resolution')
def set_resolution(data):
    stream_controller.handle_set_resolution(data)

@socketio.on('set_quality')
def set_quality(data):
    stream_controller.handle_set_quality(data)

@socketio.on('play_pause')
def play_pause(data):
    stream_controller.handle_play_pause(data)

@socketio.on('set_speed')
def set_speed(data):
    stream_controller.handle_set_speed(data)

@socketio.on('seek')
def seek(data):
    stream_controller.handle_seek(data)

@socketio.on('set_control_mode')
def set_control_mode(data):
    mode = data.get('mode')
    stream_controller.set_control_mode(mode)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=3000)
