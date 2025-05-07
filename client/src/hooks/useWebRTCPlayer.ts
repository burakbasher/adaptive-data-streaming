import { useEffect, useRef, useState } from 'react';
import { io, Socket } from 'socket.io-client';

interface WebRTCPlayerOptions {
  serverUrl: string;
  stunServer?: string;
}

interface WebRTCPlayerState {
  isConnected: boolean;
  error: string | null;
}

export const useWebRTCPlayer = (options: WebRTCPlayerOptions) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const peerConnectionRef = useRef<RTCPeerConnection | null>(null);
  const socketRef = useRef<Socket | null>(null);
  const [state, setState] = useState<WebRTCPlayerState>({
    isConnected: false,
    error: null,
  });

  useEffect(() => {
    const initializeWebRTC = async () => {
      try {
        // Initialize Socket.IO connection
        socketRef.current = io(options.serverUrl);

        // Create RTCPeerConnection
        const configuration: RTCConfiguration = {
          iceServers: [
            {
              urls: options.stunServer || 'stun:stun.l.google.com:19302',
            },
          ],
        };

        peerConnectionRef.current = new RTCPeerConnection(configuration);

        // Handle ICE candidates
        peerConnectionRef.current.onicecandidate = (event) => {
          if (event.candidate) {
            socketRef.current?.emit('ice_candidate', {
              candidate: event.candidate.candidate,
              sdpMid: event.candidate.sdpMid,
              sdpMLineIndex: event.candidate.sdpMLineIndex,
            });
          }
        };

        // Handle connection state changes
        peerConnectionRef.current.onconnectionstatechange = () => {
          setState((prev) => ({
            ...prev,
            isConnected: peerConnectionRef.current?.connectionState === 'connected',
          }));
        };

        // Handle incoming tracks
        peerConnectionRef.current.ontrack = (event) => {
          if (videoRef.current && event.streams[0]) {
            videoRef.current.srcObject = event.streams[0];
          }
        };

        // Create and send offer
        const offer = await peerConnectionRef.current.createOffer();
        await peerConnectionRef.current.setLocalDescription(offer);

        socketRef.current.emit('webrtc_offer', {
          sdp: offer.sdp,
          type: offer.type,
        });

        // Handle answer from server
        socketRef.current.on('webrtc_answer', async (data) => {
          if (peerConnectionRef.current) {
            await peerConnectionRef.current.setRemoteDescription(
              new RTCSessionDescription(data)
            );
          }
        });

        // Handle ICE candidates from server
        socketRef.current.on('ice_candidate', async (data) => {
          if (peerConnectionRef.current) {
            await peerConnectionRef.current.addIceCandidate(
              new RTCIceCandidate(data)
            );
          }
        });

      } catch (error) {
        setState((prev) => ({
          ...prev,
          error: error instanceof Error ? error.message : 'Unknown error occurred',
        }));
      }
    };

    initializeWebRTC();

    return () => {
      // Cleanup
      if (peerConnectionRef.current) {
        peerConnectionRef.current.close();
      }
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, [options.serverUrl, options.stunServer]);

  return {
    videoRef,
    ...state,
  };
}; 