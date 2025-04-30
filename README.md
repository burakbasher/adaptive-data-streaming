# Adaptive Data Streaming Based on Wi-Fi Quality

This project implements an adaptive video streaming system that adjusts video quality based on real-time Wi-Fi network conditions. The system monitors network metrics such as bandwidth, latency, and packet loss to dynamically adjust the streaming quality.

## Features

- Real-time network quality monitoring
- Adaptive video quality adjustment
- Live metrics display
- Logging of network metrics and quality changes

## Project Structure

```
adaptive-streaming-wifi/
│
├── server/                          # Server-side code
│   ├── app.py                       # Flask server (video stream endpoint)
│   ├── wifi_monitor.py              # Network quality measurement
│   ├── controller.py                # Stream quality controller
│   ├── stream_engine.py             # Video stream generator
│   └── config.py                    # General settings
│
├── client/                          # Simple HTML client
│   ├── index.html                   # Video stream interface
│   └── style.css                    # Styling
│
├── data/
│   └── sample_video.mp4            # Sample video (to be streamed)
│
├── logger/
│   └── log_writer.py               # Metrics & quality logging
│
├── requirements.txt                 # Python dependencies
├── run_server.py                    # Main application runner
└── README.md                        # Project documentation
```

## Setup Instructions

1. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Place a sample video file in the `data` directory named `sample_video.mp4`

4. Run the server:
   ```bash
   python run_server.py
   ```

5. Open a web browser and navigate to `http://localhost:5000`

## Network Quality Levels

The system supports three quality levels:

- Low: 640x360 resolution, 500 Kbps
- Medium: 1280x720 resolution, 1.5 Mbps
- High: 1920x1080 resolution, 3 Mbps

Quality is automatically adjusted based on:
- Available bandwidth
- Network latency
- Packet loss percentage

## Dependencies

- Flask: Web server framework
- OpenCV: Video processing
- psutil: System and network monitoring
- numpy: Numerical operations

## License

MIT License 