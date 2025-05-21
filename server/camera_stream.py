"""server/camera_stream.py"""

import cv2
import base64
import threading
from flask_socketio import SocketIO
from config import QUALITY_THRESHOLDS

class CameraStream:
    def __init__(self):
        self.lock = threading.Lock()
        self.camera = None
        self.running = True
        self.width = 640
        self.height = 360  
        self.open_camera(self.width, self.height)
        self.quality = 'medium'  # Track current quality level

    def open_camera(self, width, height):
        if self.camera:
            self.camera.release()
        self.camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        actual_w = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"[CAMERA] Opened at {actual_w}x{actual_h}")
        
        if width >= 1280 and height >= 720:
            self.quality = 'high'
        elif width >= 640 and height >= 360:
            self.quality = 'medium'
        else:
            self.quality = 'low'

    def handle_set_resolution(self, data):
        width = data.get('width')
        height = data.get('height')
        if width and height:
            # Check if resolution is already set to the requested values
            if width == self.width and height == self.height:
                print(f"[CAMERA] Resolution already set to {width}x{height}, skipping")
                return
                
            with self.lock:
                self.width, self.height = width, height
                self.open_camera(width, height)
    
    def handle_set_quality(self, data):
        quality = data.get('quality')
        if quality not in ['low', 'medium', 'high']:
            print(f"[CAMERA] ⚠ Unknown quality: {quality}")
            return
            
        # Skip if already at this quality level
        if quality == self.quality:
            print(f"[CAMERA] Already at {quality} quality, skipping")
            return
            
        with self.lock:
            self.quality = quality
            resolution = QUALITY_THRESHOLDS[quality]['resolution']
            
            # Only reopen camera if resolution is different
            if self.width != resolution[0] or self.height != resolution[1]:
                self.width, self.height = resolution
                self.open_camera(self.width, self.height)
                print(f"[CAMERA] ✅ Quality switched to {quality} ({self.width}x{self.height})")
            else:
                print(f"[CAMERA] ✅ Quality changed to {quality} (resolution unchanged)")

    def generate_frames(self, socketio: SocketIO):
        while self.running:
            with self.lock:
                success, frame = self.camera.read()
                if not success:
                    continue
                _, buffer = cv2.imencode('.jpg', frame)
                encoded = base64.b64encode(buffer).decode('utf-8')
                socketio.emit('image', encoded)
            socketio.sleep(0.01)
        
    def read_frame(self):
        with self.lock:
            success, frame = self.camera.read()
            if not success:
                return None
            _, buffer = cv2.imencode('.jpg', frame)
            return base64.b64encode(buffer).decode('utf-8')
    
    def get_camera_info(self):
        return {
            'width': self.width,
            'height': self.height,
            'quality': self.quality
        }
