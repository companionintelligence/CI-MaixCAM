"""
Configuration Management System
Handles all application settings and configurations

Author: Companion Intelligence
Date: July 13, 2025
"""

import json
import os
from typing import Dict, Any

from utils.models import CONFIG_KEY_TO_MODEL, migrate_model_states, read_model_states
from utils.paths import CONFIG_PATH, ensure_config_dir, migrate_legacy_config

class Config:
    """Configuration manager for the Companion Capture App"""
    
    def __init__(self, config_path=CONFIG_PATH):
        """Initialize configuration with default values"""
        self.config_path = config_path
        self.config = self._load_default_config()
        
        # Top-level keys written by other components (the setup screen stores
        # its model selection in the same file). They are not part of this
        # schema, so they are held aside on load and written back on save
        # instead of being silently dropped.
        self.foreign_keys = {}
        
        # Create config directory if it doesn't exist
        ensure_config_dir(config_path)
        
        # Seed from a legacy config file if this device predates the
        # canonical path
        migrate_legacy_config(config_path)
        
        # Load existing config if available
        self.load_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration values"""
        return {
            "app": {
                "name": "Companion Capture",
                "version": "1.0.0",
                "debug": False,
                "log_level": "INFO"
            },
            "camera": {
                "width": 640,
                "height": 480,
                "fps": 30,
                "format": "RGB888",
                "auto_exposure": True,
                "brightness": 0,
                "contrast": 0
            },
            "display": {
                "preview_area": {
                    "x": 0,
                    "y": 0,
                    "width": 480,
                    "height": 360
                },
                "ui_area": {
                    "x": 480,
                    "y": 0,
                    "width": 160,
                    "height": 480
                }
            },
            # Per-model tuning only. Whether a model runs is NOT stored here:
            # it lives once, in the top-level "model_states" record the setup
            # screen owns, and is read back through is_model_enabled().
            "ai_models": {
                "object_detection": {
                    "model_path": "/root/models/yolov8n.mud",
                    "confidence_threshold": 0.5,
                    "processing_interval": 3,
                    "priority": 1
                },
                "face_detection": {
                    "model_path": "/root/models/retinaface.mud",
                    "confidence_threshold": 0.4,
                    "processing_interval": 5,
                    "priority": 2
                },
                "face_emotion": {
                    "model_path": "/root/models/face_emotion.mud",
                    "confidence_threshold": 0.6,
                    "processing_interval": 10,
                    "priority": 3
                },
                "ocr": {
                    "model_path": "/root/models/pp_ocr.mud",
                    "confidence_threshold": 0.8,
                    "processing_interval": 15,
                    "priority": 4
                },
                "hand_landmarks": {
                    "model_path": "/root/models/hand_landmarks.mud",
                    "confidence_threshold": 0.7,
                    "processing_interval": 8,
                    "priority": 5
                },
                "pose_detection": {
                    "model_path": "/root/models/yolov8n_pose.mud",
                    "confidence_threshold": 0.5,
                    "processing_interval": 12,
                    "priority": 6
                },
                "audio_recognition": {
                    "processing_interval": 20,
                    "priority": 7
                }
            },
            "storage": {
                "base_path": "/sd/logs",
                "max_log_size_mb": 100,
                "rotation_interval_hours": 24,
                "compression_enabled": True,
                "cleanup_old_files": True,
                "max_storage_usage_percent": 80
            },
            "network": {
                "wifi_enabled": True,
                "upload_enabled": False,
                "upload_interval_seconds": 300,
                "retry_attempts": 3,
                "retry_delay_seconds": 30,
                "batch_size": 50,
                "endpoint_url": "https://api.example.com/upload",
                "api_key": "",
                "timeout_seconds": 30
            },
            "ui": {
                "theme": "dark",
                "show_fps": True,
                "show_memory": True,
                "show_ai_overlay": True,
                "touch_feedback": True,
                "status_update_interval_ms": 500
            },
            "performance": {
                "memory_warning_threshold_mb": 10,
                "memory_critical_threshold_mb": 5,
                "max_frame_skip": 5,
                "thermal_throttling_enabled": True,
                "thermal_threshold_celsius": 75
            }
        }
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    # Fold an older build's duplicate enabled-state records
                    # into model_states before anything reads them
                    migrate_model_states(loaded_config)
                    # Merge with defaults (only update existing keys)
                    self._merge_config(self.config, loaded_config)
                    # Keep anything outside this schema so save_config()
                    # round-trips it instead of destroying it
                    self.foreign_keys = {
                        key: value for key, value in loaded_config.items()
                        if key not in self.config
                    }
                print(f"Configuration loaded from {self.config_path}")
            else:
                # Save default config
                self.save_config()
                print(f"Default configuration created at {self.config_path}")
        except Exception as e:
            print(f"Error loading config: {e}")
            print("Using default configuration")
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            merged = dict(self.config)
            merged.update(self.foreign_keys)
            
            with open(self.config_path, 'w') as f:
                json.dump(merged, f, indent=2)
            print(f"Configuration saved to {self.config_path}")
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def _merge_config(self, base: Dict, update: Dict):
        """Recursively merge configuration dictionaries"""
        for key, value in update.items():
            if key in base:
                if isinstance(base[key], dict) and isinstance(value, dict):
                    self._merge_config(base[key], value)
                else:
                    base[key] = value
    
    def get(self, path: str, default=None):
        """Get configuration value using dot notation (e.g., 'camera.width')"""
        try:
            keys = path.split('.')
            value = self.config
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, path: str, value: Any):
        """Set configuration value using dot notation"""
        keys = path.split('.')
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
    
    def get_model_states(self) -> Dict[str, bool]:
        """Get the enabled state of every AI model

        The single stored copy is the top-level "model_states" key the setup
        screen writes. It is outside this class's schema, so load_config()
        parks it in foreign_keys and save_config() writes it straight back.
        """
        return read_model_states(self.foreign_keys)
    
    def get_ai_model_config(self, model_name: str) -> Dict[str, Any]:
        """Get configuration for specific AI model

        "enabled" is computed from model_states, not read from the stored
        ai_models entry, so it cannot disagree with what the app runs. The
        returned dict is a copy: writing to it stores nothing.
        """
        model_config = dict(self.get(f"ai_models.{model_name}", {}))
        if model_config:
            model_config["enabled"] = self.is_model_enabled(model_name)
        return model_config
    
    def get_ai_models_config(self) -> Dict[str, Any]:
        """Get every AI model's configuration, enabled state included"""
        return {
            model_name: self.get_ai_model_config(model_name)
            for model_name in self.config["ai_models"]
        }
    
    def is_model_enabled(self, model_name: str) -> bool:
        """Check if AI model is enabled

        A view over model_states, keyed by this class's short model names.
        """
        display_name = CONFIG_KEY_TO_MODEL.get(model_name, model_name)
        return self.get_model_states().get(display_name, False)
    
    def get_enabled_models(self) -> list:
        """Get list of enabled AI models"""
        enabled_models = []
        for model_name in self.config["ai_models"]:
            if self.is_model_enabled(model_name):
                enabled_models.append(model_name)
        return enabled_models
    
    def toggle_model(self, model_name: str, enabled: bool):
        """Toggle AI model on/off"""
        display_name = CONFIG_KEY_TO_MODEL.get(model_name, model_name)

        states = self.foreign_keys.get("model_states")
        if not isinstance(states, dict):
            states = self.get_model_states()
            self.foreign_keys["model_states"] = states

        states[display_name] = bool(enabled)
        self.save_config()
    
    def get_camera_config(self) -> Dict[str, Any]:
        """Get camera configuration"""
        return self.get("camera", {})
    
    def get_storage_config(self) -> Dict[str, Any]:
        """Get storage configuration"""
        return self.get("storage", {})
    
    def get_network_config(self) -> Dict[str, Any]:
        """Get network configuration"""
        return self.get("network", {})
    
    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI configuration"""
        return self.get("ui", {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration"""
        return self.get("performance", {})
