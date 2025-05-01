import { Box, Container, CssBaseline, ThemeProvider, Typography, createTheme } from '@mui/material'
import { useState } from 'react'
import { VideoPlayer } from './components/VideoPlayer'
import { NetworkMetrics } from './components/NetworkMetrics'

// Create a theme instance
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#2563eb', // Modern mavi
      light: '#60a5fa',
      dark: '#1e40af',
    },
    secondary: {
      main: '#db2777', // Modern pembe
      light: '#f472b6',
      dark: '#9d174d',
    },
    background: {
      default: '#f8fafc',
      paper: '#ffffff',
    },
    text: {
      primary: '#1e293b',
      secondary: '#64748b',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      color: '#1e293b',
    },
    h6: {
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        },
      },
    },
  },
})

function App() {
  const [videoQuality, setVideoQuality] = useState<string>('medium')
  const [networkMetrics, setNetworkMetrics] = useState({
    bandwidth: 0,
    latency: 0,
    packetLoss: 0,
  })

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box
        sx={{
          minHeight: '100vh',
          width: '100vw',
          bgcolor: 'background.default',
          color: 'text.primary',
          background: 'linear-gradient(180deg, #e0f2fe 0%, #f8fafc 100%)',
          overflow: 'hidden',
        }}
      >
        <Container 
          maxWidth={false} 
          sx={{ 
            height: '100vh',
            py: 3,
            px: { xs: 2, sm: 4 },
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <Box sx={{ mb: 3, textAlign: 'center' }}>
            <Typography variant="h1" gutterBottom>
              Adaptive Streaming Dashboard
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              Real-time video quality adaptation based on network conditions
            </Typography>
          </Box>
          <Box
            sx={{
              display: 'grid',
              gap: 3,
              gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr' },
              flex: 1,
              minHeight: 0, // Bu önemli, flex container içinde scroll için
            }}
          >
            <VideoPlayer videoQuality={videoQuality} />
            <NetworkMetrics metrics={networkMetrics} />
          </Box>
        </Container>
      </Box>
    </ThemeProvider>
  )
}

export default App
