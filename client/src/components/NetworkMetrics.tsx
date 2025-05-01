import { Box, Card, CardContent, Chip, Divider, Grid, LinearProgress, Typography } from '@mui/material'
import { NetworkCheck, Speed, Warning, Timer } from '@mui/icons-material'

interface NetworkMetricsProps {
  metrics: {
    bandwidth: number
    latency: number
    packetLoss: number
  }
}

const getQualityColor = (value: number, thresholds: { good: number; medium: number }) => {
  if (value <= thresholds.good) return '#4ade80'
  if (value <= thresholds.medium) return '#fbbf24'
  return '#ef4444'
}

const getQualityLabel = (value: number, thresholds: { good: number; medium: number }) => {
  if (value <= thresholds.good) return 'Good'
  if (value <= thresholds.medium) return 'Fair'
  return 'Poor'
}

const MetricCard = ({ 
  title, 
  value, 
  unit, 
  icon, 
  progress,
  thresholds,
  reverseQuality = false
}: { 
  title: string
  value: number
  unit: string
  icon: React.ReactNode
  progress: number
  thresholds: { good: number; medium: number }
  reverseQuality?: boolean
}) => {
  const qualityValue = reverseQuality ? -value : value
  const color = getQualityColor(qualityValue, thresholds)
  const label = getQualityLabel(qualityValue, thresholds)

  return (
    <Box sx={{ mb: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1, justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Box sx={{ 
            mr: 1.5, 
            display: 'flex', 
            alignItems: 'center',
            color: color
          }}>
            {icon}
          </Box>
          <Typography variant="subtitle2" color="text.secondary">
            {title}
          </Typography>
        </Box>
        <Chip 
          label={label} 
          size="small"
          sx={{ 
            backgroundColor: `${color}20`,
            color: color,
            fontWeight: 600
          }}
        />
      </Box>
      <Typography variant="h4" sx={{ mb: 1 }}>
        {value.toFixed(2)}
        <Typography component="span" variant="body2" color="text.secondary"> {unit}</Typography>
      </Typography>
      <LinearProgress 
        variant="determinate" 
        value={progress} 
        sx={{ 
          height: 6, 
          borderRadius: 3,
          backgroundColor: 'rgba(0,0,0,0.05)',
          '& .MuiLinearProgress-bar': {
            borderRadius: 3,
            backgroundColor: color
          }
        }} 
      />
    </Box>
  )
}

export const NetworkMetrics = ({ metrics }: NetworkMetricsProps) => {
  // Ping değerini latency'den hesaplıyoruz (round trip time)
  const ping = metrics.latency * 2
  const pingColor = getQualityColor(ping, { good: 100, medium: 200 })

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-around' }}>
        <Box>
          <Typography variant="h6" gutterBottom sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            Network Performance
            <Box 
              sx={{ 
                display: 'flex',
                alignItems: 'center',
                backgroundColor: `${pingColor}15`,
                padding: '8px 12px',
                borderRadius: 2,
                border: `1px solid ${pingColor}40`
              }}
            >
              <Box sx={{ mr: 1.5, display: 'flex', alignItems: 'center' }}>
                <Timer sx={{ color: pingColor, mr: 1 }} />
                <Box>
                  <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', lineHeight: 1 }}>
                    PING
                  </Typography>
                  <Typography variant="h6" sx={{ color: pingColor, fontWeight: 'bold', lineHeight: 1 }}>
                    {ping.toFixed(0)}
                    <Typography component="span" variant="caption" sx={{ ml: 0.5, color: `${pingColor}90` }}>
                      ms
                    </Typography>
                  </Typography>
                </Box>
              </Box>
              <Chip 
                label={getQualityLabel(ping, { good: 100, medium: 200 })}
                size="small"
                sx={{ 
                  backgroundColor: `${pingColor}20`,
                  color: pingColor,
                  fontWeight: 600,
                  minWidth: 55
                }}
              />
            </Box>
          </Typography>
        </Box>

        <MetricCard
          title="Bandwidth"
          value={metrics.bandwidth}
          unit="Mbps"
          icon={<Speed />}
          progress={Math.min((metrics.bandwidth / 10) * 100, 100)}
          thresholds={{ good: 5, medium: 2 }}
        />
        
        <Divider sx={{ my: 2 }} />
        
        <MetricCard
          title="Latency"
          value={metrics.latency}
          unit="ms"
          icon={<NetworkCheck />}
          progress={Math.max(100 - (metrics.latency / 200) * 100, 0)}
          thresholds={{ good: 50, medium: 100 }}
          reverseQuality
        />
        
        <Divider sx={{ my: 2 }} />
        
        <MetricCard
          title="Packet Loss"
          value={metrics.packetLoss}
          unit="%"
          icon={<Warning />}
          progress={Math.max(100 - metrics.packetLoss * 10, 0)}
          thresholds={{ good: 1, medium: 5 }}
          reverseQuality
        />
      </CardContent>
    </Card>
  )
} 