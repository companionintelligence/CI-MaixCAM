#!/usr/bin/env python3
"""
AI Models Examples and Test Implementation
Based on MaixPy examples for Companion Capture App

This file demonstrates proper MaixPy AI model usage patterns
for object detection, face detection, OCR, and pose estimation

Author: Companion Intelligence
Date: July 14, 2025
"""

from maix import camera, display, image, nn, app, time
import math

def test_object_detection():
    """Test object detection based on MaixPy example"""
    print("🔍 Testing Object Detection...")
    
    # Initialize model - using YOLOv8 for object detection
    detector = nn.YOLOv8(model="/root/models/yolov8n.mud", dual_buff=True)
    
    # Initialize camera with model's preferred input size
    cam = camera.Camera(detector.input_width(), detector.input_height(), detector.input_format())
    disp = display.Display()
    
    print(f"Camera: {detector.input_width()}x{detector.input_height()}")
    print(f"Available labels: {len(detector.labels)} classes")
    
    frame_count = 0
    while not app.need_exit() and frame_count < 50:  # Test for 50 frames
        time.fps_start()
        
        img = cam.read()
        objs = detector.detect(img, conf_th=0.5, iou_th=0.45)
        
        # Draw detections
        for obj in objs:
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)
            msg = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
            img.draw_string(obj.x, obj.y, msg, color=image.COLOR_RED)
            
            # Print detection info
            print(f"Detected: {detector.labels[obj.class_id]} ({obj.score:.2f}) at ({obj.x}, {obj.y}, {obj.w}, {obj.h})")
        
        disp.show(img)
        fps = time.fps()
        print(f"Frame {frame_count}: FPS: {fps:.1f}, Objects: {len(objs)}")
        
        frame_count += 1
    
    print("✅ Object Detection test completed")

def test_face_detection():
    """Test face detection based on MaixPy example"""
    print("👤 Testing Face Detection...")
    
    # Initialize face detector - using Retinaface
    detector = nn.Retinaface(model="/root/models/retinaface.mud", dual_buff=True)
    
    cam = camera.Camera(detector.input_width(), detector.input_height(), detector.input_format())
    disp = display.Display()
    
    print(f"Face detector: {detector.input_width()}x{detector.input_height()}")
    
    frame_count = 0
    while not app.need_exit() and frame_count < 50:
        time.fps_start()
        
        img = cam.read()
        faces = detector.detect(img, conf_th=0.4, iou_th=0.45)
        
        # Draw face detections with landmarks
        for face in faces:
            img.draw_rect(face.x, face.y, face.w, face.h, color=image.COLOR_RED)
            radius = math.ceil(face.w / 10)
            img.draw_keypoints(face.points, image.COLOR_RED, size=radius if radius < 5 else 4)
            
            print(f"Face detected: conf={face.score:.2f} at ({face.x}, {face.y}, {face.w}, {face.h})")
            print(f"Landmarks: {len(face.points)} points")
        
        disp.show(img)
        fps = time.fps()
        print(f"Frame {frame_count}: FPS: {fps:.1f}, Faces: {len(faces)}")
        
        frame_count += 1
    
    print("✅ Face Detection test completed")

def test_pose_detection():
    """Test human pose detection based on MaixPy example"""
    print("🧍 Testing Pose Detection...")
    
    # Initialize pose detector
    detector = nn.YOLOv8(model="/root/models/yolov8n_pose.mud", dual_buff=True)
    
    cam = camera.Camera(detector.input_width(), detector.input_height(), detector.input_format())
    disp = display.Display()
    
    print(f"Pose detector: {detector.input_width()}x{detector.input_height()}")
    
    frame_count = 0
    while not app.need_exit() and frame_count < 50:
        time.fps_start()
        
        img = cam.read()
        poses = detector.detect(img, conf_th=0.5, iou_th=0.45, keypoint_th=0.5)
        
        # Draw pose detections
        for pose in poses:
            img.draw_rect(pose.x, pose.y, pose.w, pose.h, color=image.COLOR_RED)
            msg = f'{detector.labels[pose.class_id]}: {pose.score:.2f}'
            img.draw_string(pose.x, pose.y, msg, color=image.COLOR_RED)
            
            # Draw pose skeleton
            detector.draw_pose(img, pose.points, 8 if detector.input_width() > 480 else 4, image.COLOR_RED)
            
            print(f"Pose detected: {detector.labels[pose.class_id]} ({pose.score:.2f})")
            print(f"Keypoints: {len(pose.points)} points")
        
        disp.show(img)
        fps = time.fps()
        print(f"Frame {frame_count}: FPS: {fps:.1f}, Poses: {len(poses)}")
        
        frame_count += 1
    
    print("✅ Pose Detection test completed")

def test_ocr():
    """Test OCR text recognition based on MaixPy example"""
    print("📝 Testing OCR...")
    
    # Initialize OCR model
    model = "/root/models/pp_ocr.mud"
    ocr = nn.PP_OCR(model)
    
    cam = camera.Camera(ocr.input_width(), ocr.input_height(), ocr.input_format())
    disp = display.Display()
    
    # Load font for text display
    try:
        image.load_font("ppocr", "/maixapp/share/font/ppocr_keys_v1.ttf", size=20)
        image.set_default_font("ppocr")
        print("Font loaded successfully")
    except Exception as e:
        print(f"Warning: Could not load font: {e}")
    
    print(f"OCR model: {ocr.input_width()}x{ocr.input_height()}")
    
    frame_count = 0
    while not app.need_exit() and frame_count < 50:
        time.fps_start()
        
        img = cam.read()
        text_objs = ocr.detect(img)
        
        # Draw text detections
        for obj in text_objs:
            points = obj.box.to_list()
            img.draw_keypoints(points, image.COLOR_RED, 4, -1, 1)
            img.draw_string(obj.box.x4, obj.box.y4, obj.char_str(), image.COLOR_RED)
            
            print(f"Text detected: '{obj.char_str()}' at ({obj.box.x4}, {obj.box.y4})")
        
        disp.show(img)
        fps = time.fps()
        print(f"Frame {frame_count}: FPS: {fps:.1f}, Texts: {len(text_objs)}")
        
        frame_count += 1
    
    print("✅ OCR test completed")

def run_all_tests():
    """Run all AI model tests"""
    print("🚀 Starting AI Models Test Suite")
    print("=" * 50)
    
    try:
        test_object_detection()
        print()
        
        test_face_detection()
        print()
        
        test_pose_detection()
        print()
        
        test_ocr()
        print()
        
        print("🎉 All AI model tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_camera_simple():
    """Simple camera test to verify basic functionality"""
    print("📷 Testing Basic Camera...")
    
    cam = camera.Camera(640, 480)
    disp = display.Display()
    
    frame_count = 0
    fps_history = []
    
    while not app.need_exit() and frame_count < 100:
        time.fps_start()
        
        img = cam.read()
        
        # Draw frame info
        img.draw_string(10, 10, f"Frame: {frame_count}", color=image.COLOR_WHITE)
        
        disp.show(img)
        fps = time.fps()
        fps_history.append(fps)
        
        if frame_count % 10 == 0:
            avg_fps = sum(fps_history[-10:]) / len(fps_history[-10:])
            print(f"Frame {frame_count}: FPS: {fps:.1f}, Avg: {avg_fps:.1f}")
        
        frame_count += 1
    
    avg_fps = sum(fps_history) / len(fps_history)
    print(f"✅ Camera test completed. Average FPS: {avg_fps:.1f}")

if __name__ == "__main__":
    # Choose which test to run
    import sys
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if test_name == "camera":
            test_camera_simple()
        elif test_name == "object":
            test_object_detection()
        elif test_name == "face":
            test_face_detection()
        elif test_name == "pose":
            test_pose_detection()
        elif test_name == "ocr":
            test_ocr()
        else:
            print(f"Unknown test: {test_name}")
            print("Available tests: camera, object, face, pose, ocr")
    else:
        run_all_tests()
