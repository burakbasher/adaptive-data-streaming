"""
WebRTC Server Module
Handles real-time video streaming using WebRTC
"""

import asyncio
import json
import logging
import os
from aiohttp import web
from av import VideoFrame
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder
import cv2
import numpy as np
from aiohttp_cors import setup as cors_setup, ResourceOptions, CorsViewMixin

# Import our custom modules
from stream_engine import StreamEngine
from config import SERVER_HOST, SERVER_PORT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('webrtc_server')

# Global list to keep track of peer connections
pcs = set()

class VideoStreamTrack(MediaStreamTrack):
    """Video stream track that adapts quality based on network conditions"""
    
    kind = "video"
    
    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(0)  # Open webcam
        if not self.cap.isOpened():
            raise RuntimeError("Could not open webcam")
        
        # Set webcam properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        self.last_frame = None
    
    async def recv(self):
        """Receive the next video frame"""
        ret, frame = self.cap.read()
        if not ret:
            # If no frame available, return black frame
            frame = np.zeros((720, 1280, 3), dtype=np.uint8)
            
        # Convert BGR to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create VideoFrame
        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        pts, time_base = await self.next_timestamp()
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame
    
    def stop(self):
        """Clean up resources"""
        if self.cap is not None:
            self.cap.release()

async def offer(request):
    """Handle WebRTC offer"""
    params = await request.json()
    offer = RTCSessionDescription(
        sdp=params["sdp"],
        type=params["type"]
    )
    
    # Create peer connection with STUN server configuration
    pc = RTCPeerConnection(configuration=RTCConfiguration(
        iceServers=[
            RTCIceServer(urls=["stun:stun.l.google.com:19302"])
        ]
    ))
    pcs.add(pc)
    
    # Create video track
    video = VideoStreamTrack()
    
    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        logger.info(f"Connection state changed to: {pc.connectionState}")
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)
    
    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        logger.info(f"ICE connection state: {pc.iceConnectionState}")
        if pc.iceConnectionState == "failed":
            await pc.close()
            pcs.discard(pc)
    
    # Add video track
    pc.addTrack(video)
    
    # Handle the offer
    await pc.setRemoteDescription(offer)
    
    # Create and set local description
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    
    return web.Response(
        content_type="application/json",
        text=json.dumps({
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        })
    )

async def network_metrics(request):
    """Return simulated network metrics"""
    return web.json_response({
        "bandwidth": 5.0,  # Mbps
        "latency": 50,     # ms
        "packetLoss": 0.1  # %
    })

async def index(request):
    """Serve the main page"""
    return web.FileResponse('client/index.html')

async def on_shutdown(app):
    """Cleanup when server shuts down"""
    # Close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()

async def init_app():
    """Initialize the WebRTC server application"""
    app = web.Application()
    
    # Setup CORS
    cors = cors_setup(app, defaults={
        "*": ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })
    
    # Add routes
    app.router.add_get("/", index)
    app.router.add_post("/offer", offer)
    app.router.add_get("/api/network-metrics", network_metrics)
    
    # Configure CORS for all routes
    for route in list(app.router.routes()):
        cors.add(route)
    
    # Add shutdown handler
    app.on_shutdown.append(on_shutdown)
    
    # Serve static files from the client directory
    client_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'client')
    app.router.add_static('/', client_dir)
    
    return app

def main():
    """Main entry point"""
    logger.info("Starting WebRTC Streaming Server")
    
    # Create and run the application
    app = asyncio.run(init_app())
    web.run_app(app, host='0.0.0.0', port=5000)

if __name__ == "__main__":
    main() 