# Companion Capture App Development Plan

## Sipeed MaixCAM Device Using MaixPy

### Project Overview

Develop a comprehensive life-logging application for the Sipeed MaixCAM device using the MaixPy framework. The application will detect and record objects, people, places, things, and events through continuous AI-powered analysis.

### Core Objectives

- **Target Recording**: People, places, things, and events
- **Output Format**: All results in JSON format only
- **Storage**: Local JSON storage with REST API sync via WiFi
- **Use Case**: Life logging for house and backyard monitoring

### Reference Documentation

- [MaixPy Basic App Development](https://wiki.sipeed.com/maixpy/doc/en/basic/app.html)
- [MaixPy Documentation](https://wiki.sipeed.com/maixpy/doc/en/index.html)

### AI Features to Implement

#### Computer Vision (AI Video)

- Object Classification
- Face Recognition
- Face Emotion Detection
- Object Tracking and Counting
- OCR (Optical Character Recognition)
- Hand Landmarks Detection
- Human Pose Classification
- Hand Gesture Classification

#### Audio Processing (AI Audio)

- Audio Recording
- Audio Playback
- Real-time Voice Recognition

#### Media Capabilities

- Video Recording
- Video Playback

### Technical Requirements

- **Data Format**: JSON with timestamps, sensor details, and confidence scores
- **Storage Strategy**: Local storage with REST API synchronization
- **User Interface**: Preview display with start/stop controls and model toggle checkboxes
- **Connectivity**: WiFi-enabled for remote data upload

### Development Framework

All features will be implemented using the MaixPy framework and its comprehensive AI toolkit as documented in the official documentation.
 

# PROJECT PLAN STEPS:

## Detailed Implementation Roadmap

| Step | Task | Description | Status |
|------|------|-------------|--------|
| 1 | Initial Setup | Setup Sipeed MaxiCam hardware and install MaixPy firmware. Verify device functionality. | ✅ |
| 2 | Development Environment | Install and configure MaixPy IDE. Ensure serial and Wi-Fi connectivity. | ✅ |
| 3 | UI Design | Design simple user interface with preview, start, stop, log, and detection model toggle checkboxes. | ✅ |
| 4 | Camera Integration | Develop and test camera preview and video recording functionalities. | 🚧 |
| 5 | Audio Integration | Integrate audio recording and playback functionalities; verify real-time voice recognition. | ☐ |
| 6 | Object Classification | Implement object classification model; output JSON with timestamp, confidence scores, and sensor details. | ☐ |
| 7 | Face Recognition & Emotion | Implement facial recognition and emotion detection models; ensure accurate JSON outputs. | ☐ |
| 8 | Object Tracking & Counting | Implement object tracking and counting functionality; validate JSON accuracy. | ☐ |
| 9 | OCR Implementation | Develop OCR for text recognition; verify accuracy and JSON formatting. | ☐ |
| 10 | Hand & Gesture Recognition | Integrate hand landmarks and hand gesture classifier; test thoroughly for reliable JSON outputs. | ☐ |
| 11 | Human Pose Classifier | Integrate human pose detection and classification; ensure robust JSON logging. | ☐ |
| 12 | JSON Output Format | Standardize JSON format to include timestamps, sensor details, model type, detection confidence, and detected entity details. | ☐ |
| 13 | Local Storage Management | Set up reliable local storage system to log JSON results continuously with clear storage management policies. | ☐ |
| 14 | REST API Integration | Develop REST client to post JSON logs securely and reliably to external server via Wi-Fi. | ☐ |
| 15 | Detection Model Toggles | Implement toggle functionality in UI to enable/disable each detection model dynamically. | ☐ |
| 16 | Testing & Debugging | Conduct unit tests and integrated testing of all features and components; fix bugs and optimize performance. | ☐ |
| 17 | Performance Optimization | Optimize AI model performance, Wi-Fi data transfer efficiency, and battery usage for continuous logging. | ☐ |
| 18 | Documentation & Deployment | Write clear documentation for usage, troubleshooting, and further development; prepare for final deployment. | ☐ |
| 19 | Final Deployment & Monitoring | Deploy final Companion Capture App to the MaxiCam, monitor initial operation, and make necessary adjustments. | ☐ |

---
 
### Step 3: UI Design
**Sub-steps:**
 - [ ] 3.2 Implement custom `Checkbox` class using MaixUI primitives
- [ ] 3.3 Implement custom `Button` class with touch event handling
- [ ] 3.4 Design camera preview area (top 80% of screen)
- [ ] 3.5 Create right sidebar for AI model toggle checkboxes
- [ ] 3.6 Design bottom action bar with start/stop button and status indicators
- [ ] 3.7 Implement touch event routing system
- [ ] 3.8 Add visual feedback for button presses and checkbox states
- [ ] 3.9 Create application state machine (INITIALIZING, IDLE, CAPTURING, ERROR)
- [ ] 3.10 Test UI responsiveness and layout on actual device

### Step 4: Camera Integration
**Sub-steps:**
- [ ] 4.1 Initialize `maix.camera.Camera` object with optimal resolution
- [ ] 4.2 Implement live camera preview in main UI loop
- [ ] 4.3 Add frame rate monitoring and display
- [ ] 4.4 Test different camera formats (RGB888, YUV420, etc.)
- [ ] 4.5 Implement camera settings adjustment (brightness, contrast)
- [ ] 4.6 Add image capture functionality for single frames
- [ ] 4.7 Implement video recording using `maix.video.Encoder`
- [ ] 4.8 Test video file output and playback compatibility
- [ ] 4.9 Handle camera initialization errors gracefully
- [ ] 4.10 Optimize camera performance for continuous operation

### Step 5: Audio Integration
**Sub-steps:**
- [ ] 5.1 Initialize `maix.audio` recording capability
- [ ] 5.2 Test basic audio recording and playback
- [ ] 5.3 Implement continuous audio buffer management
- [ ] 5.4 Initialize `maix.nn.Speech` for voice recognition
- [ ] 5.5 Configure keyword spotting models
- [ ] 5.6 Implement audio callback system for real-time processing
- [ ] 5.7 Create separate thread for audio processing
- [ ] 5.8 Test audio quality and recognition accuracy
- [ ] 5.9 Implement audio event queuing system
- [ ] 5.10 Add audio level indicators to UI

### Step 6: Object Classification
**Sub-steps:**
- [ ] 6.1 Load YOLOv8 object detection model (`/root/models/yolov8n.mud`)
- [ ] 6.2 Create `AIEngine` class with model management
- [ ] 6.3 Implement `process_frame()` method for object detection
- [ ] 6.4 Parse detection results (bounding boxes, labels, confidence)
- [ ] 6.5 Create JSON event format for object detections
- [ ] 6.6 Test detection accuracy with various objects
- [ ] 6.7 Implement confidence threshold filtering
- [ ] 6.8 Add visual bounding box overlay on camera preview
- [ ] 6.9 Test performance impact on frame rate
- [ ] 6.10 Validate JSON output format and structure

### Step 7: Face Recognition & Emotion
**Sub-steps:**
- [ ] 7.1 Load face detection model (`/root/models/yolov8n_face.mud`)
- [ ] 7.2 Load emotion classification model (`/root/models/face_emotion.mud`)
- [ ] 7.3 Implement face detection pipeline
- [ ] 7.4 Create face cropping and preprocessing for emotion analysis
- [ ] 7.5 Implement two-stage pipeline (detect faces → classify emotions)
- [ ] 7.6 Create JSON schema for face and emotion events
- [ ] 7.7 Test accuracy with multiple faces and expressions
- [ ] 7.8 Add face recognition database functionality
- [ ] 7.9 Implement face tracking between frames
- [ ] 7.10 Optimize performance for real-time emotion detection

### Step 8: Object Tracking & Counting
**Sub-steps:**
- [ ] 8.1 Implement object tracking using detection results
- [ ] 8.2 Create unique ID assignment for tracked objects
- [ ] 8.3 Implement object persistence across frames
- [ ] 8.4 Add object counting functionality
- [ ] 8.5 Create entry/exit zone detection
- [ ] 8.6 Implement tracking history and trajectory logging
- [ ] 8.7 Add JSON events for object tracking milestones
- [ ] 8.8 Test tracking accuracy with moving objects
- [ ] 8.9 Handle object occlusion and re-identification
- [ ] 8.10 Optimize tracking performance and memory usage

### Step 9: OCR Implementation
**Sub-steps:**
- [ ] 9.1 Load PP-OCR model (`/root/models/pp_ocr.mud`)
- [ ] 9.2 Implement text detection pipeline
- [ ] 9.3 Add text recognition functionality
- [ ] 9.4 Create text bounding box visualization
- [ ] 9.5 Implement text confidence filtering
- [ ] 9.6 Create JSON schema for OCR events
- [ ] 9.7 Test OCR accuracy with various text types and sizes
- [ ] 9.8 Handle multiple text regions in single frame
- [ ] 9.9 Add text orientation detection and correction
- [ ] 9.10 Optimize OCR processing frequency for performance

### Step 10: Hand & Gesture Recognition
**Sub-steps:**
- [ ] 10.1 Load hand landmarks model (`/root/models/hand_landmarks.mud`)
- [ ] 10.2 Implement hand detection and keypoint extraction
- [ ] 10.3 Create hand gesture classification pipeline
- [ ] 10.4 Add visual hand keypoint overlay
- [ ] 10.5 Implement gesture recognition from keypoint patterns
- [ ] 10.6 Create JSON schema for hand and gesture events
- [ ] 10.7 Test accuracy with various hand positions and gestures
- [ ] 10.8 Handle multiple hands in single frame
- [ ] 10.9 Add gesture history and pattern recognition
- [ ] 10.10 Optimize hand processing for real-time performance

### Step 11: Human Pose Classifier
**Sub-steps:**
- [ ] 11.1 Load human pose model (`/root/models/yolov8n_pose.mud`)
- [ ] 11.2 Implement 17-keypoint human pose detection
- [ ] 11.3 Create pose visualization with skeleton overlay
- [ ] 11.4 Implement pose classification (standing, sitting, lying, etc.)
- [ ] 11.5 Add pose tracking across frames
- [ ] 11.6 Create JSON schema for pose events
- [ ] 11.7 Test accuracy with various poses and body positions
- [ ] 11.8 Handle multiple people in single frame
- [ ] 11.9 Implement pose-based activity recognition
- [ ] 11.10 Optimize pose processing performance

### Step 12: JSON Output Format
**Sub-steps:**
- [ ] 12.1 Define comprehensive JSON schema with versioning
- [ ] 12.2 Create event envelope with metadata (timestamp, event_id, etc.)
- [ ] 12.3 Implement type-specific payload structures
- [ ] 12.4 Add UUID generation for unique event IDs
- [ ] 12.5 Implement ISO 8601 timestamp formatting
- [ ] 12.6 Create JSON validation functions
- [ ] 12.7 Add confidence score normalization
- [ ] 12.8 Implement sensor metadata inclusion (device info, model versions)
- [ ] 12.9 Test JSON serialization performance
- [ ] 12.10 Create JSON schema documentation

### Step 13: Local Storage Management
**Sub-steps:**
- [ ] 13.1 Create `DataLogger` class for file management
- [ ] 13.2 Implement SD card storage structure (`/sd/logs/`)
- [ ] 13.3 Add log file rotation based on capture sessions
- [ ] 13.4 Implement atomic file writing for data integrity
- [ ] 13.5 Create storage space monitoring and cleanup
- [ ] 13.6 Add file naming convention with timestamps
- [ ] 13.7 Implement log file compression for storage efficiency
- [ ] 13.8 Add error handling for storage failures
- [ ] 13.9 Create log file indexing for quick access
- [ ] 13.10 Test storage reliability under continuous operation

### Step 14: REST API Integration
**Sub-steps:**
- [ ] 14.1 Create `NetworkManager` class for Wi-Fi handling
- [ ] 14.2 Implement `NetworkUploader` class with threading
- [ ] 14.3 Add REST endpoint configuration (URL, authentication)
- [ ] 14.4 Implement HTTP POST requests using `requests` library
- [ ] 14.5 Add JSON payload formatting for API calls
- [ ] 14.6 Implement retry logic with exponential backoff
- [ ] 14.7 Add upload progress tracking and status reporting
- [ ] 14.8 Handle network errors and disconnections gracefully
- [ ] 14.9 Implement upload queue management
- [ ] 14.10 Test API integration with mock server

### Step 15: Detection Model Toggles
**Sub-steps:**
- [ ] 15.1 Create AI model configuration dictionary
- [ ] 15.2 Link UI checkboxes to model enable/disable flags
- [ ] 15.3 Implement dynamic model loading/unloading
- [ ] 15.4 Add NPU scheduler for time-slicing between models
- [ ] 15.5 Create model priority and frequency settings
- [ ] 15.6 Implement memory management for model switching
- [ ] 15.7 Add visual indicators for active models in UI
- [ ] 15.8 Test performance impact of different model combinations
- [ ] 15.9 Implement model configuration persistence
- [ ] 15.10 Add model status reporting and error handling

### Step 16: Testing & Debugging
**Sub-steps:**
- [ ] 16.1 Create unit tests for each AI model pipeline
- [ ] 16.2 Implement integration tests for full workflow
- [ ] 16.3 Add memory leak detection and monitoring
- [ ] 16.4 Create performance benchmarking suite
- [ ] 16.5 Test error handling and recovery scenarios
- [ ] 16.6 Implement logging system for debugging
- [ ] 16.7 Add UI responsiveness testing
- [ ] 16.8 Test storage and network failure scenarios
- [ ] 16.9 Perform stress testing with continuous operation
- [ ] 16.10 Document and fix all identified bugs

### Step 17: Performance Optimization
**Sub-steps:**
- [ ] 17.1 Profile CPU and NPU usage patterns
- [ ] 17.2 Optimize AI model processing intervals
- [ ] 17.3 Implement intelligent frame skipping
- [ ] 17.4 Add dual buffering for all AI models
- [ ] 17.5 Optimize memory allocation and garbage collection
- [ ] 17.6 Implement power management strategies
- [ ] 17.7 Optimize network upload batching
- [ ] 17.8 Add adaptive quality settings based on performance
- [ ] 17.9 Implement thermal throttling protection
- [ ] 17.10 Benchmark and validate all optimizations

### Step 18: Documentation & Deployment
**Sub-steps:**
- [ ] 18.1 Create user manual with setup instructions
- [ ] 18.2 Write developer documentation for code architecture
- [ ] 18.3 Create troubleshooting guide for common issues
- [ ] 18.4 Document API specification for REST endpoints
- [ ] 18.5 Create configuration file documentation
- [ ] 18.6 Write deployment scripts and procedures
- [ ] 18.7 Create backup and recovery procedures
- [ ] 18.8 Document hardware requirements and compatibility
- [ ] 18.9 Create training materials for end users
- [ ] 18.10 Prepare release notes and version documentation

### Step 19: Final Deployment & Monitoring
**Sub-steps:**
- [ ] 19.1 Prepare production firmware image
- [ ] 19.2 Create deployment checklist and validation procedures
- [ ] 19.3 Deploy to test environment for final validation
- [ ] 19.4 Implement monitoring and health check systems
- [ ] 19.5 Create remote diagnostic capabilities
- [ ] 19.6 Deploy to production environment
- [ ] 19.7 Monitor initial operation for 24-48 hours
- [ ] 19.8 Collect performance metrics and user feedback
- [ ] 19.9 Address any critical issues found in deployment
- [ ] 19.10 Create maintenance schedule and update procedures
 