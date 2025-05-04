import { Box, Container, CssBaseline, ThemeProvider, Typography, createTheme, Paper, LinearProgress, ButtonGroup, Button } from '@mui/material'
import { useState, useEffect } from 'react'

// API URL - Flask sunucusunun adresi
const API_URL = 'http://127.0.0.1:5000';

// Quality ve Metric tipleri
type QualityLevel = 'low' | 'medium' | 'high';

interface NetworkMetricsType {
  bandwidth: number;
  latency: number;
  packetLoss: number;
}

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

// VideoPlayer props tipi
interface VideoPlayerProps {
  videoQuality: QualityLevel;
  onQualityChange?: (quality: QualityLevel) => void;
}

// VideoPlayer bileşeni
function VideoPlayer({ videoQuality, onQualityChange }: VideoPlayerProps) {
  // Timestamp ile video URL'i oluşturma
  const getVideoUrl = () => {
    const timestamp = new Date().getTime();
    return `${API_URL}/video_feed?t=${timestamp}&quality=${videoQuality}`;
  };

  // Kalite detaylarını belirleme
  const getQualityDetails = (quality: QualityLevel) => {
    switch (quality) {
      case 'low':
        return { label: 'Low Quality', resolution: '640x360', bitrate: '0.5 Mbps', color: '#ef4444' };
      case 'medium':
        return { label: 'Medium Quality', resolution: '1280x720', bitrate: '1.5 Mbps', color: '#f59e0b' };
      case 'high':
        return { label: 'High Quality', resolution: '1920x1080', bitrate: '3.0 Mbps', color: '#22c55e' };
      default:
        return { label: 'Medium Quality', resolution: '1280x720', bitrate: '1.5 Mbps', color: '#f59e0b' };
    }
  };

  const qualityDetails = getQualityDetails(videoQuality);

  return (
    <Paper
      elevation={0}
      sx={{
        p: 2,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      <Box
        sx={{
          flex: 1,
          mb: 2,
          borderRadius: 2,
          overflow: 'hidden',
          bgcolor: 'black',
          position: 'relative',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <img
          src={getVideoUrl()}
          alt="Video Stream"
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'contain',
          }}
          onError={(e) => {
            // Hata durumunda görüntüyü yeniden yükle
            const img = e.target as HTMLImageElement;
            img.src = getVideoUrl();
          }}
        />
      </Box>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Typography
            variant="body2"
            sx={{
              px: 1.5,
              py: 0.5,
              borderRadius: 1,
              fontWeight: 600,
              mr: 2,
              color: 'white',
              bgcolor: qualityDetails.color,
            }}
          >
            {qualityDetails.label}
          </Typography>

          <Typography variant="body2" color="text.secondary" sx={{ mr: 2 }}>
            {qualityDetails.resolution}
          </Typography>

          <Typography variant="body2" color="text.secondary">
            {qualityDetails.bitrate}
          </Typography>
        </Box>

        {onQualityChange && (
          <ButtonGroup size="small" variant="outlined">
            <Button
              onClick={() => onQualityChange('low')}
              variant={videoQuality === 'low' ? 'contained' : 'outlined'}
              color="error"
            >
              Low
            </Button>
            <Button
              onClick={() => onQualityChange('medium')}
              variant={videoQuality === 'medium' ? 'contained' : 'outlined'}
              color="warning"
            >
              Medium
            </Button>
            <Button
              onClick={() => onQualityChange('high')}
              variant={videoQuality === 'high' ? 'contained' : 'outlined'}
              color="success"
            >
              High
            </Button>
          </ButtonGroup>
        )}
      </Box>
    </Paper>
  );
}

// NetworkMetrics props tipi
interface NetworkMetricsProps {
  metrics: NetworkMetricsType;
  currentQuality?: QualityLevel;
  onQualityChange?: (quality: QualityLevel) => void;
}

// NetworkMetrics bileşeni
function NetworkMetrics({ metrics, currentQuality = 'medium', onQualityChange }: NetworkMetricsProps) {
  // Durum göstergeleri için eşik değerleri
  const thresholds = {
    bandwidth: { good: 5, medium: 2 }, // Mbps
    latency: { good: 100, medium: 200 }, // ms
    packetLoss: { good: 2, medium: 5 }, // %
  };

  // Metrik durumunu hesapla
  const getMetricStatus = (name: string, value: number): 'good' | 'medium' | 'poor' => {
    if (name === 'bandwidth') {
      // Bant genişliği için, yüksek değerler iyi
      if (value >= thresholds.bandwidth.good) return 'good';
      if (value >= thresholds.bandwidth.medium) return 'medium';
      return 'poor';
    } else {
      // Gecikme ve paket kaybı için, düşük değerler iyi
      if (name === 'latency') {
        if (value <= thresholds.latency.good) return 'good';
        if (value <= thresholds.latency.medium) return 'medium';
        return 'poor';
      } else if (name === 'packetLoss') {
        if (value <= thresholds.packetLoss.good) return 'good';
        if (value <= thresholds.packetLoss.medium) return 'medium';
        return 'poor';
      }
      return 'medium'; // Varsayılan değer
    }
  };

  // Progress bar değeri hesapla (0-100 arası)
  const calculateProgress = (name: string, value: number): number => {
    const maxValues = {
      bandwidth: 10, // Mbps
      latency: 500, // ms
      packetLoss: 15, // %
    };

    if (name === 'bandwidth') {
      // Bant genişliği için, yüksek değerler iyi
      return Math.min(100, (value / maxValues.bandwidth) * 100);
    } else if (name === 'latency') {
      // Gecikme için, düşük değerler iyi (ters ölçek)
      return Math.max(0, 100 - Math.min(100, (value / maxValues.latency) * 100));
    } else if (name === 'packetLoss') {
      // Paket kaybı için, düşük değerler iyi (ters ölçek)
      return Math.max(0, 100 - Math.min(100, (value / maxValues.packetLoss) * 100));
    }
    return 50; // Varsayılan değer
  };

  // Status rengini belirle
  const getStatusColor = (status: 'good' | 'medium' | 'poor'): string => {
    switch (status) {
      case 'good': return '#22c55e';
      case 'medium': return '#f59e0b';
      case 'poor': return '#ef4444';
      default: return '#22c55e';
    }
  };

  // Metrik göstergesi için prop tipi
  interface MetricItemProps {
    name: string;
    label: string;
    value: number;
    unit: string;
  }

  // Metrik göstergesi
  const MetricItem = ({ name, label, value, unit }: MetricItemProps) => {
    const status = getMetricStatus(name, value);
    const progress = calculateProgress(name, value);
    const color = getStatusColor(status);
    
    return (
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Typography variant="body1" sx={{ flexGrow: 1 }}>
            {label}
          </Typography>
          
          <Typography
            variant="caption"
            sx={{
              px: 1,
              py: 0.5,
              borderRadius: 1,
              fontWeight: 600,
              color: 'white',
              bgcolor: color,
            }}
          >
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </Typography>
        </Box>
        
        <Typography variant="h4" fontWeight="700" sx={{ mb: 1 }}>
          {value.toFixed(2)}
          <Typography component="span" variant="body2" color="text.secondary" sx={{ ml: 1 }}>
            {unit}
          </Typography>
        </Typography>
        
        <LinearProgress
          variant="determinate"
          value={progress}
          sx={{
            height: 6,
            borderRadius: 1,
            bgcolor: 'rgba(0,0,0,0.05)',
            '& .MuiLinearProgress-bar': {
              borderRadius: 1,
              bgcolor: color,
            }
          }}
        />
      </Box>
    );
  };

  return (
    <Paper
      elevation={0}
      sx={{
        p: 3,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Typography variant="h5" fontWeight="600" sx={{ mb: 3 }}>
        Network Performance
      </Typography>
      
      <MetricItem
        name="bandwidth"
        label="Bandwidth"
        value={metrics.bandwidth}
        unit="Mbps"
      />
      
      <MetricItem
        name="latency"
        label="Latency"
        value={metrics.latency}
        unit="ms"
      />
      
      <MetricItem
        name="packetLoss"
        label="Packet Loss"
        value={metrics.packetLoss}
        unit="%"
      />
      
      {onQualityChange && (
        <Box sx={{ mt: 'auto', pt: 3, borderTop: '1px solid', borderColor: 'rgba(0,0,0,0.1)' }}>
          <Typography variant="subtitle2" gutterBottom>
            Manual Quality Control
          </Typography>
          
          <ButtonGroup fullWidth size="small" variant="outlined">
            <Button
              onClick={() => onQualityChange('low')}
              variant={currentQuality === 'low' ? 'contained' : 'outlined'}
              color="error"
            >
              Low
            </Button>
            <Button
              onClick={() => onQualityChange('medium')}
              variant={currentQuality === 'medium' ? 'contained' : 'outlined'}
              color="warning"
            >
              Medium
            </Button>
            <Button
              onClick={() => onQualityChange('high')}
              variant={currentQuality === 'high' ? 'contained' : 'outlined'}
              color="success"
            >
              High
            </Button>
          </ButtonGroup>
        </Box>
      )}
    </Paper>
  );
}

// Ana uygulama bileşeni
function App() {
  const [videoQuality, setVideoQuality] = useState<QualityLevel>('medium')
  const [networkMetrics, setNetworkMetrics] = useState<NetworkMetricsType>({
    bandwidth: 0,
    latency: 0,
    packetLoss: 0,
  })

  // API'den ağ metriklerini alma fonksiyonu
  const fetchNetworkMetrics = async () => {
    try {
      const response = await fetch(`${API_URL}/api/network-metrics`);
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      setNetworkMetrics({
        bandwidth: data.bandwidth || 0,
        latency: data.latency || 0,
        packetLoss: data.packet_loss || 0,
      });
      
      // Kalite değişikliğini kontrol et
      if (data.current_quality && data.current_quality !== videoQuality) {
        setVideoQuality(data.current_quality as QualityLevel);
      }
    } catch (error) {
      console.error('Error fetching network metrics:', error);
    }
  };

  // Kalite ayarını manuel olarak değiştirme fonksiyonu
  const changeQuality = async (quality: QualityLevel) => {
    try {
      const response = await fetch(`${API_URL}/api/set-quality/${quality}`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      setVideoQuality(quality);
    } catch (error) {
      console.error('Error changing quality:', error);
    }
  };

  // Komponent yüklendiğinde ve belirli aralıklarla metrikleri güncelle
  useEffect(() => {
    // İlk yüklemede metrikleri al
    fetchNetworkMetrics();
    
    // Düzenli aralıklarla metrikleri güncelle
    const intervalId = setInterval(fetchNetworkMetrics, 2000);
    
    // Komponent unmount edildiğinde interval'i temizle
    return () => clearInterval(intervalId);
  }, []);

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
            <VideoPlayer 
              videoQuality={videoQuality} 
              onQualityChange={changeQuality}
            />
            <NetworkMetrics 
              metrics={networkMetrics}
              onQualityChange={changeQuality} 
              currentQuality={videoQuality}
            />
          </Box>
        </Container>
      </Box>
    </ThemeProvider>
  )
}

export default App