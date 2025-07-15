# MaixCAM Testing Instructions

## 🚀 Quick Testing on MaixCAM Device

### Option 1: Standalone Test Suite
**File:** `standalone_test.py`
**Purpose:** Comprehensive test of all MaixCAM features without dependencies

```python
# Upload and run standalone_test.py via MaixVision
# This will test:
# - Camera and display
# - AI object detection  
# - AI face detection
# - Touchscreen input
# - Model file availability
```

### Option 2: Simple Life Logger
**File:** `simple_main.py` 
**Purpose:** Basic life logging app that works without external modules

```python
# Upload and run simple_main.py via MaixVision
# Features:
# - Touch to start/stop capture
# - Real-time AI detection display
# - Object and face detection
# - Status display with FPS
```

### Option 3: Full Project (requires all files)
**Folder:** Upload entire `/src` folder structure
**File:** `main.py`
**Purpose:** Complete Companion Capture App

---

## 📋 Test Results Analysis

### Expected Test Results:

#### ✅ **Working Features** (Based on your test):
- MaixPy core modules ✅
- Camera initialization (640x480) ✅  
- Display output ✅
- Basic imports ✅

#### ❌ **Known Issues**:
- Missing utils modules when running full project
- Module import paths need adjustment

#### 🔍 **Need to Test**:
- AI model loading (`/root/models/*.mud` files)
- Touchscreen functionality
- Object detection accuracy
- Face detection accuracy

---

## 🎯 Recommended Testing Sequence

### Step 1: Basic Hardware Test
```bash
# Upload standalone_test.py and run
# Expected: Camera preview, FPS display, memory info
```

### Step 2: AI Models Test  
```bash
# Run standalone_test.py AI tests
# Expected: Object detection boxes, face detection with landmarks
```

### Step 3: Simple Life Logger
```bash
# Upload simple_main.py and run
# Expected: Touch interface, real-time AI detection
```

### Step 4: Full Project (if needed)
```bash
# Upload entire /src folder structure
# Run main.py
# Expected: Complete UI with model toggles
```

---

## 🔧 Troubleshooting

### Issue: "No module named 'utils'"
**Solution:** Use `standalone_test.py` or `simple_main.py` instead of `main.py`

### Issue: AI models not loading
**Check:** 
- Model files exist in `/root/models/`
- Model file extensions are `.mud`
- File permissions are correct

### Issue: Camera not working
**Check:**
- Camera initialization logs
- Resolution settings (640x480 is confirmed working)
- Camera format settings

### Issue: Low FPS
**Expected:** 15-25 FPS with AI processing
**Solutions:**
- Reduce processing intervals
- Use round-robin model scheduling
- Lower confidence thresholds

---

## 📊 Performance Expectations

Based on your test results:

| Feature | Expected Performance |
|---------|---------------------|
| Camera Preview | 25-30 FPS |
| Object Detection | 15-20 FPS |
| Face Detection | 20-25 FPS |
| Memory Usage | <200MB |
| Model Loading | 2-5 seconds |

---

## 🎮 Next Development Steps

1. **Test standalone_test.py** - Verify all hardware works
2. **Test simple_main.py** - Basic life logging functionality  
3. **Add audio processing** - Voice activity detection
4. **Optimize AI scheduling** - Better round-robin performance
5. **Add data logging** - JSON event storage
6. **Network integration** - WiFi upload capability

---

## 📁 File Summary

| File | Purpose | Dependencies |
|------|---------|-------------|
| `standalone_test.py` | Hardware & AI testing | None (self-contained) |
| `simple_main.py` | Basic life logger | None (self-contained) | 
| `main.py` | Full application | Requires utils/, ai_engine/, etc. |
| `ai_models_examples.py` | Individual model tests | None (self-contained) |

**Recommendation:** Start with `standalone_test.py` to verify everything works, then move to `simple_main.py` for actual life logging.
