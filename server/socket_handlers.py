"""server/socket_handlers.py"""

import logging

logger = logging.getLogger('socket_handlers')

from wifi_monitor import get_network_monitor

def register_handlers(socketio):
    """
    Register all Socket.IO event handlers
    
    Args:
        socketio: The Socket.IO instance to register handlers with
    """
    @socketio.on('network_metrics')
    def handle_network_metrics(data):
        """
        Handle network metrics sent by the client.
        """
        try:
            latency = float(data.get('latency', 999.0))
            packet_loss = float(data.get('packet_loss', 100.0))
            bandwidth = float(data.get('bandwidth', 0.0))
            
            logger.info(f"Received metrics from client - Latency: {latency:.2f} ms, Packet Loss: {packet_loss:.2f}%, Bandwidth: {bandwidth:.2f} Mbps")
            
            monitor = get_network_monitor()
            monitor._update_metrics(bandwidth, latency, packet_loss)
            
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Error processing network metrics: {e}")
            return {"status": "error", "message": str(e)}