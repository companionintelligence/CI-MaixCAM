#!/usr/bin/env python3
"""
Standalone MaixCAM Test
Self-contained test that doesn't require external modules

This file tests the core functionality without dependencies on utils, ai_engine, etc.
Perfect for testing individual components on the MaixCAM device.

Author: Companion Intelligence
Date: July 14, 2025
"""

from maix import camera, display, image, nn, app, time, touchscreen
import gc
import math

def test_camera_and_display():
    """Test camera capture and display"""
    print("📷 Testing camera and display...")
    
    cam = camera.Camera(640, 480)
    disp = display.Display()
    
    print(f"Camera: {cam.width()}x{cam.height()}")
    print(f"Display: {disp.width()}x{disp.height()}")
    
    frame_count = 0
    fps_history = []
    
    print("🔴 Starting camera preview (10 seconds)...")
    start_time = time.ticks_ms()
    
    while not app.need_exit():
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, start_time) > 10000:  # 10 seconds
            break
            
        time.fps_start()
        
        img = cam.read()
        
        # Draw frame info
        img.draw_string(10, 10, f"Frame: {frame_count}", color=image.COLOR_WHITE)
        img.draw_string(10, 30, f"Time: {time.ticks_diff(current_time, start_time)}ms", color=image.COLOR_WHITE)
        
        disp.show(img)
        
        fps = time.fps()
        fps_history.append(fps)
        frame_count += 1
        
        if frame_count % 10 == 0:
            avg_fps = sum(fps_history[-10:]) / len(fps_history[-10:])
            print(f"Frame {frame_count}: FPS: {fps:.1f}, Avg: {avg_fps:.1f}")
    
    cam.close()
    avg_fps = sum(fps_history) / len(fps_history) if fps_history else 0
    print(f"✅ Camera test completed: {frame_count} frames, avg FPS: {avg_fps:.1f}")
    return True

def test_ai_object_detection():
    """Test YOLOv8 object detection"""
    print("\n🤖 Testing AI object detection...")
    
    try:
        # Try to load object detection model
        model_path = "/root/models/yolov8n.mud"
        detector = nn.YOLOv8(model=model_path, dual_buff=True)
        
        print(f"✅ Model loaded: {model_path}")
        print(f"Input size: {detector.input_width()}x{detector.input_height()}")
        print(f"Labels: {len(detector.labels)} classes")
        
        # Initialize camera with model's input size
        cam = camera.Camera(detector.input_width(), detector.input_height(), detector.input_format())
        disp = display.Display()
        
        frame_count = 0
        total_detections = 0
        
        print("🔍 Running object detection (10 seconds)...")
        start_time = time.ticks_ms()
        
        while not app.need_exit():
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, start_time) > 10000:  # 10 seconds
                break
                
            time.fps_start()
            
            img = cam.read()
            objs = detector.detect(img, conf_th=0.5, iou_th=0.45)
            
            # Draw detections
            for obj in objs:
                img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)
                label = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
                img.draw_string(obj.x, obj.y, label, color=image.COLOR_RED)
                total_detections += 1
            
            # Draw info
            img.draw_string(10, 10, f"Frame: {frame_count}", color=image.COLOR_WHITE)
            img.draw_string(10, 30, f"Objects: {len(objs)}", color=image.COLOR_WHITE)
            img.draw_string(10, 50, f"Total: {total_detections}", color=image.COLOR_WHITE)
            
            disp.show(img)
            
            fps = time.fps()
            frame_count += 1
            
            if len(objs) > 0:
                print(f"Frame {frame_count}: {len(objs)} objects detected")
        
        cam.close()
        print(f"✅ Object detection test completed: {total_detections} total detections in {frame_count} frames")
        return True
        
    except Exception as e:
        print(f"❌ Object detection test failed: {e}")
        return False

def test_ai_face_detection():
    """Test face detection"""
    print("\n👤 Testing face detection...")
    
    try:
        # Try to load face detection model
        model_path = "/root/models/retinaface.mud"
        detector = nn.Retinaface(model=model_path, dual_buff=True)
        
        print(f"✅ Face model loaded: {model_path}")
        print(f"Input size: {detector.input_width()}x{detector.input_height()}")
        
        # Initialize camera
        cam = camera.Camera(detector.input_width(), detector.input_height(), detector.input_format())
        disp = display.Display()
        
        frame_count = 0
        total_faces = 0
        
        print("👁️ Running face detection (10 seconds)...")
        start_time = time.ticks_ms()
        
        while not app.need_exit():
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, start_time) > 10000:  # 10 seconds
                break
                
            time.fps_start()
            
            img = cam.read()
            faces = detector.detect(img, conf_th=0.4, iou_th=0.45)
            
            # Draw face detections
            for face in faces:
                img.draw_rect(face.x, face.y, face.w, face.h, color=image.COLOR_GREEN)
                # Draw landmarks
                radius = max(2, face.w // 20)
                img.draw_keypoints(face.points, image.COLOR_GREEN, size=radius)
                total_faces += 1
            
            # Draw info
            img.draw_string(10, 10, f"Frame: {frame_count}", color=image.COLOR_WHITE)
            img.draw_string(10, 30, f"Faces: {len(faces)}", color=image.COLOR_WHITE)
            img.draw_string(10, 50, f"Total: {total_faces}", color=image.COLOR_WHITE)
            
            disp.show(img)
            
            fps = time.fps()
            frame_count += 1
            
            if len(faces) > 0:
                print(f"Frame {frame_count}: {len(faces)} faces detected")
        
        cam.close()
        print(f"✅ Face detection test completed: {total_faces} total faces in {frame_count} frames")
        return True
        
    except Exception as e:
        print(f"❌ Face detection test failed: {e}")
        return False

def test_touchscreen():
    """Test touchscreen input"""
    print("\n👆 Testing touchscreen...")
    
    try:
        touch = touchscreen.TouchScreen()
        disp = display.Display()
        
        print("Touch the screen to test (10 seconds)...")
        
        # Create test image
        img = image.Image(disp.width(), disp.height(), image.Format.FMT_RGB888)
        img.draw_rect(0, 0, img.width(), img.height(), color=image.COLOR_BLACK, thickness=-1)
        img.draw_string(50, 50, "Touch Screen Test", color=image.COLOR_WHITE)
        img.draw_string(50, 100, "Touch anywhere", color=image.COLOR_WHITE)
        
        touch_count = 0
        start_time = time.ticks_ms()
        
        while not app.need_exit():
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, start_time) > 10000:  # 10 seconds
                break
            
            touch_data = touch.read()
            
            if touch_data[0]:  # Touch detected
                x, y = touch_data[1], touch_data[2]
                touch_count += 1
                
                # Draw touch point
                img.draw_circle(x, y, 10, color=image.COLOR_RED, thickness=-1)
                img.draw_string(x+15, y, f"#{touch_count}", color=image.COLOR_RED)
                
                print(f"Touch {touch_count}: ({x}, {y})")
            
            # Update display
            remaining_time = 10 - time.ticks_diff(current_time, start_time) // 1000
            img.draw_rect(50, 150, 200, 30, color=image.COLOR_BLACK, thickness=-1)
            img.draw_string(50, 150, f"Time: {remaining_time}s", color=image.COLOR_WHITE)
            img.draw_string(50, 170, f"Touches: {touch_count}", color=image.COLOR_WHITE)
            
            disp.show(img)
            time.sleep_ms(50)
        
        print(f"✅ Touchscreen test completed: {touch_count} touches detected")
        return True
        
    except Exception as e:
        print(f"❌ Touchscreen test failed: {e}")
        return False

def check_model_files():
    """Check what AI model files are available"""
    print("\n📂 Checking AI model files...")
    
    import os
    
    model_dir = "/root/models"
    
    if not os.path.exists(model_dir):
        print(f"❌ Model directory not found: {model_dir}")
        return False
    
    try:
        files = os.listdir(model_dir)
        mud_files = [f for f in files if f.endswith('.mud')]
        
        print(f"📁 Found {len(mud_files)} .mud model files:")
        for file in mud_files:
            file_path = os.path.join(model_dir, file)
            file_size = os.path.getsize(file_path)
            print(f"   {file} ({file_size//1024//1024}MB)")
        
        return len(mud_files) > 0
        
    except Exception as e:
        print(f"❌ Error checking model files: {e}")
        return False

def main():
    """Run all standalone tests"""
    print("🚀 Standalone MaixCAM Test Suite")
    print("=" * 50)
    
    tests = [
        ("Model Files Check", check_model_files),
        ("Camera & Display", test_camera_and_display),
        ("AI Object Detection", test_ai_object_detection),
        ("AI Face Detection", test_ai_face_detection),
        ("Touchscreen", test_touchscreen),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n▶️ Running {test_name}...")
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"💥 {test_name} CRASHED: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! MaixCAM is working perfectly!")
    else:
        print("⚠️ Some tests failed. Check the results above.")

if __name__ == "__main__":
    main()
