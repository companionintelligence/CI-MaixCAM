#!/usr/bin/env python3
"""
Development Continuation Script
Demonstrates implementation of Step 5-6: Audio Integration & Object Classification

This script shows the next logical development steps based on the project plan
and continues from where the current camera integration left off.

Author: Companion Intelligence
Date: July 14, 2025
"""

from maix import camera, display, image, nn, app, time, audio
import math
import json


class AudioProcessor:
    """Audio processing for life logging - Step 5 implementation"""
    
    def __init__(self, config):
        self.config = config
        self.audio_enabled = False
        self.recording = False
        self.audio_buffer = []
        
        try:
            self._initialize_audio()
        except Exception as e:
            print(f"Audio initialization failed: {e}")
    
    def _initialize_audio(self):
        """Initialize audio recording capability"""
        print("🎤 Initializing audio...")
        
        # Audio configuration
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_size = 1024
        
        # Initialize audio recording
        # Note: This is conceptual - actual MaixPy audio API may differ
        try:
            self.recorder = audio.Recorder(
                sample_rate=self.sample_rate,
                channels=self.channels,
                chunk_size=self.chunk_size
            )
            self.audio_enabled = True
            print("✅ Audio initialized successfully")
        except Exception as e:
            print(f"❌ Audio initialization failed: {e}")
            self.audio_enabled = False
    
    def start_recording(self):
        """Start audio recording"""
        if self.audio_enabled and not self.recording:
            try:
                self.recorder.start()
                self.recording = True
                print("🔴 Audio recording started")
            except Exception as e:
                print(f"Failed to start recording: {e}")
    
    def stop_recording(self):
        """Stop audio recording"""
        if self.recording:
            try:
                self.recorder.stop()
                self.recording = False
                print("⏹️ Audio recording stopped")
            except Exception as e:
                print(f"Failed to stop recording: {e}")
    
    def process_audio_frame(self):
        """Process audio frame for voice recognition"""
        if not self.recording:
            return []
        
        events = []
        try:
            # Get audio chunk
            audio_chunk = self.recorder.read()
            
            if audio_chunk:
                # Simple audio level detection
                audio_level = sum(abs(sample) for sample in audio_chunk) / len(audio_chunk)
                
                # Voice activity detection threshold
                if audio_level > 1000:  # Adjust threshold as needed
                    event = {
                        "timestamp": time.ticks_ms(),
                        "type": "audio_activity",
                        "model": "audio_detector",
                        "data": {
                            "audio_level": audio_level,
                            "duration": len(audio_chunk) / self.sample_rate
                        }
                    }
                    events.append(event)
                    print(f"🔊 Audio activity detected: level={audio_level}")
        
        except Exception as e:
            print(f"Audio processing error: {e}")
        
        return events


class AdvancedAIEngine:
    """Enhanced AI Engine with multiple model support - Step 6 implementation"""
    
    def __init__(self, config):
        self.config = config
        self.models = {}
        self.active_models = []
        self.current_model_index = 0
        self.processing_stats = {}
        
        # Model performance tracking
        self.frame_times = {}
        self.error_counts = {}
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize all AI models"""
        print("🤖 Initializing AI models...")
        
        # Object Detection Model
        self._load_object_detection_model()
        
        # Face Detection Model
        self._load_face_detection_model()
        
        # OCR Model (if enabled)
        if self.config.get("ai_models", {}).get("ocr", {}).get("enabled", False):
            self._load_ocr_model()
        
        # Pose Detection Model (if enabled)
        if self.config.get("ai_models", {}).get("pose_detection", {}).get("enabled", False):
            self._load_pose_model()
        
        self._update_active_models()
    
    def _load_object_detection_model(self):
        """Load YOLOv8 object detection model"""
        try:
            print("Loading object detection model...")
            model_path = "/root/models/yolov8n.mud"
            
            detector = nn.YOLOv8(model=model_path, dual_buff=True)
            
            self.models["object_detection"] = {
                "model": detector,
                "type": "detection",
                "labels": detector.labels,
                "input_size": (detector.input_width(), detector.input_height()),
                "enabled": True
            }
            print(f"✅ Object detection loaded: {len(detector.labels)} classes")
            
        except Exception as e:
            print(f"❌ Failed to load object detection: {e}")
            self.error_counts["object_detection"] = 1
    
    def _load_face_detection_model(self):
        """Load Retinaface face detection model"""
        try:
            print("Loading face detection model...")
            model_path = "/root/models/retinaface.mud"
            
            detector = nn.Retinaface(model=model_path, dual_buff=True)
            
            self.models["face_detection"] = {
                "model": detector,
                "type": "face_detection",
                "input_size": (detector.input_width(), detector.input_height()),
                "enabled": True
            }
            print("✅ Face detection loaded")
            
        except Exception as e:
            print(f"❌ Failed to load face detection: {e}")
            self.error_counts["face_detection"] = 1
    
    def _load_ocr_model(self):
        """Load PP-OCR text recognition model"""
        try:
            print("Loading OCR model...")
            model_path = "/root/models/pp_ocr.mud"
            
            ocr = nn.PP_OCR(model=model_path)
            
            self.models["ocr"] = {
                "model": ocr,
                "type": "ocr",
                "input_size": (ocr.input_width(), ocr.input_height()),
                "enabled": True
            }
            print("✅ OCR model loaded")
            
        except Exception as e:
            print(f"❌ Failed to load OCR: {e}")
            self.error_counts["ocr"] = 1
    
    def _load_pose_model(self):
        """Load YOLOv8 pose detection model"""
        try:
            print("Loading pose detection model...")
            model_path = "/root/models/yolov8n_pose.mud"
            
            detector = nn.YOLOv8(model=model_path, dual_buff=True)
            
            self.models["pose_detection"] = {
                "model": detector,
                "type": "pose_detection",
                "labels": detector.labels,
                "input_size": (detector.input_width(), detector.input_height()),
                "enabled": True
            }
            print("✅ Pose detection loaded")
            
        except Exception as e:
            print(f"❌ Failed to load pose detection: {e}")
            self.error_counts["pose_detection"] = 1
    
    def _update_active_models(self):
        """Update list of active models"""
        self.active_models = [name for name, model in self.models.items() if model["enabled"]]
        print(f"Active models: {self.active_models}")
    
    def process_frame_round_robin(self, img):
        """Process frame using round-robin model scheduling"""
        events = []
        
        if not self.active_models:
            return events
        
        # Round-robin: process one model per frame for performance
        if self.current_model_index >= len(self.active_models):
            self.current_model_index = 0
        
        model_name = self.active_models[self.current_model_index]
        self.current_model_index += 1
        
        # Process with selected model
        start_time = time.ticks_ms()
        
        try:
            if model_name == "object_detection":
                events = self._process_object_detection(img)
            elif model_name == "face_detection":
                events = self._process_face_detection(img)
            elif model_name == "ocr":
                events = self._process_ocr(img)
            elif model_name == "pose_detection":
                events = self._process_pose_detection(img)
            
            # Track processing time
            processing_time = time.ticks_diff(time.ticks_ms(), start_time)
            self.frame_times[model_name] = processing_time
            
            if events:
                print(f"🔍 {model_name}: {len(events)} events in {processing_time}ms")
        
        except Exception as e:
            print(f"❌ Error processing {model_name}: {e}")
            self.error_counts[model_name] = self.error_counts.get(model_name, 0) + 1
        
        return events
    
    def _process_object_detection(self, img):
        """Process object detection"""
        events = []
        model_info = self.models["object_detection"]
        detector = model_info["model"]
        
        objs = detector.detect(img, conf_th=0.5, iou_th=0.45)
        
        if objs:
            objects = []
            for obj in objs:
                objects.append({
                    "label": detector.labels[obj.class_id],
                    "confidence": obj.score,
                    "bbox": [obj.x, obj.y, obj.w, obj.h]
                })
            
            event = {
                "timestamp": time.ticks_ms(),
                "type": "object_detection",
                "model": "yolov8",
                "data": {
                    "objects": objects,
                    "count": len(objects)
                }
            }
            events.append(event)
            
            # Draw detections on image
            for obj in objs:
                img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)
                label = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
                img.draw_string(obj.x, obj.y, label, color=image.COLOR_RED)
        
        return events
    
    def _process_face_detection(self, img):
        """Process face detection"""
        events = []
        model_info = self.models["face_detection"]
        detector = model_info["model"]
        
        faces = detector.detect(img, conf_th=0.4, iou_th=0.45)
        
        if faces:
            face_list = []
            for face in faces:
                face_list.append({
                    "confidence": face.score,
                    "bbox": [face.x, face.y, face.w, face.h],
                    "landmarks": len(face.points)
                })
            
            event = {
                "timestamp": time.ticks_ms(),
                "type": "face_detection",
                "model": "retinaface",
                "data": {
                    "faces": face_list,
                    "count": len(face_list)
                }
            }
            events.append(event)
            
            # Draw face detections
            for face in faces:
                img.draw_rect(face.x, face.y, face.w, face.h, color=image.COLOR_GREEN)
                radius = math.ceil(face.w / 10)
                img.draw_keypoints(face.points, image.COLOR_GREEN, size=radius if radius < 5 else 4)
        
        return events
    
    def _process_ocr(self, img):
        """Process OCR text recognition"""
        events = []
        model_info = self.models["ocr"]
        ocr = model_info["model"]
        
        text_objs = ocr.detect(img)
        
        if text_objs:
            texts = []
            for obj in text_objs:
                texts.append({
                    "text": obj.char_str(),
                    "bbox": obj.box.to_list()
                })
            
            event = {
                "timestamp": time.ticks_ms(),
                "type": "ocr_detection",
                "model": "pp_ocr",
                "data": {
                    "texts": texts,
                    "count": len(texts)
                }
            }
            events.append(event)
            
            # Draw text detections
            for obj in text_objs:
                points = obj.box.to_list()
                img.draw_keypoints(points, image.COLOR_BLUE, 4, -1, 1)
                img.draw_string(obj.box.x4, obj.box.y4, obj.char_str(), image.COLOR_BLUE)
        
        return events
    
    def _process_pose_detection(self, img):
        """Process pose detection"""
        events = []
        model_info = self.models["pose_detection"]
        detector = model_info["model"]
        
        poses = detector.detect(img, conf_th=0.5, iou_th=0.45, keypoint_th=0.5)
        
        if poses:
            pose_list = []
            for pose in poses:
                pose_list.append({
                    "label": detector.labels[pose.class_id],
                    "confidence": pose.score,
                    "bbox": [pose.x, pose.y, pose.w, pose.h],
                    "keypoints": len(pose.points)
                })
            
            event = {
                "timestamp": time.ticks_ms(),
                "type": "pose_detection",
                "model": "yolov8_pose",
                "data": {
                    "poses": pose_list,
                    "count": len(pose_list)
                }
            }
            events.append(event)
            
            # Draw pose detections
            for pose in poses:
                img.draw_rect(pose.x, pose.y, pose.w, pose.h, color=image.COLOR_YELLOW)
                detector.draw_pose(img, pose.points, 4, image.COLOR_YELLOW)
        
        return events
    
    def get_stats(self):
        """Get processing statistics"""
        return {
            "models_loaded": len(self.models),
            "active_models": len(self.active_models),
            "frame_times": self.frame_times.copy(),
            "error_counts": self.error_counts.copy()
        }


def run_advanced_life_logger():
    """Run the advanced life logger with audio and multiple AI models"""
    print("🚀 Starting Advanced Life Logger")
    print("=" * 50)
    
    # Configuration
    config = {
        "audio": {"enabled": True},
        "ai_models": {
            "ocr": {"enabled": False},  # Start with basic models
            "pose_detection": {"enabled": False}
        }
    }
    
    # Initialize components
    audio_processor = AudioProcessor(config)
    ai_engine = AdvancedAIEngine(config)
    
    # Initialize camera and display
    cam = camera.Camera(640, 480)
    disp = display.Display()
    
    # Main loop
    frame_count = 0
    total_events = 0
    fps_history = []
    
    print("📱 Starting main loop...")
    print("Press Ctrl+C to stop")
    
    # Start audio recording
    audio_processor.start_recording()
    
    try:
        while not app.need_exit():
            time.fps_start()
            
            # Capture frame
            img = cam.read()
            
            # Process AI models (round-robin)
            ai_events = ai_engine.process_frame_round_robin(img)
            
            # Process audio
            audio_events = audio_processor.process_audio_frame()
            
            # Combine events
            all_events = ai_events + audio_events
            total_events += len(all_events)
            
            # Log events (in real app, would save to JSON file)
            for event in all_events:
                event_summary = f"{event['type']} - {event.get('data', {}).get('count', 0)} items"
                print(f"📊 Event: {event_summary}")
            
            # Draw frame info
            img.draw_string(10, 10, f"Frame: {frame_count}", color=image.COLOR_WHITE)
            img.draw_string(10, 30, f"Events: {total_events}", color=image.COLOR_WHITE)
            
            # Show display
            disp.show(img)
            
            # FPS calculation
            fps = time.fps()
            fps_history.append(fps)
            
            # Status update every 30 frames
            if frame_count % 30 == 0:
                avg_fps = sum(fps_history[-30:]) / len(fps_history[-30:])
                stats = ai_engine.get_stats()
                print(f"📈 Frame {frame_count}: FPS: {avg_fps:.1f}, Total Events: {total_events}")
                print(f"   Models: {stats['active_models']}, Errors: {sum(stats['error_counts'].values())}")
            
            frame_count += 1
    
    except KeyboardInterrupt:
        print("\n⏹️ Stopping life logger...")
    
    finally:
        audio_processor.stop_recording()
        
        # Final statistics
        avg_fps = sum(fps_history) / len(fps_history) if fps_history else 0
        print(f"\n📊 Final Statistics:")
        print(f"   Total Frames: {frame_count}")
        print(f"   Average FPS: {avg_fps:.1f}")
        print(f"   Total Events: {total_events}")
        print(f"   Events per Frame: {total_events/frame_count:.2f}")
        
        stats = ai_engine.get_stats()
        print(f"   AI Processing Times: {stats['frame_times']}")
        print(f"   AI Errors: {stats['error_counts']}")


if __name__ == "__main__":
    run_advanced_life_logger()
