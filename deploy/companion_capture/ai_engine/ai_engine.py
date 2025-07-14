"""
AI Processing Engine
Manages all AI models and coordinates processing

Author: Companion Intelligence
Date: July 13, 2025
"""

import time
import gc
from maix import nn, image
from utils.logger import get_logger

logger = get_logger('AIEngine')

class AIEngine:
    """Main AI processing engine that manages all AI models"""
    
    def __init__(self, config):
        """Initialize AI engine with configuration"""
        self.config = config
        self.models = {}
        self.active_models = []
        self.current_model_index = 0
        
        # Processing state
        self.last_process_time = {}
        self.frame_count = 0
        
        # Performance monitoring
        self.processing_times = {}
        self.error_counts = {}
        
        # Initialize AI models
        self._initialize_models()
        
        logger.info("AI Engine initialized")
    
    def _initialize_models(self):
        """Initialize all enabled AI models"""
        ai_config = self.config.get("ai_models", {})
        
        for model_name, model_config in ai_config.items():
            if model_config.get("enabled", False):
                try:
                    self._load_model(model_name, model_config)
                except Exception as e:
                    logger.error(f"Failed to load model {model_name}: {e}")
                    self.error_counts[model_name] = self.error_counts.get(model_name, 0) + 1
        
        # Update active models list
        self._update_active_models()
    
    def _load_model(self, model_name, model_config):
        """Load a specific AI model"""
        logger.info(f"Loading AI model: {model_name}")
        
        model_path = model_config.get("model_path", "")
        
        if model_name == "object_detection":
            self.models[model_name] = {
                "model": nn.YOLOv8(model=model_path, dual_buff=True),
                "config": model_config,
                "type": "detection"
            }
        
        elif model_name == "face_detection":
            self.models[model_name] = {
                "model": nn.YOLOv8(model=model_path, dual_buff=True),
                "config": model_config,
                "type": "face_detection"
            }
        
        elif model_name == "face_emotion":
            # Face emotion requires face detection first
            self.models[model_name] = {
                "model": None,  # Will be loaded when needed
                "config": model_config,
                "type": "emotion_classification"
            }
        
        elif model_name == "ocr":
            self.models[model_name] = {
                "model": None,  # OCR model initialization
                "config": model_config,
                "type": "ocr"
            }
        
        elif model_name == "hand_landmarks":
            self.models[model_name] = {
                "model": None,  # Hand landmarks model
                "config": model_config,
                "type": "hand_detection"
            }
        
        elif model_name == "pose_detection":
            self.models[model_name] = {
                "model": nn.YOLOv8(model=model_path, dual_buff=True),
                "config": model_config,
                "type": "pose_detection"
            }
        
        elif model_name == "audio_recognition":
            self.models[model_name] = {
                "model": None,  # Audio model
                "config": model_config,
                "type": "audio"
            }
        
        logger.info(f"Model {model_name} loaded successfully")
    
    def _update_active_models(self):
        """Update list of active models based on enabled status"""
        self.active_models = []
        
        for model_name in self.models:
            if self.config.is_model_enabled(model_name):
                self.active_models.append(model_name)
        
        # Sort by priority
        self.active_models.sort(
            key=lambda x: self.models[x]["config"].get("priority", 999)
        )
        
        logger.info(f"Active models: {self.active_models}")
    
    def toggle_model(self, model_name, enabled):
        """Toggle a model on/off"""
        if model_name in self.models:
            # Update configuration
            self.config.toggle_model(model_name, enabled)
            
            # Update active models list
            self._update_active_models()
            
            logger.info(f"Model {model_name} {'enabled' if enabled else 'disabled'}")
        else:
            logger.warning(f"Model {model_name} not found")
    
    def get_active_models(self):
        """Get list of currently active model names"""
        return self.active_models.copy()
    
    def _should_process_model(self, model_name):
        """Check if model should be processed based on interval"""
        current_time = time.ticks_ms()
        model_config = self.models[model_name]["config"]
        interval = model_config.get("processing_interval", 1) * 1000  # Convert to ms
        
        last_time = self.last_process_time.get(model_name, 0)
        
        if time.ticks_diff(current_time, last_time) >= interval:
            self.last_process_time[model_name] = current_time
            return True
        
        return False
    
    def process_frame(self, img):
        """Process frame through active AI models using round-robin scheduling"""
        self.frame_count += 1
        events = []
        
        if not self.active_models:
            return events
        
        # Round-robin NPU scheduling - process one model per frame
        if self.current_model_index >= len(self.active_models):
            self.current_model_index = 0
        
        model_name = self.active_models[self.current_model_index]
        self.current_model_index += 1
        
        # Check if this model should be processed based on its interval
        if self._should_process_model(model_name):
            try:
                start_time = time.ticks_ms()
                
                # Process with the selected model
                model_events = self._process_single_model(img, model_name)
                events.extend(model_events)
                
                # Track processing time
                processing_time = time.ticks_diff(time.ticks_ms(), start_time)
                self.processing_times[model_name] = processing_time
                
                logger.debug(f"Processed {model_name} in {processing_time}ms")
                
            except Exception as e:
                logger.error(f"Error processing {model_name}: {e}")
                self.error_counts[model_name] = self.error_counts.get(model_name, 0) + 1
        
        return events
    
    def _process_single_model(self, img, model_name):
        """Process image with a single model"""
        events = []
        model_info = self.models[model_name]
        model = model_info["model"]
        model_config = model_info["config"]
        model_type = model_info["type"]
        
        if model is None:
            return events
        
        # Process based on model type
        if model_type == "detection":
            events = self._process_object_detection(img, model, model_config)
        
        elif model_type == "face_detection":
            events = self._process_face_detection(img, model, model_config)
        
        elif model_type == "pose_detection":
            events = self._process_pose_detection(img, model, model_config)
        
        elif model_type == "emotion_classification":
            events = self._process_emotion_classification(img, model, model_config)
        
        elif model_type == "ocr":
            events = self._process_ocr(img, model, model_config)
        
        elif model_type == "hand_detection":
            events = self._process_hand_detection(img, model, model_config)
        
        return events
    
    def _process_object_detection(self, img, model, config):
        """Process object detection"""
        events = []
        confidence_threshold = config.get("confidence_threshold", 0.5)
        
        try:
            # Run detection
            objs = model.detect(img, conf_th=confidence_threshold)
            
            if objs:
                objects = []
                for obj in objs:
                    bbox = [obj.x, obj.y, obj.w, obj.h]
                    objects.append({
                        "label": obj.label,
                        "confidence": obj.score,
                        "bbox": bbox
                    })
                
                event = {
                    "timestamp": time.ticks_ms(),
                    "type": "object_detection",
                    "model": "yolov8",
                    "objects": objects,
                    "count": len(objects)
                }
                events.append(event)
        
        except Exception as e:
            logger.error(f"Object detection error: {e}")
        
        return events
    
    def _process_face_detection(self, img, model, config):
        """Process face detection"""
        events = []
        confidence_threshold = config.get("confidence_threshold", 0.7)
        
        try:
            # Run face detection
            faces = model.detect(img, conf_th=confidence_threshold)
            
            if faces:
                face_list = []
                for face in faces:
                    bbox = [face.x, face.y, face.w, face.h]
                    face_list.append({
                        "confidence": face.score,
                        "bbox": bbox
                    })
                
                event = {
                    "timestamp": time.ticks_ms(),
                    "type": "face_detection",
                    "model": "yolov8_face",
                    "faces": face_list,
                    "count": len(face_list)
                }
                events.append(event)
        
        except Exception as e:
            logger.error(f"Face detection error: {e}")
        
        return events
    
    def _process_pose_detection(self, img, model, config):
        """Process pose detection"""
        events = []
        confidence_threshold = config.get("confidence_threshold", 0.6)
        
        try:
            # Run pose detection
            poses = model.detect(img, conf_th=confidence_threshold)
            
            if poses:
                pose_list = []
                for pose in poses:
                    # Extract keypoints (this would need to be adapted based on actual API)
                    pose_data = {
                        "confidence": pose.score,
                        "bbox": [pose.x, pose.y, pose.w, pose.h],
                        "keypoints": []  # Would contain 17 keypoints for human pose
                    }
                    pose_list.append(pose_data)
                
                event = {
                    "timestamp": time.ticks_ms(),
                    "type": "pose_detection",
                    "model": "yolov8_pose",
                    "poses": pose_list,
                    "count": len(pose_list)
                }
                events.append(event)
        
        except Exception as e:
            logger.error(f"Pose detection error: {e}")
        
        return events
    
    def _process_emotion_classification(self, img, model, config):
        """Process emotion classification (requires face detection first)"""
        # This would typically work on face crops from face detection
        return []
    
    def _process_ocr(self, img, model, config):
        """Process OCR text recognition"""
        # OCR implementation would go here
        return []
    
    def _process_hand_detection(self, img, model, config):
        """Process hand landmark detection"""
        # Hand detection implementation would go here
        return []
    
    def get_performance_stats(self):
        """Get performance statistics"""
        return {
            "processing_times": self.processing_times.copy(),
            "error_counts": self.error_counts.copy(),
            "frame_count": self.frame_count,
            "active_models": len(self.active_models)
        }
    
    def cleanup(self):
        """Clean up AI engine resources"""
        logger.info("Cleaning up AI Engine...")
        
        # Clean up models
        for model_name in self.models:
            try:
                if self.models[model_name]["model"]:
                    del self.models[model_name]["model"]
            except Exception as e:
                logger.error(f"Error cleaning up model {model_name}: {e}")
        
        self.models.clear()
        self.active_models.clear()
        
        # Force garbage collection
        gc.collect()
        
        logger.info("AI Engine cleanup completed")
