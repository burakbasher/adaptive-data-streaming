"""server/video_stream.py"""

import cv2
import base64
import threading
from flask_socketio import SocketIO
import time


class VideoStream:
    def __init__(self, base_path='server/data/sample_video'):
        self.lock = threading.Lock()
        self.base_path = base_path  #  sample_video_360.mp4
        self.video = None
        self.running = True
        self.is_playing = True
        self.playback_speed = 1.0
        self.current_frame_index = 0  
        self.total_frames = 0
        self.quality = 'medium'
        self.width, self.height = self._get_resolution_from_quality(self.quality)
        self.target_fps = 100  # Sabit FPS
        self.frame_interval = 1.0 / self.target_fps
        self.last_frame_time = 0
        self.open_video()

    def _get_resolution_from_quality(self, quality):
        resolution_map = {
            'low': (426, 240),
            'medium': (640, 360),
            'high': (1280, 720)
        }
        return resolution_map.get(quality, (640, 360))

    def _get_quality_suffix(self, quality):
        quality_map = {
            'low': '240',
            'medium': '360',
            'high': '720'
        }
        return quality_map.get(quality, '360')

    def open_video(self):
        if self.video:
            self.video.release()

        video_file = f"{self.base_path}_{self._get_quality_suffix(self.quality)}.mp4"
        self.video = cv2.VideoCapture(video_file)

        if not self.video.isOpened():
            print(f"[VIDEO] ❌ Failed to open {video_file}")
            return

        self.total_frames = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame_index)
        print(f"[VIDEO] ▶ Opened {video_file} at frame {self.current_frame_index}")

    def handle_set_quality(self, data):
        quality = data.get('quality')
        if quality not in ['low', 'medium', 'high']:
            print(f"[VIDEO] ⚠ Unknown quality: {quality}")
            return

        with self.lock:
            if self.video and self.video.isOpened():
                self.current_frame_index = int(self.video.get(cv2.CAP_PROP_POS_FRAMES))

            self.quality = quality
            self.width, self.height = self._get_resolution_from_quality(quality)
            self.open_video()
            print(f"[VIDEO] ✅ Quality switched to {quality} ({self.width}x{self.height})")

    def handle_play_pause(self, is_playing):
        with self.lock:
            self.is_playing = is_playing
            print(f"[VIDEO] {'▶ Playing' if is_playing else '⏸ Paused'}")

    def handle_set_speed(self, speed):
        with self.lock:
            self.playback_speed = speed
            print(f"[VIDEO] Speed set to {speed}x")

    def handle_seek(self, position):
        with self.lock:
            if self.video and self.video.isOpened():
                frame_index = int(position * self.total_frames)
                self.current_frame_index = min(max(0, frame_index), self.total_frames - 1)
                self.video.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame_index)
                print(f"[VIDEO] Seeking to frame {self.current_frame_index}")

    def generate_frames(self, socketio: SocketIO):
        target_fps = 100
        frame_interval = 1.0 / target_fps

        while self.running:
            start_time = time.time()

            with self.lock:
                if not self.video or not self.video.isOpened() or not self.is_playing:
                    continue

                success, frame = self.video.read()
                if not success:
                    self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.current_frame_index = 0
                    continue

                self.current_frame_index = int(self.video.get(cv2.CAP_PROP_POS_FRAMES))
                frame = cv2.resize(frame, (self.width, self.height))
                _, buffer = cv2.imencode('.jpg', frame)
                encoded = base64.b64encode(buffer).decode('utf-8')
                socketio.emit('image', encoded)

            elapsed = time.time() - start_time
            sleep_time = max(0, frame_interval - elapsed)
            time.sleep(sleep_time)

    def read_frame(self):
        with self.lock:
            if not self.video or not self.video.isOpened() or not self.is_playing:
                return None

            adjusted_interval = self.frame_interval / self.playback_speed
            
            current_time = time.time()
            elapsed = current_time - self.last_frame_time
            if elapsed < adjusted_interval:
                return None
                
            if self.playback_speed > 1:
                frames_to_skip = int((self.playback_speed - 1) * 2)  
                for _ in range(frames_to_skip):
                    self.video.read()  # Skip frames
                    self.current_frame_index = int(self.video.get(cv2.CAP_PROP_POS_FRAMES))
                    if self.current_frame_index >= self.total_frames - 1:
                        self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        self.current_frame_index = 0

            success, frame = self.video.read()
            if not success:
                self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.current_frame_index = 0
                return None

            self.current_frame_index = int(self.video.get(cv2.CAP_PROP_POS_FRAMES))
            frame = cv2.resize(frame, (self.width, self.height))
            _, buffer = cv2.imencode('.jpg', frame)
            self.last_frame_time = current_time
            return base64.b64encode(buffer).decode('utf-8')

    def get_video_info(self):
        return {
            'total_frames': self.total_frames,
            'current_frame': self.current_frame_index,
            'is_playing': self.is_playing,
            'playback_speed': self.playback_speed,
            'quality': self.quality,
            'buffer_size': 0  
        }
