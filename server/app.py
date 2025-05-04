"""
Flask server for Adaptive Streaming System
"""

import os
import time
import json
import logging
from flask import Flask, Response, jsonify, render_template, request, send_from_directory
from flask_cors import CORS

# Import our custom modules
from config import SERVER_HOST, SERVER_PORT, DEBUG_MODE, LOGS_DIR
from wifi_monitor import NetworkMonitor
from controller import StreamController
from stream_engine import StreamEngine
from logger.log_writer import MetricsLogger

# Configure logging
logger = logging.getLogger('app')

# Initialize Flask app
app = Flask(__name__, static_folder='../client', static_url_path='')
CORS(app)  # Enable Cross-Origin Resource Sharing

# Initialize components
network_monitor = NetworkMonitor()
stream_controller = StreamController()
stream_engine = StreamEngine()
metrics_logger = MetricsLogger(LOGS_DIR)

@app.route('/')
def index():
    """Serve the main page"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/video_feed')
def video_feed():
    """
    Video streaming route
    """
    # Start components if not started
    if not hasattr(network_monitor, 'running') or not network_monitor.running:
        network_monitor.start()
    
    if not hasattr(stream_engine, 'streaming') or not stream_engine.streaming:
        stream_engine.start()
    
    # Create a response with the video stream
    return Response(
        stream_engine.get_frame_generator(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/api/network-metrics', methods=['GET'])
def get_network_metrics():
    """
    Return the latest network metrics
    """
    # Get current metrics from monitor
    metrics = network_monitor.get_metrics()
    
    # Determine quality based on metrics
    quality = stream_controller.determine_quality(metrics)
    
    # Set stream quality
    stream_engine.set_quality(quality)
    
    # Log metrics
    metrics_logger.log_metrics(metrics, quality)
    
    # Return response
    return jsonify({
        'bandwidth': metrics['bandwidth'],
        'latency': metrics['latency'],
        'packet_loss': metrics['packet_loss'],
        'current_quality': quality,
        'resolution': stream_controller.get_resolution(),
        'bitrate': stream_controller.get_bitrate()
    })

@app.route('/api/manual-metrics', methods=['POST'])
def update_manual_metrics():
    """
    Update metrics manually (for testing)
    """
    try:
        data = request.json
        
        # Extract metrics
        metrics = {
            'bandwidth': float(data.get('bandwidth', 0)),
            'latency': float(data.get('latency', 0)),
            'packet_loss': float(data.get('packet_loss', 0))
        }
        
        # Determine quality based on metrics
        quality = stream_controller.determine_quality(metrics)
        
        # Set stream quality
        stream_engine.set_quality(quality)
        
        # Log metrics
        metrics_logger.log_metrics(metrics, quality)
        
        return jsonify({
            'status': 'success',
            'quality': quality,
            'resolution': stream_controller.get_resolution(),
            'bitrate': stream_controller.get_bitrate()
        })
        
    except Exception as e:
        logger.error(f"Error updating metrics: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/api/quality-history', methods=['GET'])
def get_quality_history():
    """
    Return quality change history
    """
    limit = request.args.get('limit', default=10, type=int)
    quality_changes = metrics_logger.get_quality_changes(limit=limit)
    
    return jsonify(quality_changes)

@app.route('/api/metrics-history', methods=['GET'])
def get_metrics_history():
    """
    Return network metrics history
    """
    limit = request.args.get('limit', default=30, type=int)
    metrics_history = metrics_logger.get_metrics_history(limit=limit)
    
    return jsonify(metrics_history)

@app.route('/api/metrics-summary', methods=['GET'])
def get_metrics_summary():
    """
    Return summary of collected metrics
    """
    summary = metrics_logger.generate_summary_report()
    return jsonify(summary)

@app.route('/api/set-quality/<quality>', methods=['POST'])
def set_quality(quality):
    """
    Manually set streaming quality
    """
    if quality not in ['low', 'medium', 'high']:
        return jsonify({'status': 'error', 'message': 'Invalid quality level'}), 400
    
    # Set quality in stream engine
    stream_engine.set_quality(quality)
    
    return jsonify({
        'status': 'success',
        'quality': quality,
        'resolution': stream_controller.get_resolution(),
        'bitrate': stream_controller.get_bitrate()
    })

def shutdown_server():
    """Shutdown all components"""
    try:
        if hasattr(network_monitor, 'stop'):
            network_monitor.stop()
        
        if hasattr(stream_engine, 'stop'):
            stream_engine.stop()
            
        logger.info("All components stopped")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Register shutdown function
import atexit
atexit.register(shutdown_server)

def main():
    """Main entry point"""
    logger.info("Starting Adaptive Streaming Server")
    
    # Start the network monitor
    network_monitor.start()
    
    # Start the Flask app
    app.run(debug=DEBUG_MODE, host=SERVER_HOST, port=SERVER_PORT)

if __name__ == "__main__":
    main()