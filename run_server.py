from server.app import app
from server.wifi_monitor import WiFiMonitor
from server.controller import StreamController
from server.stream_engine import StreamEngine
from server.config import *
from logger.log_writer import LogWriter
import os

def main():
    # Initialize components
    wifi_monitor = WiFiMonitor()
    stream_controller = StreamController()
    stream_engine = StreamEngine(VIDEO_PATH)
    log_writer = LogWriter(LOG_DIR, LOG_FILE)
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Start the Flask server
    app.run(host=HOST, port=PORT, debug=DEBUG)

if __name__ == '__main__':
    main() 