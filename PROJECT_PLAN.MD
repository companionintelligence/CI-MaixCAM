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
 

| Step | Task | Description | Status |
|------|------|-------------|--------|
| 1 | Initial Setup | Setup Sipeed MaxiCam hardware and install MaixPy firmware. Verify device functionality. | ☐ |
| 2 | Development Environment | Install and configure MaixPy IDE. Ensure serial and Wi-Fi connectivity. | ☐ |
| 3 | UI Design | Design simple user interface with preview, start, stop, log, and detection model toggle checkboxes. | ☐ |
| 4 | Camera Integration | Develop and test camera preview and video recording functionalities. | ☐ |
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



# **Technical Development Plan: Companion Capture App for AI-Powered Life-Logging**


## **1.0 System Architecture and Design Philosophy**

This document outlines the technical development plan for the Companion Capture App, a sophisticated life-logging application designed for continuous operation on the Sipeed MaxiCam hardware. The plan details a robust, modular software architecture engineered to handle multiple concurrent AI tasks, a responsive graphical user interface, and reliable data persistence and network synchronization.


### **1.1 High-Level Architectural Blueprint**

The application will be constructed from four primary, decoupled software modules: the **GUI Manager**, the **AI Engine**, the **Data Logger**, and the **Network Uploader**. This modularity is paramount for managing complexity, enabling parallel development workstreams, and facilitating isolated unit testing.

The data flow is designed for clarity and efficiency:



1. The maix.camera peripheral serves as the primary data source, providing a continuous stream of image frames.
2. Frames are simultaneously fed to the **GUI Manager** for live preview on the device's display and to the **AI Engine** for analysis.
3. The **GUI Manager** captures all user interactions, such as toggling AI features or starting/stopping the capture process. These interactions update the configuration state of the **AI Engine**.
4. The **AI Engine**, based on its current configuration, processes incoming frames using one or more neural network models. It generates structured detection events (e.g., an object was detected at specific coordinates).
5. These events are passed to the **Data Logger**, which formats them into the specified JSON schema and appends them to a log file stored on the local SD card.
6. Operating asynchronously, the **Network Uploader** periodically scans for completed log files, reads their contents, and transmits the data to a designated REST server over WiFi.

This architecture ensures that the real-time processing pipeline (camera -> AI -> logger) is not blocked by potentially slow network operations.


### **1.2 Application State Management**

To ensure predictable and stable behavior, the application will be governed by a formal state machine. This approach eliminates ambiguity in control flow and provides a clear logical structure. The primary application states are:



* **INITIALIZING**: The initial state upon application launch. Responsibilities include initializing hardware peripherals (camera, display), loading all required AI models into memory, and establishing the initial UI layout.
* **IDLE**: The default operational state after initialization. The camera preview is active, and the UI is fully responsive to user input. However, no AI processing or data logging occurs. This is a low-power, "ready" state.
* **CAPTURING**: Entered when the user presses the "Start" button. In this state, the AI Engine is actively processing frames, and the Data Logger is writing any generated events to the local log file. The UI remains responsive.
* **UPLOADING**: This is not a primary application state but rather the state of a background thread. The Network Uploader operates independently of the main application state, handling data synchronization whenever a network connection is available.
* **ERROR**: A terminal state entered upon a critical, unrecoverable failure (e.g., failed to initialize the camera). The application will display an error message and halt further processing.


### **1.3 Core Execution Loop and Event-Driven Model**

A naive implementation might use separate, blocking loops for UI management and AI processing, which would result in either a frozen interface or a stalled AI pipeline. The foundational architectural decision for this application is the use of a **single, unified, non-blocking main loop**. This loop will integrate the MaixUI event system with the application's core logic, ensuring continuous UI responsiveness and real-time AI analysis.

The structure of the main loop will be as follows:


    Python

# Conceptual Main Loop \
container.reload(main_app_ui) # Load the main UI \
while True: \
    # 1. Service the MaixUI framework for event handling and drawing \
    container.forever() \
 \
    # 2. Execute one tick of the application's logic \
    app.tick() \
 \
    # 3. A small delay can be introduced to manage CPU usage if needed \
    time.sleep_ms(1) \


The container.forever() call, as described in MaixUI documentation, handles touch events and screen updates, returning control quickly.<sup>1</sup> The custom

app.tick() function will contain the application's state-driven logic. It will check if the current state is CAPTURING; if so, it will capture a single frame from the camera and dispatch it to the AI Engine for processing. This interleaving of UI and application logic within a single, fast-iterating loop is critical to the feasibility of the entire project.


## **2.0 Foundation: Hardware and Development Environment**

The success of this project hinges on a thorough understanding of the target platform and a standardized development environment.


### **2.1 Sipeed MaxiCam Platform Analysis**

The Sipeed MaxiCam is the designated hardware platform. Its specifications directly inform the design constraints and capabilities of the software.



* **Compute Resources**: The platform's core is a powerful dual-core RISC-V processor (up to 1GHz) coupled with a **1TOPS@INT8 Neural Processing Unit (NPU)**.<sup>3</sup> This specification dictates a critical requirement: all AI models deployed must be quantized to the INT8 data type to leverage the hardware acceleration provided by the NPU. CPU-based operations, such as those in OpenCV, should be used sparingly to avoid performance bottlenecks.<sup>5</sup>
* **Memory**: The device is equipped with **256MB of DDR3 RAM**.<sup>3</sup> While generous for a microcontroller, this is a significant constraint when running a Linux-based OS, the Python 3 interpreter, a graphical UI, and multiple large neural network models simultaneously. A rigorous memory management strategy will be essential throughout the development lifecycle.
* **Connectivity**: The inclusion of **WiFi6 (2.4G/5G)** and a USB-C port enables the core data upload requirement and simplifies development, respectively.<sup>3</sup> The USB connection can provide a virtual network adapter, allowing for easy SSH access and debugging with the MaixVision IDE.<sup>6</sup>
* **Peripherals**: The onboard camera (up to 500W), microphone, and SDIO interface for TF cards directly support the application's primary functions of image capture, voice recognition, and local data logging.<sup>3</sup>

<table>
  <tr>
   <td>
Feature
   </td>
   <td>Specification
   </td>
   <td>Impact on Development
   </td>
   <td>Source(s)
   </td>
  </tr>
  <tr>
   <td><strong>CPU</strong>
   </td>
   <td>1GHz RISC-V (Linux) + 700MHz RISC-V (RTOS)
   </td>
   <td>Provides ample processing power for application logic and OS tasks.
   </td>
   <td><sup>3</sup>
   </td>
  </tr>
  <tr>
   <td><strong>NPU</strong>
   </td>
   <td>1TOPS@INT8
   </td>
   <td>Critical for real-time AI. Mandates INT8 model quantization.
   </td>
   <td><sup>3</sup>
   </td>
  </tr>
  <tr>
   <td><strong>Memory</strong>
   </td>
   <td>256MB DDR3
   </td>
   <td>A key constraint. Requires careful memory management and model selection.
   </td>
   <td><sup>3</sup>
   </td>
  </tr>
  <tr>
   <td><strong>Storage</strong>
   </td>
   <td>Flash (Internal), SD Card (via SDIO)
   </td>
   <td>Flash for the OS and application; SD card for persistent JSON logging.
   </td>
   <td><sup>3</sup>
   </td>
  </tr>
  <tr>
   <td><strong>Connectivity</strong>
   </td>
   <td>WiFi6 (2.4G/5G), BLE 5.4, USB 2.0
   </td>
   <td>Enables robust data upload and simplified debugging/development.
   </td>
   <td><sup>3</sup>
   </td>
  </tr>
  <tr>
   <td><strong>Peripherals</strong>
   </td>
   <td>500W Camera, Microphone, Touchscreen
   </td>
   <td>Directly support the core requirements of the application.
   </td>
   <td><sup>3</sup>
   </td>
  </tr>
  <tr>
   <td><strong>OS/Language</strong>
   </td>
   <td>Linux + RTOS / Python 3
   </td>
   <td>Enables use of the full Python ecosystem (e.g., requests, json).
   </td>
   <td><sup>3</sup>
   </td>
  </tr>
</table>



### **2.2 Development Environment Setup**

A consistent development environment is crucial for team efficiency. All developers will adhere to the following setup:



1. **Firmware**: The latest stable release of **MaixPy v4** must be installed on the device. MaixPy v4 is a long-term support version designed for modern Sipeed hardware and uses the standard Python 3 language, providing access to a rich ecosystem of packages.<sup>3</sup>
2. **IDE**: The **MaixVision IDE** is the recommended development tool. Its ability to provide a real-time camera feed on the computer, execute scripts remotely, and transfer files makes it exceptionally well-suited for debugging computer vision applications on the device.<sup>6</sup>
3. **File Transfer**: Files will be transferred to the device primarily through the MaixVision IDE's built-in tools.<sup>8</sup> For automation or command-line workflows, tools like \
rshell or ampy can be used.<sup>10</sup>
4. **Device Connection**: Initial device setup will follow the documented procedure of connecting via USB to establish a virtual Ethernet connection. This provides an IP address for the device, enabling connection via SSH and the MaixVision IDE.<sup>6</sup>

A critical point of clarification for the development team is the distinction between MaixPy versions. Research materials contain references to both the modern MaixPy v4 (for MaixCAM) and the legacy MaixPy v1 (for the older K210 platform). The K210 platform used a MicroPython-based environment and a different AI API centered on a KPU module.<sup>11</sup> The MaixCAM platform, as specified for this project, runs a full Python 3 environment and uses the modern

maix.nn module for all AI operations.<sup>14</sup> Any attempt to use

KPU code or examples will fail. **All development for this project must exclusively use the MaixPy v4 framework and the maix.nn API.**


## **3.0 Graphical User Interface (GUI) Implementation with MaixUI**

The user interface will be built using the MaixUI framework, which is designed for high performance and low memory usage on embedded systems.<sup>16</sup>


### **3.1 UI Layout and Composition**

The screen will be partitioned into three functional areas to prioritize information and accessibility:



* **Camera Preview (Top 80%):** A large, prominent area dedicated to displaying the live feed from the camera.
* **Control Panel (Right Sidebar):** A vertical stack of checkboxes for toggling each of the specified AI features.
* **Action Bar (Bottom):** A bar containing a large "Start/Stop Capture" button and status indicators (e.g., FPS, Recording Status).


### **3.2 Implementing the Live Camera Preview**

The live preview is the centerpiece of the UI. It will be rendered in a draw_preview function called within the main application loop. This function will perform two simple steps:



1. Read the latest frame from the initialized camera object: img = cam.read().
2. Draw the captured maix.image.Image object directly onto the main UI canvas at position (0, 0): ui.canvas.draw_image(img, 0, 0).

The final ui.display() call at the end of the main loop will then push the updated canvas to the physical screen.<sup>1</sup>


### **3.3 Interactive Control Elements**

The MaixUI framework does not provide a standard library of pre-built widgets like buttons or checkboxes; it is a drawing and event-handling framework, not a widget toolkit.<sup>16</sup> Therefore, all interactive elements must be custom-built using drawing primitives and manual touch-event handling. This requires dedicated development effort to create reusable UI component classes.

A Checkbox class will be implemented to manage its state (e.g., self.checked = True/False), its screen position, and its drawing logic. When its draw() method is called, it will render a rectangle using ui.canvas.draw_rect and a text label with ui.canvas.draw_string. If self.checked is true, it will also draw a checkmark or 'X' inside the rectangle.

Similarly, a Button class will be created to manage its appearance and state (e.g., pressed, released).


#### **3.3.1 Start/Stop Capture Button Logic**

A Button object will be instantiated for the "Start/Stop" control. In the main loop, its draw() method will render it on the canvas. The application's touch handler will check if a touch event's coordinates fall within the button's bounding box. If a touch is detected, the handler will toggle the application's global state between IDLE and CAPTURING and potentially change the button's text (e.g., from "Start" to "Stop").


#### **3.3.2 AI Feature Toggling Mechanism**

A list of Checkbox objects will be created, one for each AI feature specified in the requirements. Each checkbox instance will be linked to a boolean flag in the AI Engine's configuration dictionary. When a user touches a checkbox, its handle_touch() method will flip its internal boolean state, redraw itself in the new state, and update the corresponding configuration flag in the AI Engine.


### **3.4 Handling User Input and UI Events**

MaixUI is fundamentally event-driven.<sup>16</sup> A central touch-handling function will be implemented. This function will be called by the framework when a touch event occurs. It will receive the touch coordinates

(x, y) and iterate through a list of all interactive UI elements (the Start/Stop button and all checkboxes). It will call a is_touched(x, y) method on each element to determine which, if any, was the target of the interaction, and then trigger that element's specific action.


## **4.0 The AI Engine: Multi-Model Integration and Management**

The AI Engine is the computational core of the application, responsible for managing and executing all neural network models.


### **4.1 AI Engine Core**

A central AIEngine class will be implemented to orchestrate all AI tasks. This class will have the following responsibilities:



* **Model Initialization**: On startup, it will load all necessary AI models from their respective files (.mud format) and hold the initialized maix.nn objects (e.g., nn.YOLOv8, nn.Classifier) in memory. This avoids the significant overhead of loading models from storage during runtime.
* **Configuration Management**: It will maintain a dictionary of boolean flags (e.g., {'object_detection_enabled': True, 'emotion_detection_enabled': False,...}), which is directly controlled by the UI checkboxes.
* **Frame Processing**: It will expose a single process_frame(img) method. This method is the entry point for all AI analysis and contains the crucial NPU scheduling logic.

<table>
  <tr>
   <td>
Feature Name
   </td>
   <td>MaixPy Class
   </td>
   <td>Default Model File
   </td>
   <td>Relevant Source(s)
   </td>
  </tr>
  <tr>
   <td><strong>Object Detection</strong>
   </td>
   <td>maix.nn.YOLOv8
   </td>
   <td>/root/models/yolov8n.mud
   </td>
   <td><sup>15</sup>
   </td>
  </tr>
  <tr>
   <td><strong>Face Detection</strong>
   </td>
   <td>maix.nn.FaceRecognizer
   </td>
   <td>/root/models/yolov8n_face.mud
   </td>
   <td><sup>18</sup>
   </td>
  </tr>
  <tr>
   <td><strong>Emotion Analysis</strong>
   </td>
   <td>maix.nn.Classifier
   </td>
   <td>/root/models/face_emotion.mud
   </td>
   <td><sup>20</sup>
   </td>
  </tr>
  <tr>
   <td><strong>OCR</strong>
   </td>
   <td>maix.nn.PP_OCR
   </td>
   <td>/root/models/pp_ocr.mud
   </td>
   <td><sup>21</sup>
   </td>
  </tr>
  <tr>
   <td><strong>Pose Estimation</strong>
   </td>
   <td>maix.nn.YOLOv8
   </td>
   <td>/root/models/yolov8n_pose.mud
   </td>
   <td><sup>17</sup>
   </td>
  </tr>
  <tr>
   <td><strong>Hand Landmark Analysis</strong>
   </td>
   <td>maix.nn.HandLandmarks
   </td>
   <td>/root/models/hand_landmarks.mud
   </td>
   <td><sup>24</sup>
   </td>
  </tr>
  <tr>
   <td><strong>Voice Recognition</strong>
   </td>
   <td>maix.nn.Speech
   </td>
   <td>/root/models/am_3332_192_int8.mud
   </td>
   <td><sup>26</sup>
   </td>
  </tr>
</table>



### **4.2 AI Feature Implementation Details**

The AIEngine will execute the following logic for each enabled feature.



* **Object/Face Detection**: When enabled, the engine will pass the image to the nn.YOLOv8.detect() or nn.FaceRecognizer.recognize() method. The returned objects contain the bounding box, class ID, and confidence score, which will be formatted into a JSON event.<sup>15</sup>
* **Facial Emotion Analysis**: This is a two-stage pipeline. The engine first gets face bounding boxes from the face detector. For each face, it uses landmarks_detector.crop_image to create a standardized face chip. This chip is converted to grayscale and passed to the nn.Classifier.classify() method to get emotion predictions.<sup>20</sup>
* **OCR**: The engine will call the nn.PP_OCR.detect() method, which performs both text detection and recognition. The resulting objects, containing bounding boxes and the recognized string, will be logged.<sup>21</sup>
* **Pose/Hand Analysis**: For human pose, the engine will use nn.YOLOv8 with a pose-specific model to get 17 body keypoints.<sup>17</sup> For hands, it will use \
nn.HandLandmarks to detect 21 keypoints per hand.<sup>24</sup> A secondary classifier may be needed for specific gesture recognition.<sup>25</sup>
* **Voice Recognition**: This feature will be handled differently to avoid blocking the vision pipeline. The nn.Speech module will be initialized to use the microphone and configured for keyword spotting. It will run in a separate, dedicated thread, using a callback function to push detected keywords into the main application's event queue for logging.<sup>26</sup>


### **4.3 NPU Resource Scheduling**

The core challenge of the AI Engine is managing the execution of multiple complex models on a single NPU. Running all enabled models sequentially on every frame would result in an unacceptably low frame rate. Loading and unloading models dynamically is also too slow.

The solution is to implement an intelligent NPU scheduler within the AIEngine.process_frame() method. This scheduler will use a **time-slicing (round-robin) approach**. It will maintain a list of currently active AI tasks (based on the UI toggles) and a frame counter. On each call, it will execute only one AI task from the active list, then advance to the next task on the subsequent call.

For example:



* Frame 1: Run Object Detection
* Frame 2: Run Face/Emotion Detection
* Frame 3: Run OCR
* Frame 4: Run Pose Estimation
* Frame 5: Run Hand Landmark Detection
* Frame 6: Run Object Detection (cycle repeats)

This approach ensures that the NPU's resources are shared fairly over time, allowing all enabled features to provide periodic updates without grinding the system to a halt. This scheduling mechanism is the most critical architectural component of the AI Engine and is fundamental to achieving the project's goals on the available hardware.


## **5.0 Data Logging and On-Device Persistence**

All events generated by the AI Engine must be reliably stored on the device before being uploaded.


### **5.1 JSON Event Schema Definition**

A strict, versioned JSON schema will be enforced for all logged data. This ensures consistency and simplifies parsing for the backend server. Each event will be a JSON object with a common envelope and a type-specific payload.


<table>
  <tr>
   <td>Field Name
   </td>
   <td>Data Type
   </td>
   <td>Description
   </td>
   <td>Example
   </td>
  </tr>
  <tr>
   <td><strong>event_id</strong>
   </td>
   <td>String (UUID)
   </td>
   <td>A unique identifier for this specific event.
   </td>
   <td>"a1b2c3d4-..."
   </td>
  </tr>
  <tr>
   <td><strong>timestamp_iso8601</strong>
   </td>
   <td>String (ISO 8601)
   </td>
   <td>The UTC timestamp when the event was generated.
   </td>
   <td>"2025-03-15T14:30:05.123Z"
   </td>
  </tr>
  <tr>
   <td><strong>event_type</strong>
   </td>
   <td>String
   </td>
   <td>The type of AI event.
   </td>
   <td>"object_detection"
   </td>
  </tr>
  <tr>
   <td><strong>payload</strong>
   </td>
   <td>Object
   </td>
   <td>A nested object containing data specific to the event type.
   </td>
   <td>{...}
   </td>
  </tr>
  <tr>
   <td><em>payload.detections</em>
   </td>
   <td>Array of Objects
   </td>
   <td>(For object_detection) List of detected items.
   </td>
   <td>[{"label": "person",...}]
   </td>
  </tr>
  <tr>
   <td><em>payload.label</em>
   </td>
   <td>String
   </td>
   <td>The class name of the detected object or face.
   </td>
   <td>"person", "happy"
   </td>
  </tr>
  <tr>
   <td><em>payload.confidence</em>
   </td>
   <td>Float
   </td>
   <td>The model's confidence score for the detection (0.0 to 1.0).
   </td>
   <td>0.92
   </td>
  </tr>
  <tr>
   <td><em>payload.bounding_box</em>
   </td>
   <td>Array of Int
   </td>
   <td>The [x, y, width, height] of the bounding box.
   </td>
   <td>``
   </td>
  </tr>
  <tr>
   <td><em>payload.text</em>
   </td>
   <td>String
   </td>
   <td>(For ocr) The recognized text string.
   </td>
   <td>"Hello World"
   </td>
  </tr>
  <tr>
   <td><em>payload.keypoints</em>
   </td>
   <td>Array of Int
   </td>
   <td>(For pose/hand) A flat list of [x1, y1, x2, y2,...] coordinates.
   </td>
   <td>[150, 60, 152, 61,...]
   </td>
  </tr>
</table>



### **5.2 Local File Management Strategy**

The Data Logger module will handle writing these JSON events to the file system.



* **Storage Location**: All logs will be written to the SD card (mounted at /sd/), as the internal flash has limited capacity and write cycles.<sup>10</sup>
* **File I/O**: MaixPy v4's full Python 3 support allows the use of standard, robust file handling with context managers: with open(filepath, 'a') as f:. This is a significant improvement over more limited MicroPython systems.<sup>7</sup> Each JSON event will be written as a single line to the log file.
* **Log Rotation**: To prevent log files from growing indefinitely and to simplify the upload process, a log rotation strategy will be implemented. A new log file (e.g., capture_log_YYYYMMDD_HHMMSS.json) will be created whenever the CAPTURING state is initiated. This ensures that each capture session has its own discrete log file.


## **6.0 Network Communication and Data Synchronization**

The Network Uploader module is responsible for reliably transmitting the locally stored JSON logs to the remote server.


### **6.1 WiFi Connectivity Management**

A NetworkManager class will encapsulate all WiFi functionality. On application startup, it will attempt to connect to a pre-configured network using credentials stored in a configuration file (e.g., /boot/wifi.ssid and /boot/wifi.pass).<sup>6</sup> It will use the

maix.network.wifi.Wifi class to manage the connection state, periodically checking wifi.is_connected() and implementing a retry mechanism with exponential backoff in case of disconnection.<sup>27</sup>


### **6.2 RESTful Data Upload Protocol**

The NetworkUploader will operate in a dedicated background thread to ensure it never blocks the main UI and AI processing loop. Its logic will be:



1. Periodically scan the /sd/ log directory for completed log files.
2. For each file, read its entire content.
3. Construct an HTTP POST request with the Content-Type: application/json header.
4. Send the log data to the server's REST endpoint. The requests library, available in the MaixPy v4 environment, is perfectly suited for this task. The core call will be requests.post(url, json=payload_data), which automatically handles JSON serialization and header setting.<sup>28</sup>


### **6.3 Error Handling and Retry Logic**

Robustness is key for a life-logging application. The uploader must gracefully handle network failures and server errors.



* **Connection Errors**: If a requests.exceptions.ConnectionError is caught, the upload attempt will be aborted, and the file will be left on the device for a future retry.
* **Server Errors**: If the server returns a non-2xx status code (e.g., 500 Internal Server Error), the upload will also be considered failed, and the file will be preserved.<sup>31</sup>
* **Success Handling**: Only after a successful upload (i.e., a 2xx response from the server) will the local log file be moved to an uploaded/ subdirectory on the SD card. This prevents data loss and avoids re-uploading the same data.


## **7.0 Performance, Optimization, and System Constraints**

Achieving real-time performance with multiple AI models on an embedded device requires a focus on optimization.


### **7.1 Managing Concurrent AI Inference**

Beyond the core NPU time-slicing scheduler, several other techniques will be employed:



* **Model-Specific Intervals**: Not all AI tasks require the same update frequency. Object detection might run every 2-3 frames, while OCR, a more computationally expensive and less time-sensitive task, could be scheduled to run only every 10-15 frames. These intervals will be configurable.
* **Dual Buffering**: The dual_buff=True parameter will be enabled when initializing all maix.nn models. This feature improves the efficiency of the NPU pipeline by allowing data to be prepared for the next inference while the current one is still executing, leading to higher overall throughput.<sup>14</sup>


### **7.2 Memory and Power Consumption Analysis**



* **Memory Management**: With only 256MB of RAM, memory is a premium resource. The development process will include mandatory, periodic checks of available memory using gc.mem_free() to detect leaks early.<sup>16</sup> Best practices, such as explicitly deleting large objects like image buffers ( \
del img) when they are no longer needed and periodically calling gc.collect(), will be enforced.
* **Power Consumption**: As a life-logging device, power efficiency is a long-term concern. While initial development will focus on functionality, future optimization phases could explore CPU frequency scaling or leveraging the MaixCAM's low-power 8051 core for managing system tasks when the main AI engine is in the IDLE state.<sup>3</sup>


## **8.0 Conclusion and Strategic Recommendations**

This plan outlines a comprehensive and architecturally sound approach to developing the Companion Capture App on the Sipeed MaxiCam. The design prioritizes modularity, performance on resource-constrained hardware, and data reliability.


### **8.1 Summary of the Development Strategy**

The core of the strategy is a modular, event-driven architecture built around a unified, non-blocking main loop. This loop services both a custom-built MaixUI graphical interface and a sophisticated AI Engine. The AI Engine's primary innovation is its time-slicing NPU scheduler, which enables the concurrent operation of multiple AI models by intelligently multiplexing access to the single NPU. Data is captured and logged locally to an SD card before being reliably synchronized to a remote server by a threaded network uploader.


### **8.2 Key Implementation Risks and Mitigation Strategies**



1. **Risk: NPU Overload and Low Frame Rates.** The demand to run multiple heavy AI models concurrently could overwhelm the NPU.
    * **Mitigation**: The primary mitigation is the **time-slicing AI Engine scheduler**. This is the most critical architectural safeguard against this risk. Further mitigation includes configurable, model-specific processing intervals.
2. **Risk: Memory Exhaustion.** Loading the OS, Python, the UI, and multiple AI models could exceed the 256MB RAM limit.
    * **Mitigation**: A strict memory budget will be established. Models will be chosen carefully for their size-to-performance ratio. Proactive memory management (del, gc.collect()) and continuous monitoring (gc.mem_free()) will be integral to the development workflow.
3. **Risk: Poor UI Performance.** A complex UI or a blocked main loop could lead to a laggy, unresponsive user experience.
    * **Mitigation**: The UI will be built with lightweight, custom components using MaixUI's drawing primitives. The non-blocking main loop architecture is designed specifically to ensure the UI thread is never stalled by AI or other long-running tasks.


### **8.3 Recommendations for Phased Development and Future Enhancements**

A phased approach is recommended to manage complexity and deliver value incrementally.



* **Phase 1: Core Functionality & UI Shell.**
    * Implement the application framework, the non-blocking main loop, and the state machine.
    * Build the complete UI with the live camera preview, custom button, and checkbox widgets.
    * Integrate a single AI feature (e.g., object detection) and the Data Logger to prove the end-to-end pipeline from camera to local JSON file.
* **Phase 2: Full AI Integration & Performance Tuning.**
    * Implement the AI Engine's time-slicing scheduler.
    * Incrementally add and test each remaining AI feature, carefully monitoring performance (FPS) and memory usage at each step.
    * Implement the threaded voice recognition module.
* **Phase 3: Networking & Robustness.**
    * Develop and integrate the threaded NetworkUploader module.
    * Implement robust error handling and retry logic for both WiFi connectivity and HTTP requests.
    * Conduct long-duration stress testing to ensure system stability.

Upon successful completion, future enhancements could include on-device model personalization (as suggested by self-learning classifier concepts <sup>32</sup>), more complex multi-stage gesture analysis <sup>25</sup>, and advanced power-saving modes.


#### Works cited



1. MaixUI basic usage guide - Sipeed Wiki, accessed July 13, 2025, [https://wiki.sipeed.com/soft/maixpy/en/course/others/maixui.html](https://wiki.sipeed.com/soft/maixpy/en/course/others/maixui.html)
2. sipeed_wiki/docs/soft/maixpy/en/course/others/maixui.md at main - GitHub, accessed July 13, 2025, [https://github.com/sipeed/sipeed_wiki/blob/main/docs/soft/maixpy/en/course/others/maixui.md](https://github.com/sipeed/sipeed_wiki/blob/main/docs/soft/maixpy/en/course/others/maixui.md)
3. MaixPy - PyPI, accessed July 13, 2025, [https://pypi.org/project/MaixPy/](https://pypi.org/project/MaixPy/)
4. Sipeed Maix Amigo Development Kit, accessed July 13, 2025, [https://www.mouser.com/pdfDocs/ProductOverview_SeeedStudio_102110463.pdf](https://www.mouser.com/pdfDocs/ProductOverview_SeeedStudio_102110463.pdf)
5. MaixPy/docs/doc/en/vision/opencv.md at main - GitHub, accessed July 13, 2025, [https://github.com/sipeed/MaixPy/blob/main/docs/doc/en/vision/opencv.md](https://github.com/sipeed/MaixPy/blob/main/docs/doc/en/vision/opencv.md)
6. MaixPy/docs/doc/en/README_no_screen.md at main - GitHub, accessed July 13, 2025, [https://github.com/sipeed/MaixPy/blob/main/docs/doc/en/README_no_screen.md](https://github.com/sipeed/MaixPy/blob/main/docs/doc/en/README_no_screen.md)
7. sipeed/MaixPy: Easily create AI projects with Python on edge device - GitHub, accessed July 13, 2025, [https://github.com/sipeed/MaixPy](https://github.com/sipeed/MaixPy)
8. MaixPy IDE installation and use - Sipeed Wiki, accessed July 13, 2025, [https://wiki.sipeed.com/soft/maixpy/en/get_started/env_maixpyide.html](https://wiki.sipeed.com/soft/maixpy/en/get_started/env_maixpyide.html)
9. Install MaixPyIDE(optional) - MaixPy IDE, accessed July 13, 2025, [http://www.86x.org/cn-maixpy/cn.maixpy.sipeed.com/en/get_started/maixpyide.html](http://www.86x.org/cn-maixpy/cn.maixpy.sipeed.com/en/get_started/maixpyide.html)
10. Edit and execute the file - Sipeed Wiki, accessed July 13, 2025, [https://wiki.sipeed.com/soft/maixpy/en/get_started/get_started_edit_file.html](https://wiki.sipeed.com/soft/maixpy/en/get_started/get_started_edit_file.html)
11. README.md - sipeed/MaixPy-v1 - GitHub, accessed July 13, 2025, [https://github.com/sipeed/MaixPy-v1/blob/master/README.md](https://github.com/sipeed/MaixPy-v1/blob/master/README.md)
12. KPU - Sipeed Wiki, accessed July 13, 2025, [https://wiki.sipeed.com/soft/maixpy/en/api_reference/Maix/kpu.html](https://wiki.sipeed.com/soft/maixpy/en/api_reference/Maix/kpu.html)
13. KPU · MaixPy DOC, accessed July 13, 2025, [http://www.86x.org/cn-maixpy/cn.maixpy.sipeed.com/en/libs/Maix/kpu.html](http://www.86x.org/cn-maixpy/cn.maixpy.sipeed.com/en/libs/Maix/kpu.html)
14. Using AI Models for Object Classification in MaixCAM MaixPy - MaixPy, accessed July 13, 2025, [https://wiki.sipeed.com/maixpy/doc/en/vision/classify.html](https://wiki.sipeed.com/maixpy/doc/en/vision/classify.html)
15. MaixPy/docs/doc/en/vision/yolov5.md at main - GitHub, accessed July 13, 2025, [https://github.com/sipeed/MaixPy/blob/main/docs/doc/en/vision/yolov5.md](https://github.com/sipeed/MaixPy/blob/main/docs/doc/en/vision/yolov5.md)
16. sipeed/MaixUI: This is the MicroPython UI framework. - GitHub, accessed July 13, 2025, [https://github.com/sipeed/MaixUI](https://github.com/sipeed/MaixUI)
17. MaixCAM MaixPy Human Pose Keypoint Detection - MaixPy, accessed July 13, 2025, [https://wiki.sipeed.com/maixpy/doc/en/vision/body_key_points.html](https://wiki.sipeed.com/maixpy/doc/en/vision/body_key_points.html)
18. MaixCAM MaixPy Face Recognition - MaixPy - Sipeed Wiki, accessed July 13, 2025, [https://wiki.sipeed.com/maixpy/doc/en/vision/face_recognition.html](https://wiki.sipeed.com/maixpy/doc/en/vision/face_recognition.html)
19. MaixCAM MaixPy Face Detection and Keypoint Detection - Sipeed Wiki, accessed July 13, 2025, [https://wiki.sipeed.com/maixpy/doc/en/vision/face_detection.html](https://wiki.sipeed.com/maixpy/doc/en/vision/face_detection.html)
20. MaixCAM MaixPy Facial Expression Recognition, Gender, Mask ..., accessed July 13, 2025, [https://wiki.sipeed.com/maixpy/doc/en/vision/face_emotion.html](https://wiki.sipeed.com/maixpy/doc/en/vision/face_emotion.html)
21. OCR Image Text Recognition with MaixCAM MaixPy - MaixPy, accessed July 13, 2025, [https://wiki.sipeed.com/maixpy/doc/en/vision/ocr.html](https://wiki.sipeed.com/maixpy/doc/en/vision/ocr.html)
22. MaixPy/examples/vision/ai_vision/nn_pp_ocr.py at main - GitHub, accessed July 13, 2025, [https://github.com/sipeed/MaixPy/blob/main/examples/vision/ai_vision/nn_pp_ocr.py](https://github.com/sipeed/MaixPy/blob/main/examples/vision/ai_vision/nn_pp_ocr.py)
23. YOLOv8-Pose body keypoint detection, 17 points - MaixHub, accessed July 13, 2025, [https://maixhub.com/model/zoo/401](https://maixhub.com/model/zoo/401)
24. MaixPy/docs/doc/en/vision/face_landmarks.md at main - GitHub, accessed July 13, 2025, [https://github.com/sipeed/MaixPy/blob/main/docs/doc/en/vision/face_landmarks.md](https://github.com/sipeed/MaixPy/blob/main/docs/doc/en/vision/face_landmarks.md)
25. MaixCAM MaixPy Hand Gesture Classification Based on Hand Keypoint Detection, accessed July 13, 2025, [https://wiki.sipeed.com/maixpy/doc/en/vision/hand_gesture_classification.html](https://wiki.sipeed.com/maixpy/doc/en/vision/hand_gesture_classification.html)
26. MaixPy/docs/doc/en/audio/keyword.md at main · sipeed/MaixPy ..., accessed July 13, 2025, [https://github.com/sipeed/MaixPy/blob/main/docs/doc/en/audio/keyword.md](https://github.com/sipeed/MaixPy/blob/main/docs/doc/en/audio/keyword.md)
27. maix.network.wifi - MaixPy - Sipeed Wiki, accessed July 13, 2025, [https://wiki.sipeed.com/maixpy/api/maix/network/wifi.html](https://wiki.sipeed.com/maixpy/api/maix/network/wifi.html)
28. Using HTTP Network Communication with MaixPy MaixCAM - Sipeed Wiki, accessed July 13, 2025, [https://wiki.sipeed.com/maixpy/doc/en/network/http.html](https://wiki.sipeed.com/maixpy/doc/en/network/http.html)
29. How do I post JSON using the Python Requests Library? - ReqBin, accessed July 13, 2025, [https://reqbin.com/code/python/m2g4va4a/python-requests-post-json-example](https://reqbin.com/code/python/m2g4va4a/python-requests-post-json-example)
30. How to POST JSON data with Python Requests? - Stack Overflow, accessed July 13, 2025, [https://stackoverflow.com/questions/9733638/how-to-post-json-data-with-python-requests](https://stackoverflow.com/questions/9733638/how-to-post-json-data-with-python-requests)
31. Python Requests: How to POST JSON Data with Ease in 2025 - Apidog, accessed July 13, 2025, [https://apidog.com/blog/python-requests-post-json/](https://apidog.com/blog/python-requests-post-json/)
32. Introduction - MaixHub, accessed July 13, 2025, [https://maixhub.com/model/zoo/61](https://maixhub.com/model/zoo/61)