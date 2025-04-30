import cv2
import numpy as np
from typing import Generator, Dict, Tuple
import time

class StreamEngine:
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        
    def get_frame(self, quality_settings: Dict) -> bytes:
        """
        Get a single frame with specified quality settings
        """
        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset video to start
            ret, frame = self.cap.read()
            
        # Resize frame according to quality settings
        resolution = quality_settings['resolution']
        frame = cv2.resize(frame, resolution)
        
        # Encode frame
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
        _, buffer = cv2.imencode('.jpg', frame, encode_param)
        return buffer.tobytes()
    
    def generate_stream(self, quality_settings: Dict) -> Generator[bytes, None, None]:
        """
        Generate video stream with specified quality settings
        """
        while True:
            frame = self.get_frame(quality_settings)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(1/30)  # 30 FPS
    
    def __del__(self):
        self.cap.release() 