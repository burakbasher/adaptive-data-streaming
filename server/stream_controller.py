"""server/stream_controller.py"""

from flask_socketio import SocketIO
from camera_stream import CameraStream
from video_stream import VideoStream
from controller import AdaptiveQualityController
from wifi_monitor import NetworkMonitor, get_network_monitor
import time
import threading

class StreamController:
    def __init__(self):
        self.current_source = 'video'  
        
        self.video_stream = VideoStream()
        self.camera_stream = None  

        self.running = True
        self.control_mode = 'manual'
        
        # Use shared network monitor instance instead of creating a new one
        self.network_monitor = get_network_monitor()
        
        self.adaptive_controller = AdaptiveQualityController()
        self.adaptive_quality_thread = None
        self.start_adaptive_control()
        
        self.current_quality = 'medium'  # Varsayılan kalite
        
    def start_adaptive_control(self):
        """Start the adaptive quality control thread"""
        if self.adaptive_quality_thread is None:
            self.adaptive_quality_thread = threading.Thread(target=self._adaptive_quality_loop)
            self.adaptive_quality_thread.daemon = True
            self.adaptive_quality_thread.start()
    
    def _adaptive_quality_loop(self):
        """Background thread for adaptive quality control"""
        last_applied_quality = None
        
        while self.running and self.control_mode == 'adaptive':
            metrics = self.network_monitor.get_metrics()
            
            # Determine optimal quality
            optimal_quality = self.adaptive_controller.determine_quality(metrics)
            
            # Apply quality if needed and if it's different from the last applied quality
            if optimal_quality != last_applied_quality:
                print(f"[ADAPTIVE] Changing quality from {last_applied_quality} to {optimal_quality}")
                
                # Apply to current stream source
                if self.current_source == 'video':
                    if self.video_stream.quality != optimal_quality:
                        self.video_stream.handle_set_quality({'quality': optimal_quality})
                elif self.current_source == 'camera' and self.camera_stream:
                    # For camera, check if current resolution matches before applying
                    optimal_resolution = self.adaptive_controller.get_resolution()
                    current_resolution = (self.camera_stream.width, self.camera_stream.height)
                    
                    if current_resolution != optimal_resolution:
                        print(f"[ADAPTIVE] Changing camera resolution from {current_resolution} to {optimal_resolution}")
                        self.camera_stream.handle_set_resolution({
                            'width': optimal_resolution[0], 
                            'height': optimal_resolution[1]
                        })
                    else:
                        print(f"[ADAPTIVE] Camera already at optimal resolution: {optimal_resolution}")
                
                # Update the last applied quality
                last_applied_quality = optimal_quality
                    
            # Check every 2 seconds
            time.sleep(2)

    def set_source(self, source):
        """
        Set the video source (camera or video file)
        """
        if source not in ['camera', 'video']:
            return
        
        # Skip if we're already using this source
        if self.current_source == source:
            return
        
        print(f"[StreamController] Switching source from {self.current_source} to {source}")
        self.current_source = source
        
        # Handle camera source
        if source == 'camera':
            # Initialize camera if needed
            if self.camera_stream is None:
                self.camera_stream = CameraStream()
        else:  # video source
            # Close camera if it's open to free up resources
            if self.camera_stream:
                # Release camera resources
                print("[StreamController] Closing camera")
                self.camera_stream.camera.release()
                self.camera_stream = None

    def handle_set_resolution(self, data):
        if self.current_source == 'camera':
            self.camera_stream.handle_set_resolution(data)

    def handle_set_quality(self, data):

        quality = data.get('quality', 'medium')
        self.current_quality = quality  # Mevcut kaliteyi güncelle
        
        # Etkin stream'in kalitesini güncelle
        if self.current_source == 'video':
            # Alt sınıfa sözlük olarak gönder
            self.video_stream.handle_set_quality({'quality': quality})
        elif self.current_source == 'camera' and self.camera_stream:
            # Alt sınıfa sözlük olarak gönder
            self.camera_stream.handle_set_quality({'quality': quality})
            
        # Update adaptive controller if in manual mode
        if self.control_mode == 'manual':
            self.adaptive_controller.set_quality(quality)
            print(f"[STREAM] Manually set quality to {quality}")
        
        return {'success': True, 'quality': quality}

    def handle_play_pause(self, data):
        if self.current_source == 'video':
            self.video_stream.handle_play_pause(data.get('is_playing', True))

    def handle_set_speed(self, data):
        if self.current_source == 'video':
            self.video_stream.handle_set_speed(data.get('speed', 1.0))

    def handle_seek(self, data):
        if self.current_source == 'video':
            self.video_stream.handle_seek(data.get('position', 0))
            
    def set_control_mode(self, mode):
        if mode not in ['manual', 'adaptive']:
            return
            
        if self.control_mode == mode:
            return
            
        self.control_mode = mode
        print(f"[STREAM] Control mode changed to: {mode}")
        
        if mode == 'adaptive':
            # Start adaptive quality control thread
            if self.adaptive_quality_thread is None or not self.adaptive_quality_thread.is_alive():
                self.adaptive_quality_thread = threading.Thread(target=self._adaptive_quality_loop)
                self.adaptive_quality_thread.daemon = True
                self.adaptive_quality_thread.start()
        else:
            pass

    def get_stream_info(self):
        info = {}
        if self.current_source == 'video':
            info = self.video_stream.get_video_info()
        elif self.current_source == 'camera':
            info = self.camera_stream.get_camera_info()
            
        info['control_mode'] = self.control_mode
        info['source'] = self.current_source
        
        if self.control_mode == 'adaptive':
            info['network_metrics'] = self.network_monitor.get_metrics()
            
        return info

    def generate_frames(self, socketio: SocketIO):
        while self.running:
            frame_data = None
            if self.current_source == 'camera':
                frame_data = self.camera_stream.read_frame()
            elif self.current_source == 'video':
                frame_data = self.video_stream.read_frame()

            if frame_data:
                socketio.emit('image', frame_data)
                socketio.emit('video_info', self.get_stream_info())

            socketio.sleep(0.01)
            
    def __del__(self):
        """Destructor to cleanup resources"""
        self.running = False
        if hasattr(self, 'network_monitor'):
            self.network_monitor.stop()

    def get_current_quality(self) -> str:
        """
        Get the current video quality setting
        
        Returns:
            Current quality level ('low', 'medium', or 'high')
        """
        if self.control_mode == 'adaptive' and hasattr(self, 'adaptive_controller'):
            return self.adaptive_controller.current_quality
        
        if self.current_source == 'video' and hasattr(self.video_stream, 'current_quality'):
            return self.video_stream.current_quality
        
        if self.current_source == 'camera' and self.camera_stream and hasattr(self.camera_stream, 'current_quality'):
            return self.camera_stream.current_quality
            
        return self.current_quality

