"""
WiFi Network Monitor
Measures network quality metrics for adaptive streaming
"""

import time
import logging
import platform
import subprocess
import socket
import threading
import random
import statistics
from typing import Dict, List, Optional

# Import configuration
from config import QUALITY_THRESHOLDS

# Configure logger
logger = logging.getLogger('wifi_monitor')

class NetworkMonitor:
    """
    Monitors network quality metrics including bandwidth, latency, and packet loss
    """
    
    def __init__(self, test_server: str = '8.8.8.8', update_interval: float = 1.0):
        """
        Initialize the network monitor
        
        Args:
            test_server: Server to use for ping tests
            update_interval: Time between measurements in seconds
        """
        self.test_server = test_server
        self.update_interval = update_interval
        self.running = False
        self.monitor_thread = None
        
        # Latest metrics
        self._latest_metrics = {
            'bandwidth': 0.0,  # Mbps
            'latency': 0.0,    # ms
            'packet_loss': 0.0 # %
        }
        
        # Store historical measurements
        self._bandwidth_history: List[float] = []
        self._latency_history: List[float] = []
        self._packet_loss_history: List[float] = []
        
        # History size
        self._history_size = 10
        
        logger.info(f"NetworkMonitor initialized (test server: {test_server})")
    
    def start(self) -> None:
        """Start the network monitoring thread"""
        if self.running:
            logger.warning("Monitor is already running")
            return
            
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("Network monitoring started")
    
    def stop(self) -> None:
        """Stop the network monitoring thread"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
            
        logger.info("Network monitoring stopped")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop"""
        while self.running:
            try:
                # Measure network metrics
                bandwidth = self._measure_bandwidth()
                latency, packet_loss = self._measure_latency_and_packet_loss()
                
                # Update metrics
                self._update_metrics(bandwidth, latency, packet_loss)
                
                # Wait for next update
                time.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(self.update_interval)
    
    def _measure_bandwidth(self) -> float:
        """
        Measure network bandwidth
        
        In a real implementation, this would use speedtest or similar tools.
        This demo implementation simulates bandwidth measurements.
        
        Returns:
            Measured bandwidth in Mbps
        """
        # Simulated bandwidth measurement
        # In real implementation, use tools like speedtest-cli, iperf, or custom implementation
        
        # Base bandwidth (simulate home internet connection)
        base_bandwidth = 10.0  # 10 Mbps
        
        # Add some random variation
        variation = random.uniform(-2.0, 2.0)
        
        # Occasional congestion (10% chance)
        if random.random() < 0.1:
            congestion_factor = random.uniform(0.3, 0.8)
            measured_bandwidth = max(0.5, (base_bandwidth + variation) * congestion_factor)
        else:
            measured_bandwidth = max(0.5, base_bandwidth + variation)
        
        logger.debug(f"Measured bandwidth: {measured_bandwidth:.2f} Mbps")
        return measured_bandwidth
    
    def _measure_latency_and_packet_loss(self) -> tuple:
        """
        Measure network latency and packet loss using ping
        
        Returns:
            Tuple of (latency_ms, packet_loss_percent)
        """
        # In a real implementation, use actual ping or custom implementation
        # This demo implementation simulates measurements
        
        # Base latency
        base_latency = 50.0  # 50 ms
        
        # Add random variation
        latency_variation = random.uniform(-20.0, 30.0)
        latency = max(5.0, base_latency + latency_variation)
        
        # Packet loss (normally low, occasionally higher)
        if random.random() < 0.1:  # 10% chance of packet loss event
            packet_loss = random.uniform(1.0, 15.0)
        else:
            packet_loss = random.uniform(0.0, 2.0)
        
        logger.debug(f"Measured latency: {latency:.2f} ms, packet loss: {packet_loss:.2f}%")
        return latency, packet_loss
    
    def _update_metrics(self, bandwidth: float, latency: float, packet_loss: float) -> None:
        """
        Update the latest metrics with new measurements
        
        Args:
            bandwidth: Measured bandwidth in Mbps
            latency: Measured latency in ms
            packet_loss: Measured packet loss in %
        """
        # Update histories
        self._bandwidth_history.append(bandwidth)
        self._latency_history.append(latency)
        self._packet_loss_history.append(packet_loss)
        
        # Trim histories if too long
        if len(self._bandwidth_history) > self._history_size:
            self._bandwidth_history = self._bandwidth_history[-self._history_size:]
        if len(self._latency_history) > self._history_size:
            self._latency_history = self._latency_history[-self._history_size:]
        if len(self._packet_loss_history) > self._history_size:
            self._packet_loss_history = self._packet_loss_history[-self._history_size:]
        
        # Calculate smoothed metrics (moving average)
        smoothed_bandwidth = statistics.mean(self._bandwidth_history)
        smoothed_latency = statistics.mean(self._latency_history)
        smoothed_packet_loss = statistics.mean(self._packet_loss_history)
        
        # Update latest metrics
        self._latest_metrics = {
            'bandwidth': round(smoothed_bandwidth, 2),
            'latency': round(smoothed_latency, 2),
            'packet_loss': round(smoothed_packet_loss, 2)
        }
    
    def get_metrics(self) -> Dict[str, float]:
        """
        Get the latest network metrics
        
        Returns:
            Dictionary containing bandwidth, latency, and packet loss
        """
        return self._latest_metrics.copy()
    
    def get_suggested_quality(self) -> str:
        """
        Get the suggested quality level based on current network metrics
        
        Returns:
            Suggested quality level ('low', 'medium', or 'high')
        """
        bandwidth = self._latest_metrics['bandwidth']
        latency = self._latest_metrics['latency']
        packet_loss = self._latest_metrics['packet_loss']
        
        if (bandwidth >= QUALITY_THRESHOLDS['high']['min_bandwidth'] and 
            latency <= QUALITY_THRESHOLDS['high']['max_latency'] and 
            packet_loss <= QUALITY_THRESHOLDS['high']['max_packet_loss']):
            return 'high'
        elif (bandwidth >= QUALITY_THRESHOLDS['medium']['min_bandwidth'] and 
              latency <= QUALITY_THRESHOLDS['medium']['max_latency'] and 
              packet_loss <= QUALITY_THRESHOLDS['medium']['max_packet_loss']):
            return 'medium'
        else:
            return 'low'

# Utility function to run a real ping test
def ping_test(host: str = '8.8.8.8', count: int = 5) -> tuple:
    """
    Run a ping test to measure latency and packet loss
    
    Args:
        host: Host to ping
        count: Number of pings to send
    
    Returns:
        Tuple of (avg_latency, packet_loss_percent)
    """
    try:
        # Determine operating system
        os_name = platform.system().lower()
        
        if os_name == 'windows':
            # Windows ping command
            output = subprocess.check_output(
                ['ping', '-n', str(count), host],
                universal_newlines=True
            )
            
            # Parse Windows ping output
            lines = output.split('\n')
            loss_line = [l for l in lines if 'Lost' in l][0]
            packet_loss = int(loss_line.split('(')[1].split('%')[0])
            
            # Extract average latency if available
            time_line = [l for l in lines if 'Average' in l]
            if time_line:
                avg_latency = float(time_line[0].split('=')[1].split('ms')[0].strip())
            else:
                avg_latency = 999.0
                
        else:
            # Linux/MacOS ping command
            output = subprocess.check_output(
                ['ping', '-c', str(count), host],
                universal_newlines=True
            )
            
            # Parse Linux/MacOS ping output
            lines = output.split('\n')
            
            # Find packet loss line
            loss_line = [l for l in lines if 'packet loss' in l][0]
            packet_loss = float(loss_line.split('%')[0].split(' ')[-1])
            
            # Find average latency line
            stats_line = [l for l in lines if 'min/avg/max' in l]
            if stats_line:
                avg_latency = float(stats_line[0].split('/')[4].split('/')[0])
            else:
                avg_latency = 999.0
        
        return avg_latency, packet_loss
        
    except Exception as e:
        logger.error(f"Ping test failed: {e}")
        return 999.0, 100.0  # High values indicate failure

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start monitor
    monitor = NetworkMonitor()
    monitor.start()
    
    try:
        # Print metrics periodically
        for _ in range(20):
            metrics = monitor.get_metrics()
            suggested_quality = monitor.get_suggested_quality()
            
            print(f"Bandwidth: {metrics['bandwidth']} Mbps")
            print(f"Latency: {metrics['latency']} ms")
            print(f"Packet Loss: {metrics['packet_loss']}%")
            print(f"Suggested Quality: {suggested_quality}")
            print("-" * 50)
            
            time.sleep(0.01)
    finally:
        # Stop the monitor
        monitor.stop()