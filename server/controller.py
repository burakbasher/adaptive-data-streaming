"""
Controller Module for Adaptive Streaming System
Determines optimal streaming quality based on network metrics
"""

import time
import logging
from typing import Dict, Literal, Tuple

# Import configuration
from config import QUALITY_THRESHOLDS, QUALITY_STABILITY_PERIOD, DEFAULT_QUALITY

# Configure logging
logger = logging.getLogger('controller')

# Quality level type - Updated for 3 quality levels
QualityLevel = Literal['low', 'medium', 'high']

class AdaptiveQualityController:
    """
    Controller class that determines optimal streaming quality
    based on current network conditions
    """
    
    def __init__(self, initial_quality: QualityLevel = DEFAULT_QUALITY):
        """
        Initialize the stream controller
        
        Args:
            initial_quality: Starting quality level
        """
        self.current_quality = initial_quality
        self.last_change_time = time.time()
        self.quality_stability_period = QUALITY_STABILITY_PERIOD
        
        # Keep track of quality history
        self.quality_history = [initial_quality]
        
        logger.info(f"AdaptiveQualityController initialized with {initial_quality} quality")

    def determine_quality(self, metrics: Dict[str, float]) -> QualityLevel:
        """
        Determine the optimal quality level based on current network metrics
        
        Args:
            metrics: Dictionary containing bandwidth (Mbps), latency (ms), and packet_loss (%)
            
        Returns:
            Appropriate quality level (low, medium, high)
        """
        bandwidth = metrics.get('bandwidth', 0)
        latency = metrics.get('latency', 500)
        packet_loss = metrics.get('packet_loss', 15)
        
        # Log incoming metrics
        logger.info(f"Current metrics - Bandwidth: {bandwidth} Mbps, Latency: {latency} ms, Packet Loss: {packet_loss}%")
        
        # Determine optimal quality based on metrics
        high_threshold_met = (
            bandwidth >= QUALITY_THRESHOLDS['high']['min_bandwidth'] and 
            latency <= QUALITY_THRESHOLDS['high']['max_latency'] and 
            packet_loss <= QUALITY_THRESHOLDS['high']['max_packet_loss']
        )
        
        medium_threshold_met = (
            bandwidth >= QUALITY_THRESHOLDS['medium']['min_bandwidth'] and 
            latency <= QUALITY_THRESHOLDS['medium']['max_latency'] and 
            packet_loss <= QUALITY_THRESHOLDS['medium']['max_packet_loss']
        )
        
        if high_threshold_met:
            optimal_quality = 'high'
            logger.info(f"High quality thresholds met: bandwidth >= {QUALITY_THRESHOLDS['high']['min_bandwidth']}, " 
                        f"latency <= {QUALITY_THRESHOLDS['high']['max_latency']}, "
                        f"packet_loss <= {QUALITY_THRESHOLDS['high']['max_packet_loss']}")
        elif medium_threshold_met:
            optimal_quality = 'medium'
            logger.info(f"Medium quality thresholds met: bandwidth >= {QUALITY_THRESHOLDS['medium']['min_bandwidth']}, " 
                        f"latency <= {QUALITY_THRESHOLDS['medium']['max_latency']}, "
                        f"packet_loss <= {QUALITY_THRESHOLDS['medium']['max_packet_loss']}")
        else:
            optimal_quality = 'low'
            logger.info("Using low quality: medium thresholds not met")
        
        # Check if we should change quality (avoid rapid fluctuations)
        current_time = time.time()
        if optimal_quality != self.current_quality:
            if (current_time - self.last_change_time) >= self.quality_stability_period:
                logger.info(f"Quality change: {self.current_quality} -> {optimal_quality}")
                
                # Update current quality and timestamp
                self.current_quality = optimal_quality
                self.last_change_time = current_time
                
                # Add to quality history
                self.quality_history.append(optimal_quality)
            else:
                logger.info(f"Quality change suppressed due to stability period: {current_time - self.last_change_time:.2f}s < {self.quality_stability_period}s")
        
        # Trim history if needed
        if len(self.quality_history) > 100:
            self.quality_history = self.quality_history[-100:]
        
        return self.current_quality
    
    def get_quality_settings(self) -> Dict:
        """
        Get the current quality level settings
        
        Returns:
            Dictionary containing resolution, bitrate and other settings
        """
        return QUALITY_THRESHOLDS[self.current_quality]
    
    def get_resolution(self) -> Tuple[int, int]:
        """
        Get the current resolution
        
        Returns:
            Tuple containing width and height
        """
        return QUALITY_THRESHOLDS[self.current_quality]['resolution']
    
    def get_bitrate(self) -> int:
        """
        Get the current bitrate in Kbps
        
        Returns:
            Bitrate value
        """
        return QUALITY_THRESHOLDS[self.current_quality]['bitrate']
    
    def get_quality_history(self, limit: int = 10) -> list:
        """
        Get recent quality history
        
        Args:
            limit: Maximum number of history items to return
        
        Returns:
            List of recent quality levels
        """
        return self.quality_history[-limit:]

    def set_quality(self, quality: QualityLevel) -> None:
        """
        Manually set quality level
        
        Args:
            quality: The quality level to set
        """
        if quality not in QUALITY_THRESHOLDS:
            logger.warning(f"Invalid quality: {quality}")
            return
            
        if quality != self.current_quality:
            logger.info(f"Manually setting quality: {self.current_quality} -> {quality}")
            self.current_quality = quality
            self.quality_history.append(quality)
            self.last_change_time = time.time()

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create controller
    controller = AdaptiveQualityController()
    
    # Example metrics
    metrics_samples = [
        {'bandwidth': 6.0, 'latency': 50, 'packet_loss': 1.0},  # High quality
        {'bandwidth': 3.0, 'latency': 100, 'packet_loss': 3.0},  # Medium quality
        {'bandwidth': 1.0, 'latency': 200, 'packet_loss': 8.0},  # Low quality
        {'bandwidth': 2.5, 'latency': 120, 'packet_loss': 4.0},  # Medium quality
        {'bandwidth': 7.0, 'latency': 30, 'packet_loss': 0.5},   # High quality
    ]
    
    # Simulate changing network conditions
    for i, metrics in enumerate(metrics_samples):
        quality = controller.determine_quality(metrics)
        resolution = controller.get_resolution()
        bitrate = controller.get_bitrate()
        
        print(f"Sample {i+1}:")
        print(f"  Metrics: {metrics}")
        print(f"  Quality: {quality}")
        print(f"  Resolution: {resolution}")
        print(f"  Bitrate: {bitrate} Kbps")
        print()
        
        # Simulate time passing
        time.sleep(2)