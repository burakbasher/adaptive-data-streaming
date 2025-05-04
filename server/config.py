"""
Configuration settings for Adaptive Streaming System
"""

import os
import logging

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Paths
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
SAMPLE_VIDEO_PATH = os.path.join(DATA_DIR, 'sample_video.mp4')

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Server configuration
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5000
DEBUG_MODE = True

# Logging configuration
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Network quality thresholds
QUALITY_THRESHOLDS = {
    'low': {
        'resolution': (640, 360),
        'bitrate': 500,  # Kbps
        'min_bandwidth': 0,  # Mbps
        'max_latency': 500,  # ms
        'max_packet_loss': 10,  # %
    },
    'medium': {
        'resolution': (1280, 720),
        'bitrate': 1500,  # Kbps
        'min_bandwidth': 2,  # Mbps
        'max_latency': 150,  # ms
        'max_packet_loss': 5,  # %
    },
    'high': {
        'resolution': (1920, 1080),
        'bitrate': 3000,  # Kbps 
        'min_bandwidth': 5,  # Mbps
        'max_latency': 75,  # ms
        'max_packet_loss': 2,  # %
    }
}

# Stream settings
FPS = 30  # Frames per second
QUALITY_STABILITY_PERIOD = 5  # Seconds to wait before changing quality
DEFAULT_QUALITY = 'medium'  # Default quality level

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT
)