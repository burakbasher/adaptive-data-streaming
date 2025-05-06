import React, { useEffect, useRef, useState } from 'react';
import './WebRTCVideo.css';

interface WebRTCVideoProps {
  serverUrl: string;
}

const WebRTCVideo: React.FC<WebRTCVideoProps> = ({ serverUrl }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    let pc: RTCPeerConnection | null = null;

    const startStream = async () => {
      try {
        // Create peer connection
        pc = new RTCPeerConnection({
          iceServers: [
            { urls: 'stun:stun.l.google.com:19302' }
          ]
        });

        // Handle incoming video stream
        pc.ontrack = (event) => {
          if (videoRef.current) {
            videoRef.current.srcObject = event.streams[0];
            setIsConnected(true);
          }
        };

        // Handle connection state changes
        pc.onconnectionstatechange = () => {
          console.log('Connection state:', pc?.connectionState);
          if (pc?.connectionState === 'failed') {
            setError('Connection failed');
            setIsConnected(false);
          }
        };

        // Create offer
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        // Send offer to server
        const response = await fetch(`${serverUrl}/offer`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            sdp: pc.localDescription?.sdp,
            type: pc.localDescription?.type,
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to connect to server');
        }

        // Set remote description from server's answer
        const answer = await response.json();
        await pc.setRemoteDescription(new RTCSessionDescription(answer));

      } catch (err) {
        console.error('Error starting stream:', err);
        setError(err instanceof Error ? err.message : 'Failed to start stream');
        setIsConnected(false);
      }
    };

    startStream();

    // Cleanup
    return () => {
      if (pc) {
        pc.close();
        setIsConnected(false);
      }
    };
  }, [serverUrl]);

  return (
    <div className="webrtc-video-container">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        style={{ width: '100%', maxWidth: '800px' }}
      />
      {error && (
        <div className="error-message">
          Error: {error}
        </div>
      )}
      {!isConnected && !error && (
        <div className="connecting-message">
          Connecting to stream...
        </div>
      )}
    </div>
  );
};

export default WebRTCVideo; 