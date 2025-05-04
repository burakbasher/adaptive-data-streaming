"""
Main entry point for Adaptive Streaming System
"""

import os
import sys
import time
import logging
import argparse
import threading

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

# Import server modules
from server.app import app
from server.wifi_monitor import NetworkMonitor
from server.controller import StreamController
from server.stream_engine import StreamEngine
from logger.log_writer import MetricsLogger
from server.config import SERVER_HOST, SERVER_PORT, DEBUG_MODE, LOGS_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('run_server')

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Adaptive Streaming Server')
    
    parser.add_argument('--host', type=str, default=SERVER_HOST,
                        help=f'Host to run the server on (default: {SERVER_HOST})')
    parser.add_argument('--port', type=int, default=SERVER_PORT,
                        help=f'Port to run the server on (default: {SERVER_PORT})')
    parser.add_argument('--debug', action='store_true', default=DEBUG_MODE,
                        help='Enable debug mode')
    parser.add_argument('--log-dir', type=str, default=LOGS_DIR,
                        help=f'Directory for log files (default: {LOGS_DIR})')
    
    return parser.parse_args()

def setup_components():
    """Initialize and start all system components"""
    # Create and initialize components
    network_monitor = NetworkMonitor()
    stream_controller = StreamController()
    stream_engine = StreamEngine()
    metrics_logger = MetricsLogger(LOGS_DIR)
    
    # Start network monitoring
    network_monitor.start()
    
    # Return initialized components
    return {
        'network_monitor': network_monitor,
        'stream_controller': stream_controller,
        'stream_engine': stream_engine,
        'metrics_logger': metrics_logger
    }

def run_metrics_update_loop(components):
    """
    Run a loop to continuously update metrics and adjust quality
    """
    network_monitor = components['network_monitor']
    stream_controller = components['stream_controller']
    stream_engine = components['stream_engine']
    metrics_logger = components['metrics_logger']
    
    while True:
        try:
            # Get current network metrics
            metrics = network_monitor.get_metrics()
            
            # Determine optimal quality
            quality = stream_controller.determine_quality(metrics)
            
            # Update stream quality
            stream_engine.set_quality(quality)
            
            # Log metrics
            metrics_logger.log_metrics(metrics, quality)
            
            # Log current status
            logger.info(f"Metrics - Bandwidth: {metrics['bandwidth']} Mbps, " +
                        f"Latency: {metrics['latency']} ms, " +
                        f"Packet Loss: {metrics['packet_loss']}%")
            logger.info(f"Streaming Quality: {quality}")
            
            # Wait before next update
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error in metrics update loop: {e}")
            time.sleep(2)

def main():
    """Main entry point"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Log startup info
    logger.info("=" * 50)
    logger.info("Adaptive Streaming System")
    logger.info("=" * 50)
    logger.info(f"Server host: {args.host}")
    logger.info(f"Server port: {args.port}")
    logger.info(f"Debug mode: {args.debug}")
    logger.info(f"Log directory: {args.log_dir}")
    
    # Setup components
    components = setup_components()
    
    # Start metrics update loop in a separate thread
    metrics_thread = threading.Thread(
        target=run_metrics_update_loop,
        args=(components,)
    )
    metrics_thread.daemon = True
    metrics_thread.start()
    
    # Start the Flask server
    try:
        logger.info("Starting web server...")
        app.run(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Error starting server: {e}")
    finally:
        # Shutdown components
        logger.info("Shutting down components...")
        components['network_monitor'].stop()
        components['stream_engine'].stop()
        logger.info("Shutdown complete")

if __name__ == "__main__":
    main()