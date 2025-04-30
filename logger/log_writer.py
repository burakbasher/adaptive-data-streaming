import json
import os
from datetime import datetime
from typing import Dict

class LogWriter:
    def __init__(self, log_dir: str, log_file: str):
        self.log_dir = log_dir
        self.log_file = log_file
        self._ensure_log_directory()
        
    def _ensure_log_directory(self):
        """Create log directory if it doesn't exist"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
    def log_metrics(self, metrics: Dict):
        """
        Log network metrics and stream quality
        """
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'metrics': metrics
        }
        
        log_path = os.path.join(self.log_dir, self.log_file)
        with open(log_path, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
            
    def get_recent_metrics(self, limit: int = 100) -> list:
        """
        Get recent metrics from log file
        """
        log_path = os.path.join(self.log_dir, self.log_file)
        if not os.path.exists(log_path):
            return []
            
        metrics = []
        with open(log_path, 'r') as f:
            for line in f:
                try:
                    metrics.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
                    
        return metrics[-limit:] 