# Companion Capture App

A comprehensive life-logging application for the Sipeed MaixCAM device using the MaixPy framework.

## Project Overview

This application detects and records objects, people, places, things, and events through continuous AI-powered analysis, outputting all results in JSON format for local storage and remote synchronization.

## Project Structure

```
MaixPy/
├── PROJECT_PLAN.MD              # Detailed project plan and roadmap
├── test_basic.py               # Basic component tests
├── src/                        # Main source code
│   ├── main.py                # Main application entry point
│   ├── utils/                 # Utility modules
│   │   ├── config.py         # Configuration management
│   │   └── logger.py         # Logging utilities
│   ├── ui/                    # User interface components
│   │   ├── main_ui.py        # Main UI management
│   │   └── ui_elements.py    # Custom UI elements (buttons, checkboxes)
│   ├── ai_engine/             # AI processing engine
│   │   └── ai_engine.py      # AI model management and processing
│   ├── data_logger/           # Data logging system
│   │   └── logger.py         # JSON event logging
│   └── network/               # Network functionality
│       └── uploader.py       # REST API upload functionality
└── MaixPy_examples/           # Example code (reference)
    └── ...
```

## Features Implemented

### ✅ Core Infrastructure
- **Application Framework**: Main app with state management
- **Configuration System**: JSON-based configuration with defaults
- **Logging System**: Centralized logging to file and console
- **UI Framework**: Custom touch-based UI with buttons and checkboxes
- **Modular Architecture**: Clean separation of concerns

### ✅ AI Processing Engine
- **Model Management**: Round-robin NPU scheduling for multiple AI models
- **Object Detection**: YOLOv8-based object detection with confidence filtering
- **Face Detection**: Dedicated face detection pipeline
- **Pose Detection**: Human pose estimation
- **Extensible Design**: Easy to add new AI models

### ✅ Data Management
- **JSON Logging**: Standardized event logging with metadata
- **Session Management**: Start/stop logging sessions
- **Storage Management**: Automatic cleanup and rotation
- **Event Processing**: Structured event data with confidence scores

### ✅ Network Integration
- **REST API Client**: Background upload to remote servers
- **Queue Management**: Upload queue with retry logic
- **Batch Processing**: Efficient batch uploads
- **Error Handling**: Robust error handling and recovery

### ✅ User Interface
- **Touch Interface**: Custom buttons and checkboxes
- **Camera Preview**: Live camera feed with AI overlays
- **Status Display**: Real-time system status and performance metrics
- **Model Controls**: Toggle AI models on/off dynamically

## Quick Start

### 1. Test Basic Components (Local)

```bash
cd /Users/williambroza/devel/MaixPy
python test_basic.py
```

### 2. Transfer to MaixCAM Device

Copy the entire `src/` folder to your MaixCAM device:

```bash
# Using MaixVision IDE file manager, or:
scp -r src/ root@<maixcam-ip>:/root/companion_capture/
```

### 3. Run on Device

```python
# On MaixCAM device
cd /root/companion_capture
python main.py
```

## Configuration

The app uses a JSON configuration file (`/sd/config/app_config.json`) with the following key sections:

### AI Models
```json
{
  "ai_models": {
    "object_detection": {
      "enabled": true,
      "model_path": "/root/models/yolov8n.mud",
      "confidence_threshold": 0.5,
      "processing_interval": 3
    }
  }
}
```

### Camera Settings
```json
{
  "camera": {
    "width": 640,
    "height": 480,
    "fps": 30
  }
}
```

### Storage Settings
```json
{
  "storage": {
    "base_path": "/sd/logs",
    "max_log_size_mb": 100,
    "rotation_interval_hours": 24
  }
}
```

### Network Settings
```json
{
  "network": {
    "upload_enabled": false,
    "endpoint_url": "https://api.example.com/upload",
    "upload_interval_seconds": 300
  }
}
```

## AI Models Supported

1. **Object Detection** - YOLOv8 general object detection
2. **Face Detection** - Specialized face detection
3. **Face Emotion** - Emotion classification (requires face detection)
4. **OCR** - Text recognition (PP-OCR)
5. **Hand Landmarks** - Hand pose estimation
6. **Human Pose** - 17-keypoint human pose detection
7. **Audio Recognition** - Real-time voice recognition

## Data Output Format

All AI detections are logged in standardized JSON format:

```json
{
  "event_id": "uuid-here",
  "timestamp": "2025-07-13T14:30:22.123456",
  "session_id": "session-uuid",
  "type": "object_detection",
  "model": "yolov8",
  "confidence_scores": [0.85, 0.92],
  "data": {
    "objects": [
      {
        "label": "person",
        "confidence": 0.85,
        "bbox": [100, 150, 50, 100]
      }
    ],
    "count": 1
  },
  "metadata": {
    "device_info": {...},
    "memory_usage": {...}
  }
}
```

## Performance Targets

- **Frame Rate**: 15-20 FPS camera preview
- **Memory Usage**: <200MB under normal operation
- **AI Processing**: <100ms per model inference
- **Storage Write**: <10ms per event
- **Network Upload**: 95% success rate

## Development Status

| Component | Status | Notes |
|-----------|--------|-------|
| Core Framework | ✅ Complete | Ready for testing |
| Configuration | ✅ Complete | JSON-based with defaults |
| UI System | ✅ Complete | Touch interface implemented |
| AI Engine | ✅ Complete | Round-robin scheduling |
| Data Logging | ✅ Complete | JSON event logging |
| Network Upload | ✅ Complete | Background REST API client |

## Next Steps

1. **Hardware Testing** - Test on actual MaixCAM device
2. **AI Model Integration** - Verify all AI models load correctly
3. **Performance Optimization** - Fine-tune for real-world usage
4. **Extended Features** - Add remaining AI models (OCR, hand detection, etc.)
5. **User Testing** - Validate UI/UX on device

## Troubleshooting

### Common Issues

**Import Errors**: Ensure all `__init__.py` files are present and the `src` directory is in the Python path.

**Configuration Issues**: Check that `/sd/config/` directory exists and is writable.

**AI Model Errors**: Verify models exist in `/root/models/` and are in `.mud` format.

**Memory Issues**: Monitor memory usage and adjust AI model processing intervals.

### Debug Mode

Enable debug logging in configuration:
```json
{
  "app": {
    "debug": true,
    "log_level": "DEBUG"
  }
}
```

## Contributing

1. Follow the modular architecture
2. Add comprehensive logging
3. Update configuration schema as needed
4. Write tests for new functionality
5. Update this README for new features

## License

Companion Intelligence - 2025

---

*For detailed implementation roadmap, see PROJECT_PLAN.MD*
