from typing import Dict, List
import numpy as np

class StreamController:
    def __init__(self):
        self.quality_levels = {
            'low': {'bitrate': 500, 'resolution': (640, 360)},    # 500 Kbps
            'medium': {'bitrate': 1500, 'resolution': (1280, 720)}, # 1.5 Mbps
            'high': {'bitrate': 3000, 'resolution': (1920, 1080)}  # 3 Mbps
        }
        
    def determine_quality_level(self, network_metrics: Dict[str, float]) -> str:
        """
        Determine the appropriate quality level based on network metrics
        Returns: 'low', 'medium', or 'high'
        """
        bandwidth = network_metrics['bandwidth']
        latency = network_metrics['latency']
        packet_loss = network_metrics['packet_loss']
        
        # Simple decision logic based on bandwidth
        if bandwidth < 1.0 or latency > 100 or packet_loss > 5:
            return 'low'
        elif bandwidth < 2.5:
            return 'medium'
        else:
            return 'high'
    
    def get_quality_settings(self, level: str) -> Dict:
        """
        Get the quality settings for a given level
        """
        return self.quality_levels.get(level, self.quality_levels['low']) 