"""
Logger Module for Adaptive Streaming System
Records network metrics and quality change events to CSV files
"""

import os
import csv
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Literal

QualityLevel = Literal['low', 'medium', 'high']

logger = logging.getLogger('log_writer')

class MetricsLogger:
    """
    Class for logging network metrics and quality changes to CSV files
    """
    
    def __init__(self, log_dir: str = 'logs'):
        """
        Initialize the metrics logger
        
        Args:
            log_dir: Directory to store log files
        """
        self.log_dir = log_dir
        self._ensure_log_dir()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.metrics_filename = os.path.join(self.log_dir, f"network_metrics_{timestamp}.csv")
        self.quality_filename = os.path.join(self.log_dir, f"quality_changes_{timestamp}.csv")
        
        self._init_metrics_csv()
        self._init_quality_csv()
        
        logger.info(f"MetricsLogger initialized. Metrics file: {self.metrics_filename}")
        logger.info(f"Quality changes file: {self.quality_filename}")
        
        self.current_quality = None
        
    def _ensure_log_dir(self) -> None:
        """Creates log directory if it doesn't exist"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            logger.info(f"Created log directory: {self.log_dir}")
    
    def _init_metrics_csv(self) -> None:
        """Initializes the network metrics CSV file with headers"""
        with open(self.metrics_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'timestamp', 
                'bandwidth_mbps', 
                'latency_ms', 
                'packet_loss_percent',
                'current_quality'
            ])
    
    def _init_quality_csv(self) -> None:
        """Initializes the quality changes CSV file with headers"""
        with open(self.quality_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'timestamp', 
                'previous_quality', 
                'new_quality',
                'bandwidth_mbps', 
                'latency_ms', 
                'packet_loss_percent'
            ])
            
    def log_metrics(self, metrics: Dict[str, float], quality: QualityLevel) -> None:
        """
        Log current network metrics to CSV
        
        Args:
            metrics: Dictionary with bandwidth, latency, packet_loss
            quality: Current streaming quality level
        """
        timestamp = datetime.now().isoformat()
        
        with open(self.metrics_filename, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                timestamp,
                metrics.get('bandwidth', 0),
                metrics.get('latency', 0),
                metrics.get('packet_loss', 0),
                quality
            ])
        
        if self.current_quality is not None and quality != self.current_quality:
            self.log_quality_change(self.current_quality, quality, metrics)
        
        self.current_quality = quality
    
    def log_quality_change(self, previous_quality: QualityLevel, 
                          new_quality: QualityLevel, 
                          metrics: Dict[str, float]) -> None:
        """
        Log quality change events with corresponding network metrics
        
        Args:
            previous_quality: Quality level before change
            new_quality: New quality level
            metrics: Network metrics at time of change
        """
        timestamp = datetime.now().isoformat()
        
        with open(self.quality_filename, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                timestamp,
                previous_quality,
                new_quality,
                metrics.get('bandwidth', 0),
                metrics.get('latency', 0),
                metrics.get('packet_loss', 0)
            ])
        
        logger.info(f"Quality changed: {previous_quality} -> {new_quality}")
    
    def get_metrics_history(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Retrieve recent metrics history
        
        Args:
            limit: Optional limit on number of records to return
            
        Returns:
            List of dictionaries containing metrics
        """
        metrics_history = []
        
        try:
            with open(self.metrics_filename, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    metrics_history.append(dict(row))
                    
                    if limit and len(metrics_history) >= limit:
                        break
        except Exception as e:
            logger.error(f"Error reading metrics history: {e}")
            
        return metrics_history
    
    def get_quality_changes(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Retrieve quality change history
        
        Args:
            limit: Optional limit on number of records to return
            
        Returns:
            List of dictionaries containing quality change events
        """
        quality_changes = []
        
        try:
            with open(self.quality_filename, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    quality_changes.append(dict(row))
                    
                    # Apply limit if specified
                    if limit and len(quality_changes) >= limit:
                        break
        except Exception as e:
            logger.error(f"Error reading quality change history: {e}")
            
        return quality_changes
    
    def generate_summary_report(self, output_file: Optional[str] = None) -> Dict:
        """
        Generate a summary report of metrics and quality changes
        
        Args:
            output_file: Optional file to write the summary to
            
        Returns:
            Dictionary with summary statistics
        """
        metrics_history = self.get_metrics_history()
        quality_changes = self.get_quality_changes()
        
        bandwidths = [float(m['bandwidth_mbps']) for m in metrics_history if 'bandwidth_mbps' in m]
        latencies = [float(m['latency_ms']) for m in metrics_history if 'latency_ms' in m]
        packet_losses = [float(m['packet_loss_percent']) for m in metrics_history if 'packet_loss_percent' in m]
        
        quality_distribution = {
            'low': 0,
            'medium': 0,
            'high': 0
        }
        
        for m in metrics_history:
            if 'current_quality' in m and m['current_quality'] in quality_distribution:
                quality_distribution[m['current_quality']] += 1
        
        summary = {
            'metrics_count': len(metrics_history),
            'quality_changes_count': len(quality_changes),
            'avg_bandwidth': sum(bandwidths) / max(1, len(bandwidths)),
            'max_bandwidth': max(bandwidths) if bandwidths else 0,
            'min_bandwidth': min(bandwidths) if bandwidths else 0,
            'avg_latency': sum(latencies) / max(1, len(latencies)),
            'max_latency': max(latencies) if latencies else 0,
            'min_latency': min(latencies) if latencies else 0, 
            'avg_packet_loss': sum(packet_losses) / max(1, len(packet_losses)),
            'max_packet_loss': max(packet_losses) if packet_losses else 0,
            'quality_distribution': quality_distribution
        }
        
        if output_file:
            try:
                with open(output_file, 'w', newline='') as outfile:
                    writer = csv.writer(outfile)
                    writer.writerow(['Metric', 'Value'])
                    
                    for key, value in summary.items():
                        if key == 'quality_distribution':
                            for quality, count in value.items():
                                writer.writerow([f'Quality {quality}', count])
                        else:
                            writer.writerow([key, value])
                logger.info(f"Summary report written to {output_file}")
            except Exception as e:
                logger.error(f"Error writing summary report: {e}")
        
        return summary

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    metrics_logger = MetricsLogger()
    
    for i in range(10):
        metrics = {
            'bandwidth': 5.0 + (i * 0.5),
            'latency': 100.0 - (i * 5),
            'packet_loss': max(0, 5.0 - (i * 0.5))
        }
        
        if metrics['bandwidth'] > 8.0:
            quality = 'high'
        elif metrics['bandwidth'] > 4.0:
            quality = 'medium'
        else:
            quality = 'low'
            
        metrics_logger.log_metrics(metrics, quality)
        
        # Wait a bit
        time.sleep(0.5)
    
    summary = metrics_logger.generate_summary_report('logs/summary.csv')
    
    print("Summary Report:")
    for key, value in summary.items():
        print(f"{key}: {value}")