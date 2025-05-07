from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from stream_controller import StreamController
from wifi_monitor import NetworkMonitor  # Import your existing NetworkMonitor

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
stream_controller = StreamController()
network_monitor = NetworkMonitor()  # Create instance of your existing monitor

# Initialize the monitor directly
network_monitor.start()  # Start the network monitor at app initialization

@app.route('/api/network-metrics')
def get_network_metrics():
    metrics = network_monitor.get_metrics()
    metrics['current_quality'] = network_monitor.get_suggested_quality()
    return jsonify(metrics)

@app.route('/api/set-quality/<quality>', methods=['POST'])
def set_quality(quality):
    stream_controller.set_quality(quality)
    return jsonify({"status": "success", "quality": quality})

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
