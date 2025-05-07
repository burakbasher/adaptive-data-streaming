import { 
  Box, Container, CssBaseline, ThemeProvider, Typography, createTheme, 
  Paper, LinearProgress, ButtonGroup, Button, CircularProgress 
} from '@mui/material';
import { useState, useEffect, useRef, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';

const API_URL = 'http://127.0.0.1:3000';
const SOCKET_URL = 'http://localhost:3000';

type QualityLevel = 'low' | 'medium' | 'high';

interface NetworkMetricsType {
  bandwidth: number;
  latency: number;
  packetLoss: number;
}

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#2563eb', light: '#60a5fa', dark: '#1e40af' },
    secondary: { main: '#db2777', light: '#f472b6', dark: '#9d174d' },
    background: { default: '#f8fafc', paper: '#ffffff' },
    text: { primary: '#1e293b', secondary: '#64748b' },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: { fontSize: '2.5rem', fontWeight: 700, color: '#1e293b' },
    h6: { fontWeight: 600 },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        },
      },
    },
  },
});

// Update the VideoPlayer component props type
function VideoPlayer({ 
  videoQuality, 
  onQualityChange,
  onClearBuffer 
}: { 
  videoQuality: QualityLevel; 
  onQualityChange?: (quality: QualityLevel) => void;
  onClearBuffer?: (clearBufferFn: () => void) => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const socketRef = useRef<Socket | null>(null);
  const frameBufferRef = useRef<string[]>([]);
  const timelineRef = useRef<HTMLCanvasElement>(null);
  const [isPlaying, setIsPlaying] = useState(true);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [totalFrames, setTotalFrames] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [bufferSize, setBufferSize] = useState(0);
  const lastFrameTimeRef = useRef<number>(0);
  const requestAnimationRef = useRef<number | undefined>(undefined);
  
  // Constants - Basic buffer size
  const MAX_BUFFER_SIZE = 300; // Standard buffer size
  const TARGET_FPS = 30;
  const FRAME_INTERVAL = 1000 / TARGET_FPS;
  const SPEEDS = [0.5, 1, 1.5, 2];

  const getQualityDetails = (quality: QualityLevel) => {
    switch (quality) {
      case 'low': return { label: 'Low Quality', resolution: '640x360', bitrate: '0.5 Mbps', color: '#ef4444' };
      case 'medium': return { label: 'Medium Quality', resolution: '1280x720', bitrate: '1.5 Mbps', color: '#f59e0b' };
      case 'high': return { label: 'High Quality', resolution: '1920x1080', bitrate: '3.0 Mbps', color: '#22c55e' };
    }
  };

  const qualityDetails = getQualityDetails(videoQuality);

  // Update canvas size when container size changes
  const updateCanvasSize = () => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    const containerWidth = container.clientWidth;
    const containerHeight = container.clientHeight;

    // Calculate aspect ratio based on quality
    let aspectRatio = 16/9; // Default to 16:9

    // Calculate dimensions to fit container while maintaining aspect ratio
    let width, height;
    if (containerWidth / containerHeight > aspectRatio) {
      // Container is wider than needed
      height = containerHeight;
      width = height * aspectRatio;
    } else {
      // Container is taller than needed
      width = containerWidth;
      height = width / aspectRatio;
    }

    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    canvas.width = width;
    canvas.height = height;
  };

  // Draw timeline showing current progress
  const drawTimeline = useCallback((progress: number) => {
    const timeline = timelineRef.current;
    if (!timeline) return;
    
    const ctx = timeline.getContext('2d');
    if (!ctx) return;
    
    ctx.clearRect(0, 0, timeline.width, timeline.height);
    
    // Progress bar
    const fillWidth = progress * timeline.width;
    ctx.fillStyle = '#22c55e';
    ctx.fillRect(0, 0, fillWidth, timeline.height);
    
    // Progress line
    ctx.strokeStyle = '#000';
    ctx.beginPath();
    ctx.moveTo(fillWidth, 0);
    ctx.lineTo(fillWidth, timeline.height);
    ctx.stroke();
  }, []);

  // Play next frame from buffer - simple version
  const playNextFrame = useCallback(() => {
    if (!isPlaying) return;
    
    const now = performance.now();
    const elapsed = now - lastFrameTimeRef.current;
    
    if (elapsed >= FRAME_INTERVAL / playbackSpeed && frameBufferRef.current.length > 0) {
      const frame = frameBufferRef.current.shift() || '';
      const canvas = canvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext('2d');
        if (ctx) {
          const img = new Image();
          img.onload = () => {
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
          };
          img.src = frame;
        }
      }
      lastFrameTimeRef.current = now;
      setBufferSize(frameBufferRef.current.length);
    }
    
    requestAnimationRef.current = requestAnimationFrame(playNextFrame);
  }, [isPlaying, playbackSpeed]);

  // Timeline click handler for seeking
  const handleTimelineClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const timeline = timelineRef.current;
    if (!timeline) return;
    
    const rect = timeline.getBoundingClientRect();
    const position = (e.clientX - rect.left) / rect.width;
    
    socketRef.current?.emit('seek', { position });
  }, []);

  // Play/Pause toggle
  const togglePlayPause = useCallback(() => {
    setIsPlaying(prev => !prev);
    socketRef.current?.emit('play_pause', { is_playing: !isPlaying });
  }, [isPlaying]);

  // Speed control
  const changeSpeed = useCallback((newSpeed: number) => {
    setPlaybackSpeed(newSpeed);
    socketRef.current?.emit('set_speed', { speed: newSpeed });
  }, []);

  // Clear buffer function
  const clearBuffer = useCallback(() => {
    frameBufferRef.current = [];
    setBufferSize(0);
  }, []);

  // Expose the clearBuffer function to parent component via ref
  useEffect(() => {
    // Make clearBuffer available to the parent through a ref if needed
    if (onClearBuffer && typeof onClearBuffer === 'function') {
      onClearBuffer(clearBuffer);
    }
  }, [clearBuffer, onClearBuffer]);

  // Socket connection for receiving frames
  useEffect(() => {
    const socket = io(SOCKET_URL);
    socketRef.current = socket;

    socket.on('connect', () => {
      console.log('Connected to video socket server');
    });

    socket.on('image', (data: string) => {
      if (frameBufferRef.current.length < MAX_BUFFER_SIZE) {
        frameBufferRef.current.push(`data:image/jpeg;base64,${data}`);
        setBufferSize(frameBufferRef.current.length);
      }
    });

    socket.on('video_info', (info: any) => {
      if (info) {
        setCurrentFrame(info.current_frame || 0);
        setTotalFrames(info.total_frames || 0);
        setIsPlaying(info.is_playing || true);
        
        const progress = info.total_frames ? info.current_frame / info.total_frames : 0;
        drawTimeline(progress);
      }
    });

    // Start frame playback
    requestAnimationRef.current = requestAnimationFrame(playNextFrame);

    // Add resize observer to handle container size changes
    const resizeObserver = new ResizeObserver(updateCanvasSize);
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    // Initial size update
    updateCanvasSize();

    return () => {
      socket.disconnect();
      resizeObserver.disconnect();
      if (requestAnimationRef.current) {
        cancelAnimationFrame(requestAnimationRef.current);
      }
    };
  }, [videoQuality, playNextFrame, drawTimeline]);

  return (
    <Paper elevation={0} sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <Box
        ref={containerRef}
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
        <canvas 
          ref={canvasRef}
          style={{
            maxWidth: '100%',
            maxHeight: '100%',
            objectFit: 'contain'
          }}
        />
        
        {/* Simple buffer visualization */}
        <Box sx={{ 
          position: 'absolute',
          bottom: 0,
          left: 0,
          width: '100%',
          height: '4px',
          bgcolor: 'rgba(200, 200, 200, 0.5)',
          pointerEvents: 'none'
        }}>
          <Box sx={{ 
            height: '100%',
            bgcolor: 'rgba(100, 100, 100, 0.5)',
            width: `${(bufferSize / MAX_BUFFER_SIZE) * 100}%`,
            transition: 'width 0.1s ease-out'
          }}/>
        </Box>
      </Box>
      
      {/* Timeline */}
      <Box sx={{ mb: 1 }}>
        <canvas 
          ref={timelineRef}
          width={640}
          height={20}
          onClick={handleTimelineClick}
          style={{ width: '100%', height: '20px', cursor: 'pointer' }}
        />
      </Box>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Typography variant="body2" sx={{ px: 1.5, py: 0.5, borderRadius: 1, fontWeight: 600, mr: 2, color: 'white', bgcolor: qualityDetails.color }}>
            {qualityDetails.label}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mr: 2 }}>{qualityDetails.resolution}</Typography>
          <Typography variant="body2" color="text.secondary">{qualityDetails.bitrate}</Typography>
        </Box>
        <Box>
          <Typography variant="body2">
            Frame: {currentFrame}/{totalFrames} • Buffer: {bufferSize} • Speed: {playbackSpeed}x
          </Typography>
        </Box>
      </Box>

      {/* Video controls */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        {onQualityChange && (
          <ButtonGroup size="small" variant="outlined">
            {(['low', 'medium', 'high'] as QualityLevel[]).map((level) => (
              <Button key={level} onClick={() => onQualityChange(level)} variant={videoQuality === level ? 'contained' : 'outlined'} color={level === 'low' ? 'error' : level === 'medium' ? 'warning' : 'success'}>
                {level.charAt(0).toUpperCase() + level.slice(1)}
              </Button>
            ))}
          </ButtonGroup>
        )}
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" onClick={togglePlayPause}>
            {isPlaying ? 'Pause' : 'Play'}
          </Button>
          <ButtonGroup size="small">
            {SPEEDS.map(speed => (
              <Button 
                key={speed} 
                variant={playbackSpeed === speed ? 'contained' : 'outlined'}
                onClick={() => changeSpeed(speed)}
              >
                {speed}x
              </Button>
            ))}
          </ButtonGroup>
        </Box>
      </Box>
    </Paper>
  );
}

function measureNetworkMetrics(socket: Socket) {
  const startTime = performance.now();
  
  // Ping ölçümü
  fetch('http://localhost:3000/ping', {
    mode: 'cors',
    headers: {
      'Accept': 'application/json'
    },
    // Önbelleği devre dışı bırak
    cache: 'no-store'
  })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      
      // Latency ölçümü (ms)
      const latency = performance.now() - startTime;
      
      // Bandwidth ve paket kaybı ölçümlerini paralel yap
      Promise.all([
        measureActualBandwidth(),
        measurePacketLoss()
      ]).then(([bandwidth, packetLoss]) => {
        // Tüm metrikleri sunucuya gönder
        const metrics = {
          latency,
          packet_loss: packetLoss,
          bandwidth
        };
        
        socket.emit('network_metrics', metrics);
        console.log(`Network metrics - Latency: ${latency.toFixed(2)}ms, Packet Loss: ${packetLoss.toFixed(2)}%, Bandwidth: ${bandwidth.toFixed(2)} Mbps`);
        
        // Ölçüm sonuçlarını lokal state'e de kaydet
        // setNetworkMetrics fonksiyonu varsa kullan
        if (window.updateNetworkMetrics) {
          window.updateNetworkMetrics({
            bandwidth: bandwidth,
            latency: latency,
            packetLoss: packetLoss
          });
        }
      });
    })
    .catch(error => {
      console.warn('Ping test failed, using fallback metrics:', error);
      
      // Bağlantı başarısız olursa varsayılan değerler kullan
      const fallbackMetrics = {
        latency: 200,
        packet_loss: 5,
        bandwidth: 1.5
      };
      
      // Sunucuya varsayılan metrikleri gönder
      socket.emit('network_metrics', fallbackMetrics);
    });
  
  Promise.all([measureActualBandwidth(), measurePacketLoss()])
    .then(([bandwidth, packetLoss]) => {
      // Tüm metrikleri sunucuya gönder
      const metrics = {
        latency,
        packet_loss: packetLoss,
        bandwidth
      };
      
      socket.emit('network_metrics', metrics);
      
      // Client tarafında UI'a metrik güncelleme
      if (typeof window.updateNetworkMetrics === 'function') {
        const clientMetrics = {
          bandwidth: bandwidth,
          latency: latency,
          packetLoss: packetLoss
        };
        window.updateNetworkMetrics(clientMetrics);
        console.log(`UI updated with metrics - Latency: ${latency.toFixed(2)}ms, Packet Loss: ${packetLoss.toFixed(2)}%, Bandwidth: ${bandwidth.toFixed(2)} Mbps`);
      } else {
        console.warn("updateNetworkMetrics function not available");
      }
    });
}

// Gerçek bant genişliğini ölçen fonksiyon - iyileştirilmiş
async function measureActualBandwidth(): Promise<number> {
  try {
    const fileSize = 1024 * 1024; // 1MB
    const startTime = performance.now();
    
    // Test dosyasını indir
    const response = await fetch('http://localhost:3000/test-file', {
      cache: 'no-store', // Önbelleği devre dışı bırak
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    });
    
    if (!response.ok) throw new Error('Test file download failed');
    
    // ArrayBuffer olarak dosyayı al
    await response.arrayBuffer();
    const endTime = performance.now();
    
    // Süreyi hesapla (saniye)
    const durationInSeconds = (endTime - startTime) / 1000;
    
    // Çok kısa sürdüyse (önbellek veya hata durumu) geçersiz kabul et
    if (durationInSeconds < 0.1) {
      console.warn('Download time too short, might be cached or error');
      return 5.0; // Varsayılan değer
    }
    
    // Bant genişliğini hesapla (Mbps)
    const bandwidth = (fileSize * 8) / 1000000 / durationInSeconds;
    
    // Sonucu makul bir aralıkta tut (0.5 - 100 Mbps)
    return Math.min(Math.max(bandwidth, 0.5), 100);
  } catch (error) {
    console.error("Bandwidth measurement failed:", error);
    return 3.0; // Varsayılan değer
  }
}

// Paket kaybını ölçmeyi güçlendirelim
async function measurePacketLoss(): Promise<number> {
  try {
    const pingCount = 10; // Daha fazla ping
    let successCount = 0;
    const pingPromises = [];
    
    // Tüm ping isteklerini paralel olarak yap
    for (let i = 0; i < pingCount; i++) {
      const promise = fetch(`http://localhost:3000/ping?seq=${i}&t=${Date.now()}`, {
        mode: 'cors',
        cache: 'no-store',
        headers: { 
          'Accept': 'application/json',
          'Cache-Control': 'no-cache'
        }
      })
      .then(res => {
        if (res.ok) successCount++;
        return res.ok;
      })
      .catch(() => false); // Hata durumunda başarısız kabul et
      
      pingPromises.push(promise);
    }
    
    // Tüm ping isteklerinin tamamlanmasını bekle
    await Promise.all(pingPromises);
    
    // Paket kaybı yüzdesini hesapla
    const packetLoss = ((pingCount - successCount) / pingCount) * 100;
    return packetLoss;
  } catch (error) {
    console.error("Packet loss measurement failed:", error);
    return 1.0; // Varsayılan değer
  }
}

// Global değişken ekle, diğer bileşenlerin ağ metriklerine erişebilmesi için
window.updateNetworkMetrics = null;

// 5 saniyede bir ağ metriklerini ölç
const socket = io(SOCKET_URL);
setInterval(() => measureNetworkMetrics(socket), 5000);

function App() {
  // Change default to 'video' instead of 'camera'
  const [streamSource, setStreamSource] = useState<'camera' | 'video'>('video');
  const [videoQuality, setVideoQuality] = useState<QualityLevel>('medium');
  const [networkMetrics, setNetworkMetrics] = useState<NetworkMetricsType>({ bandwidth: 0, latency: 0, packetLoss: 0 });
  const [controlMode, setControlMode] = useState<'manual' | 'adaptive'>('manual');
  // Ref for video player clearBuffer function
  const clearBufferRef = useRef<(() => void) | null>(null);

  // Set the clearBuffer function from the VideoPlayer component
  const handleClearBuffer = useCallback((clearBufferFn: () => void) => {
    clearBufferRef.current = clearBufferFn;
  }, []);

  // Fetch network metrics and quality info
  /*
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const res = await fetch(`${API_URL}/api/network-metrics`);
        const data = await res.json();
        
        // Always update network metrics, regardless of mode
        setNetworkMetrics({
          bandwidth: data.bandwidth || 0,
          latency: data.latency || 0,
          packetLoss: data.packet_loss || 0,
        });
        
        // Only update quality in adaptive mode
        if (data.current_quality && controlMode === 'adaptive') {
          setVideoQuality(data.current_quality as QualityLevel);
        }
      } catch (err) {
        console.error('Metric fetch error:', err);
      }
    };
    
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 500);
    return () => clearInterval(interval);
  }, [controlMode]);
  */
  
  // Sadece kalite bilgisini çeken daha seyrek bir API çağrısı ekle
  useEffect(() => {
    // Sadece adaptive modda kaliteyi güncelle
    if (controlMode === 'adaptive') {
      const fetchQualityInfo = async () => {
        try {
          const res = await fetch(`${API_URL}/api/network-metrics`);
          const data = await res.json();
          
          if (data.current_quality) {
            setVideoQuality(data.current_quality as QualityLevel);
          }
        } catch (err) {
          console.error('Quality info fetch error:', err);
        }
      };
      
      fetchQualityInfo();
      const interval = setInterval(fetchQualityInfo, 2000); // Her 2 saniyede bir
      return () => clearInterval(interval);
    }
  }, [controlMode]);
  
  // UpdateNetworkMetrics fonksiyonunu global değişkene daha erken at
  useEffect(() => {
    // Global değişkene atama yap
    window.updateNetworkMetrics = (metrics: NetworkMetricsType) => {
      console.log("UI updating metrics:", metrics);
      setNetworkMetrics(metrics);
    };
    
    return () => {
      window.updateNetworkMetrics = null;
    };
  }, []);

  // Handle quality change
  const changeQuality = async (quality: QualityLevel) => {
    try {
      await fetch(`${API_URL}/api/set-quality/${quality}`, { method: 'POST' });
      setVideoQuality(quality);
    } catch (err) {
      console.error('Quality change error:', err);
    }
  };

  // Handle source change with buffer clearing
  const handleSourceChange = async (source: 'camera' | 'video') => {
    try {
      // Clear the buffer first when switching sources
      if (clearBufferRef.current) {
        console.log(`Clearing buffer before switching to ${source} mode`);
        clearBufferRef.current();
      }
      
      setStreamSource(source);
      await fetch(`${API_URL}/api/set-source/${source}`, { method: 'POST' });
    } catch (err) {
      console.error('Source change error:', err);
    }
  };

  // Handle control mode change
  const handleControlModeChange = async (mode: 'manual' | 'adaptive') => {
    try {
      setControlMode(mode);
      await fetch(`${API_URL}/api/set-control-mode/${mode}`, { method: 'POST' });
    } catch (err) {
      console.error('Control mode change error:', err);
    }
  };

  // Start with video on initial load instead of camera
  useEffect(() => {
    handleSourceChange('video');
  }, []);

  // UpdateNetworkMetrics fonksiyonunu global değişkene at
  useEffect(() => {
    window.updateNetworkMetrics = setNetworkMetrics;
    
    return () => {
      window.updateNetworkMetrics = null;
    };
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ minHeight: '100vh', width: '100vw', bgcolor: 'background.default', color: 'text.primary', background: 'linear-gradient(180deg, #e0f2fe 0%, #f8fafc 100%)', overflow: 'hidden' }}>
        <Container maxWidth={false} sx={{ height: '100vh', py: 3, px: { xs: 2, sm: 4 }, display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ mb: 3, textAlign: 'center' }}>
            <Typography variant="h1" gutterBottom>Adaptive Streaming Dashboard</Typography>
            <Typography variant="subtitle1" color="text.secondary">Real-time video quality adaptation based on network conditions</Typography>
          </Box>
          
          {/* Stream Settings Controls */}
          <Paper elevation={0} sx={{ p: 2, mb: 3 }}>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
              <Box>
                <Typography variant="subtitle2" gutterBottom>Source</Typography>
                <ButtonGroup>
                  <Button 
                    variant={streamSource === 'video' ? 'contained' : 'outlined'}
                    onClick={() => handleSourceChange('video')}
                  >
                    Video
                  </Button>
                  <Button 
                    variant={streamSource === 'camera' ? 'contained' : 'outlined'}
                    onClick={() => handleSourceChange('camera')}
                  >
                    Camera
                  </Button>
                </ButtonGroup>
              </Box>
              
              <Box>
                <Typography variant="subtitle2" gutterBottom>Control Mode</Typography>
                <ButtonGroup>
                  <Button 
                    variant={controlMode === 'manual' ? 'contained' : 'outlined'}
                    onClick={() => handleControlModeChange('manual')}
                  >
                    Manual
                  </Button>
                  <Button 
                    variant={controlMode === 'adaptive' ? 'contained' : 'outlined'}
                    onClick={() => handleControlModeChange('adaptive')}
                  >
                    Adaptive
                  </Button>
                </ButtonGroup>
              </Box>
            </Box>
          </Paper>
          
          <Box sx={{ display: 'grid', gap: 3, gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr' }, flex: 1, minHeight: 0 }}>
            <VideoPlayer videoQuality={videoQuality} onQualityChange={controlMode === 'manual' ? changeQuality : undefined} onClearBuffer={handleClearBuffer} />
            <Paper elevation={0} sx={{ p: 3, display: 'flex', flexDirection: 'column' }}>
              {/* Network Performance metrikleri - her zaman görüntülenecek */}
              <Typography variant="h5" fontWeight="600" sx={{ mb: 3 }}>Network Performance</Typography>
              {(['bandwidth', 'latency', 'packetLoss'] as const).map((key) => {
                const value = networkMetrics[key];
                const thresholds = {
                  bandwidth: { good: 5, medium: 2 },
                  latency: { good: 100, medium: 200 },
                  packetLoss: { good: 2, medium: 5 },
                };
                const maxValues = { bandwidth: 10, latency: 500, packetLoss: 15 };
                const status = key === 'bandwidth' ? (value >= thresholds[key].good ? 'good' : value >= thresholds[key].medium ? 'medium' : 'poor') : (value <= thresholds[key].good ? 'good' : value <= thresholds[key].medium ? 'medium' : 'poor');
                const progress = key === 'bandwidth' ? Math.min(100, (value / maxValues[key]) * 100) : Math.max(0, 100 - Math.min(100, (value / maxValues[key]) * 100));
                const color = status === 'good' ? '#22c55e' : status === 'medium' ? '#f59e0b' : '#ef4444';
                return (
                  <Box key={key} sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Typography variant="body1" sx={{ flexGrow: 1 }}>{key.charAt(0).toUpperCase() + key.slice(1)}</Typography>
                      <Typography variant="caption" sx={{ px: 1, py: 0.5, borderRadius: 1, fontWeight: 600, color: 'white', bgcolor: color }}>{status.charAt(0).toUpperCase() + status.slice(1)}</Typography>
                    </Box>
                    <Typography variant="h4" fontWeight="700" sx={{ mb: 1 }}>{value.toFixed(2)}<Typography component="span" variant="body2" color="text.secondary" sx={{ ml: 1 }}>{key === 'bandwidth' ? 'Mbps' : key === 'latency' ? 'ms' : '%'}</Typography></Typography>
                    <LinearProgress variant="determinate" value={progress} sx={{ height: 6, borderRadius: 1, bgcolor: 'rgba(0,0,0,0.05)', '& .MuiLinearProgress-bar': { borderRadius: 1, bgcolor: color } }} />
                  </Box>
                );
              })}
              
              {/* Kontrol modu bilgilendirmesi - adaptive mode için bilgi mesajı */}
              {controlMode === 'adaptive' && (
                <Box sx={{ mt: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                  <Typography variant="subtitle1" fontWeight="600" gutterBottom>
                    Adaptive Quality Control Active
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    The system is automatically adjusting quality based on network conditions.
                  </Typography>
                </Box>
              )}
              
              {/* Kalite kontrolü - sadece manual modda gösterilecek */}
              {controlMode === 'manual' && (
                <Box sx={{ mt: 'auto', pt: 3, borderTop: '1px solid', borderColor: 'rgba(0,0,0,0.1)' }}>
                  <Typography variant="subtitle2" gutterBottom>Manual Quality Control</Typography>
                  <ButtonGroup fullWidth size="small" variant="outlined">
                    {(['low', 'medium', 'high'] as QualityLevel[]).map((level) => (
                      <Button key={level} onClick={() => changeQuality(level)} variant={videoQuality === level ? 'contained' : 'outlined'} color={level === 'low' ? 'error' : level === 'medium' ? 'warning' : 'success'}>{level.charAt(0).toUpperCase() + level.slice(1)}</Button>
                    ))}
                  </ButtonGroup>
                </Box>
              )}
            </Paper>
          </Box>
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;

// Typescript için global değişken tanımı (window nesnesine yeni özellik ekle)
declare global {
  interface Window {
    updateNetworkMetrics: ((metrics: NetworkMetricsType) => void) | null;
  }
}