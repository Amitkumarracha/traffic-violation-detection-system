# 🚀 Quick Installation Guide

## Prerequisites

- Python 3.8+ (3.10 or 3.11 recommended)
- pip (Python package manager)
- 4GB+ RAM
- Webcam or video file for testing

## Installation Steps

### 1. Install Dependencies

```bash
cd ~/traffic_violation_detection
pip install -r requirements.txt
```

This will install all required packages:
- onnxruntime (YOLO inference)
- opencv-python (image processing)
- fastapi + uvicorn (API server)
- sqlalchemy (database)
- pydantic (configuration)
- deep-sort-realtime (tracking)
- paddleocr + paddlepaddle (OCR)
- google-generativeai (LLM - optional)
- sendgrid (email - optional)
- reportlab (PDF - optional)
- basicsr + realesrgan (SRGAN - optional)

### 2. Verify Installation

```bash
python verify_installation.py
```

You should see:
```
✅ INSTALLATION VERIFIED - System ready!
```

### 3. Configure (Optional)

Edit `.env` file to add API keys:

```bash
# Google Gemini (for LLM verification)
GEMINI_API_KEY=your_key_here

# SendGrid (for email notifications)
SENDGRID_API_KEY=your_key_here
```

### 4. Get a Model

**Option A: Train Your Own**

```bash
# Place datasets in raw_datasets/
python scripts/merge_datasets.py
python scripts/train.py
python scripts/export_model.py
```

**Option B: Use Pre-trained Model**

If you have a trained model (best.pt), place it in:
- `model/checkpoints/best.pt`

Then export:
```bash
python scripts/export_model.py
```

**Option C: Download Pre-trained (if available)**

```bash
# Download from your model repository
# Place in exports/ folder
```

### 5. Test the System

```bash
# Verify everything works
python run.py --benchmark

# Test with webcam
python run.py --mode test --source 0
```

### 6. Run!

```bash
# Real-time detection
python run.py

# Or start API server
python run.py --mode api

# Or both
python run.py --mode full
```

---

## Troubleshooting

### "No module named 'onnxruntime'"

```bash
pip install onnxruntime
```

### "No module named 'fastapi'"

```bash
pip install fastapi uvicorn
```

### "No model found"

```bash
# Export model first
python scripts/export_model.py

# Or place trained model in model/checkpoints/best.pt
```

### "Camera not found"

```bash
# Test camera
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'FAIL')"

# Try different camera index
python run.py --source 1
```

### Pydantic errors

```bash
pip install --upgrade pydantic pydantic-settings
```

---

## Platform-Specific Notes

### Windows

```powershell
# Use PowerShell
pip install -r requirements.txt
python run.py
```

### Linux

```bash
pip install -r requirements.txt
python run.py
```

### Raspberry Pi

```bash
# Install system dependencies first
sudo apt update
sudo apt install python3-pip python3-venv
sudo apt install python3-picamera2

# Install Python packages
pip install -r requirements.txt

# Quantize model for better performance
python scripts/quantize_for_rpi.py

# Run headless
python run.py --no-display
```

---

## What Gets Installed

### Core (Required)
- onnxruntime - ONNX model inference
- opencv-python - Image processing
- numpy - Numerical computing
- pydantic - Configuration management
- python-dotenv - Environment variables

### API (Required)
- fastapi - REST API framework
- uvicorn - ASGI server
- sqlalchemy - Database ORM
- python-multipart - File uploads

### Detection (Required)
- deep-sort-realtime - Multi-object tracking

### OCR (Required)
- paddleocr - License plate text extraction
- paddlepaddle - PaddleOCR backend

### Optional (Recommended)
- google-generativeai - Gemini LLM verification
- sendgrid - Email notifications
- reportlab - PDF report generation
- Pillow - Image processing for PDF
- basicsr - SRGAN super-resolution
- realesrgan - Real-ESRGAN model

### Training (Optional - only if training models)
- torch - PyTorch
- torchvision - PyTorch vision
- ultralytics - YOLO training
- albumentations - Data augmentation

---

## Minimal Installation (No Optional Features)

If you want to skip optional features:

```bash
# Install only core dependencies
pip install onnxruntime opencv-python numpy pydantic python-dotenv
pip install fastapi uvicorn sqlalchemy python-multipart
pip install deep-sort-realtime
pip install paddleocr paddlepaddle
```

This will work but without:
- LLM verification (Gemini)
- Email notifications (SendGrid)
- PDF reports (ReportLab)
- SRGAN enhancement (BasicSR)

---

## Verification Checklist

After installation, verify:

- [ ] `python verify_installation.py` shows "INSTALLATION VERIFIED"
- [ ] Model exists in `exports/` folder (or can be exported)
- [ ] `.env` file exists (copy from `.env.example` if needed)
- [ ] `python run.py --benchmark` runs without errors
- [ ] `python run.py --mode test` opens webcam and shows detections

---

## Next Steps

Once installed:

1. **Read SETUP_COMPLETE.md** - Complete system overview
2. **Read DEPLOYMENT_GUIDE.md** - Deployment instructions
3. **Run examples** - See `examples/` folder
4. **Check docs** - See `docs/` folder

---

## Getting Help

- Run `python verify_installation.py` to diagnose issues
- Check `docs/guides/ISSUE_RESOLUTION.md`
- See examples in `examples/` folder
- Check tests in `tests/` folder

---

**Installation time: ~5-10 minutes**

**Ready to detect violations! 🚗🚦**
