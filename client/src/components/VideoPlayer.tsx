import { Box, Card, CardContent, IconButton, Typography } from '@mui/material'
import { HighQuality, Settings, FiberManualRecord } from '@mui/icons-material'
import { useEffect, useRef } from 'react'

interface VideoPlayerProps {
  videoQuality: string
}

export const VideoPlayer = ({ videoQuality }: VideoPlayerProps) => {
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    if (videoRef.current) {
      // Video stream URL'sini Flask backend'den alacağız
      videoRef.current.src = `http://localhost:5000/video_feed?quality=${videoQuality}`
    }
  }, [videoQuality])

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flex: 1, p: '16px !important', display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ 
          position: 'relative',
          flex: 1,
          minHeight: 0,
          '&:hover .controls': {
            opacity: 1,
          }
        }}>
          {/* Video Container */}
          <Box 
            sx={{ 
              width: '100%',
              height: '100%',
              bgcolor: 'black',
              borderRadius: 1,
              overflow: 'hidden'
            }}
          >
            <video
              ref={videoRef}
              style={{ 
                width: '100%', 
                height: '100%', 
                objectFit: 'contain'
              }}
              autoPlay
              playsInline
              muted
            />
          </Box>

          {/* Controls Overlay */}
          <Box 
            className="controls"
            sx={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              p: 2,
              background: 'linear-gradient(transparent, rgba(0,0,0,0.7))',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              opacity: 0,
              transition: 'opacity 0.3s ease',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Typography variant="body2" sx={{ color: 'white', mr: 1 }}>
                Quality: {videoQuality}
              </Typography>
              {videoQuality === 'high' ? (
                <HighQuality sx={{ color: '#4ade80' }} />
              ) : (
                <FiberManualRecord sx={{ color: '#fbbf24', width: 20, height: 20 }} />
              )}
            </Box>
            <IconButton 
              size="small" 
              sx={{ color: 'white' }}
            >
              <Settings />
            </IconButton>
          </Box>
        </Box>
      </CardContent>
    </Card>
  )
} 