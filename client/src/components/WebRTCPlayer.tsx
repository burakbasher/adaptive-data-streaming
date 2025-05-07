import React from 'react';
import { useWebRTCPlayer } from '../hooks/useWebRTCPlayer';

interface WebRTCPlayerProps {
  serverUrl: string;
  stunServer?: string;
  className?: string;
}

export const WebRTCPlayer: React.FC<WebRTCPlayerProps> = ({
  serverUrl,
  stunServer,
  className,
}) => {
  const { videoRef, isConnected, error } = useWebRTCPlayer({
    serverUrl,
    stunServer,
  });

  return (
    <div className={`webrtc-player ${className || ''}`}>
      <video
        ref={videoRef}
        autoPlay
        playsInline
        style={{ width: '100%', maxWidth: '800px' }}
      />
      {!isConnected && !error && (
        <div className="connection-status">Connecting...</div>
      )}
      {error && <div className="error-message">Error: {error}</div>}
    </div>
  );
}; 