"""
Streaming Engine Module
Handles video streaming with adaptive quality
"""

import os
import cv2
import time
import logging
import threading
from typing import Generator, Optional, Tuple

# Import configuration
from config import SAMPLE_VIDEO_PATH, FPS, QUALITY_THRESHOLDS

# Configure logger
logger = logging.getLogger('stream_engine')

class VideoStreamError(Exception):
    """Exception raised for video streaming errors"""
    pass

class StreamEngine:
    """
    Video streaming engine that adapts quality based on network conditions
    """
    
    def __init__(self, video_path: str = SAMPLE_VIDEO_PATH):
        """
        Initialize the streaming engine
        
        Args:
            video_path: Path to the video file
        """
        self.video_path = video_path
        self.video_capture = None
        self.current_quality = 'medium'
        self.streaming = False
        self.stream_thread = None
        
        # Frame data
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        # Frame rate control
        self.fps = FPS
        self.frame_time = 1.0 / self.fps
        
        # Check if video file exists
        if not os.path.exists(video_path):
            raise VideoStreamError(f"Video file not found: {video_path}")
        
        logger.info(f"StreamEngine initialized with video: {video_path}")
    
    def start(self) -> None:
        """Start the streaming thread"""
        if self.streaming:
            logger.warning("Streaming is already in progress")
            return
        
        try:
            # Open video file
            self.video_capture = cv2.VideoCapture(self.video_path)
            
            if not self.video_capture.isOpened():
                raise VideoStreamError(f"Could not open video file: {self.video_path}")
            
            # Start streaming thread
            self.streaming = True
            self.stream_thread = threading.Thread(target=self._stream_loop)
            self.stream_thread.daemon = True
            self.stream_thread.start()
            
            logger.info("Video streaming started")
            
        except Exception as e:
            logger.error(f"Error starting stream: {e}")
            if self.video_capture:
                self.video_capture.release()
                self.video_capture = None
            raise
    
    def stop(self) -> None:
        """Stop the streaming thread"""
        self.streaming = False
        
        if self.stream_thread:
            self.stream_thread.join(timeout=2.0)
            
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
            
        logger.info("Video streaming stopped")
    
    def _stream_loop(self) -> None:
        """Main streaming loop"""
        last_frame_time = time.time()
        
        while self.streaming and self.video_capture:
            try:
                # Calculate time since last frame
                current_time = time.time()
                elapsed = current_time - last_frame_time
                
                # Control frame rate
                if elapsed < self.frame_time:
                    time.sleep(self.frame_time - elapsed)
                
                # Read the next frame
                success, frame = self.video_capture.read()
                
                # If end of video, loop back to beginning
                if not success:
                    logger.debug("End of video reached, restarting")
                    self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                
                # Resize frame according to current quality
                resized_frame = self._resize_frame(frame, self.current_quality)
                
                # Update current frame (thread-safe)
                with self.frame_lock:
                    self.current_frame = resized_frame
                
                last_frame_time = time.time()
                
            except Exception as e:
                logger.error(f"Error in streaming loop: {e}")
                time.sleep(0.1)  # Avoid tight loop on error
    
    def _resize_frame(self, frame, quality: str) -> bytes:
        """
        Resize a frame according to quality level
        
        Args:
            frame: Original video frame
            quality: Quality level ('low', 'medium', 'high')
            
        Returns:
            JPEG encoded frame at the appropriate resolution
        """
        # Get target resolution
        width, height = QUALITY_THRESHOLDS[quality]['resolution']
        
        # Resize frame
        resized = cv2.resize(frame, (width, height))
        
        # Simulate compression based on bitrate (this is simplified)
        # In a real implementation, you would use actual video codecs with bitrate control
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), self._get_jpeg_quality(quality)]
        _, buffer = cv2.imencode('.jpg', resized, encode_params)
        
        return buffer.tobytes()
    
    def _get_jpeg_quality(self, quality: str) -> int:
        """
        Convert quality level to JPEG encoding quality
        
        Args:
            quality: Quality level ('low', 'medium', 'high')
            
        Returns:
            JPEG quality value (0-100)
        """
        # Map quality levels to JPEG quality values
        quality_map = {
            'low': 70,
            'medium': 85,
            'high': 95
        }
        return quality_map.get(quality, 85)
    
    def set_quality(self, quality: str) -> None:
        """
        Set the streaming quality
        
        Args:
            quality: Quality level ('low', 'medium', 'high')
        """
        if quality not in QUALITY_THRESHOLDS:
            logger.warning(f"Invalid quality level: {quality}, using medium")
            quality = 'medium'
            
        if quality != self.current_quality:
            logger.info(f"Changing stream quality: {self.current_quality} -> {quality}")
            self.current_quality = quality
    
    def get_frame(self) -> Optional[bytes]:
        """
        Get the current frame
        
        Returns:
            JPEG encoded current frame or None if no frame available
        """
        with self.frame_lock:
            if self.current_frame is None:
                return None
            return self.current_frame
    
    def get_frame_generator(self) -> Generator[bytes, None, None]:
        """
        Get a generator that yields video frames
        
        Returns:
            Generator yielding JPEG frames in multipart/x-mixed-replace format
        """
        if not self.streaming:
            self.start()
            
        while self.streaming:
            # Get the current frame
            frame_data = self.get_frame()
            
            if frame_data:
                # Yield the frame in multipart/x-mixed-replace format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
            else:
                # No frame available, wait a bit
                time.sleep(0.01)

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Sample video path
    video_path = SAMPLE_VIDEO_PATH
    
    # Check if video file exists, use a placeholder message if not
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        logger.info("Please place a sample video at the path specified in config.py")
        exit(1)
    
    # Create and start streaming engine
    engine = StreamEngine(video_path)
    
    try:
        engine.start()
        
        # Simulate quality changes
        qualities = ['low', 'medium', 'high', 'medium', 'low']
        
        for quality in qualities:
            logger.info(f"Setting quality to {quality}")
            engine.set_quality(quality)
            time.sleep(5)  # Stream at this quality for 5 seconds
            
    finally:
        # Stop the engine
        engine.stop()