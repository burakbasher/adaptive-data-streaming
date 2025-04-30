import os

# Server Configuration
HOST = '0.0.0.0'
PORT = 5000
DEBUG = True

# Video Configuration
VIDEO_PATH = os.path.join('data', 'sample_video.mp4')
DEFAULT_FPS = 30

# Network Quality Thresholds
BANDWIDTH_THRESHOLDS = {
    'low': 1.0,      # Mbps
    'medium': 2.5,   # Mbps
    'high': 5.0      # Mbps
}

LATENCY_THRESHOLDS = {
    'low': 100,      # ms
    'medium': 50,    # ms
    'high': 20       # ms
}

PACKET_LOSS_THRESHOLDS = {
    'low': 5.0,      # %
    'medium': 2.0,   # %
    'high': 0.5      # %
}

# Logging Configuration
LOG_DIR = 'logs'
LOG_FILE = 'stream_metrics.log' 