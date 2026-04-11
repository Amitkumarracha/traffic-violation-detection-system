# 🚀 PRODUCTION SETUP - Quick Start Guide

## Today's Goal: Test with Mobile Camera → Deploy to Raspberry Pi

---

## ⚡ STEP 1: Install Dependencies (5 minutes)

```bash
cd ~/traffic_violation_detection
pip install -r backend_requirements.txt
```

---

## ⚡ STEP 2: Create .env File (2 minutes)

```bash
# Copy example to .env
cp .env.example .env
```

Edit `.env` file with your settings:

```env
# REQUIRED: None! System works without API keys

# OPTIONAL (for enhanced features):
GEMINI_API_KEY=your_key_here          # AI verification (optional)
SENDGRID_API_KEY=your_key_here        # Email alerts (optional)
NOTIFICATION_EMAIL=your@email.com     # Where to send alerts

# Database (default SQLite works fine)
DATABASE_URL=sqlite:///./violations.db

# API Server
API_HOST=0.0.0.0
API_PORT=8000
```

---

## ⚡ STEP 3: Get YOLO Model (3 minutes)

You need a trained YOLO model. Choose ONE option:

### Option A: Use Pre-trained Model (Fastest)
```bash
# Place your best.pt file in:
mkdir -p model/checkpoints
# Copy best.pt to model/checkpoints/best.pt
```

### Option B: Download from Cloud
```bash
# If you have model in cloud storage
wget YOUR_MODEL_URL -O model/checkpoints/best.pt
```

### Option C: Train Your Own (Takes hours)
```bash
# Only if you have training data
python scripts/train.py
```

---

## ⚡ STEP 4: Test with Mobile Camera (5 minutes)

### Method 1: IP Webcam App (Recommended)

1. Install "IP Webcam" app on Android
2. Start server in app (note the IP address, e.g., http://192.168.1.100:8080)
3. Run:

```bash
python test_mobile_camera.py --ip 192.168.1.100:8080
```

### Method 2: DroidCam

1. Install DroidCam on mobile + PC
2. Connect via USB or WiFi
3. Run:

```bash
python test_mobile_camera.py --source 1
```

### Method 3: USB Connection

1. Connect phone via USB
2. Enable USB tethering
3. Run:

```bash
python test_mobile_camera.py --source 1
```

---

## ⚡ STEP 5: Run Full System (2 minutes)

```bash
# Start API server + detection pipeline
python backend/run_server.py --host 0.0.0.0 --port 8000
```

Access:
- API: http://localhost:8000/docs
- Health: http://localhost:8000/health

---

## ⚡ STEP 6: Deploy to Raspberry Pi (10 minutes)

### On Your PC:

```bash
# Package the project
tar -czf traffic_violation.tar.gz ~/traffic_violation_detection
```

### On Raspberry Pi:

```bash
# 1. Copy file to RPi (use SCP or USB)
scp traffic_violation.tar.gz pi@raspberrypi.local:~

# 2. SSH into RPi
ssh pi@raspberrypi.local

# 3. Extract
tar -xzf traffic_violation.tar.gz
cd traffic_violation_detection

# 4. Install dependencies
pip install -r backend_requirements.txt

# 5. Install RPi camera support (if using Pi Camera)
pip install picamera2

# 6. Run
python backend/run_server.py --host 0.0.0.0 --port 8000
```

---

## 📱 Mobile Camera Integration Scripts

I'll create helper scripts for you:

1. `test_mobile_camera.py` - Test mobile camera connection
2. `run_with_mobile.py` - Run full system with mobile camera
3. `deploy_to_rpi.sh` - Automated RPi deployment

---

## 🔧 Troubleshooting

### "No module named X"
```bash
pip install -r backend_requirements.txt
```

### "Model not found"
```bash
# Make sure best.pt is in model/checkpoints/
ls model/checkpoints/best.pt
```

### "Camera not found"
```bash
# Try different camera indices
python test_mobile_camera.py --source 0  # Built-in webcam
python test_mobile_camera.py --source 1  # External camera
python test_mobile_camera.py --source 2  # USB camera
```

### "Port already in use"
```bash
# Use different port
python backend/run_server.py --port 8001
```

---

## 🎯 What Works WITHOUT API Keys

✅ Vehicle detection
✅ Violation detection
✅ License plate detection
✅ Basic OCR
✅ Tracking
✅ Speed estimation
✅ Database storage
✅ API endpoints

## 🎯 What Needs API Keys

❌ AI verification (Gemini) - Optional enhancement
❌ Email notifications (SendGrid) - Optional alerts

---

## 📊 System Requirements

### Minimum:
- Python 3.8+
- 4GB RAM
- Webcam or mobile camera
- CPU (works without GPU)

### Recommended:
- Python 3.9+
- 8GB RAM
- NVIDIA GPU (faster)
- Raspberry Pi 4/5 (for edge deployment)

---

## 🚀 Quick Commands

```bash
# Test camera only
python test_mobile_camera.py

# Run API server
python backend/run_server.py

# Run with mobile camera
python run_with_mobile.py --ip 192.168.1.100:8080

# Check system status
python verify_installation.py

# Deploy to RPi
bash deploy_to_rpi.sh
```

---

## ✅ Production Checklist

- [ ] Dependencies installed
- [ ] .env file created
- [ ] YOLO model in place
- [ ] Mobile camera tested
- [ ] API server running
- [ ] Database initialized
- [ ] Raspberry Pi ready (if deploying)

---

## 🎉 You're Ready!

The system is production-ready and works WITHOUT any API keys. API keys are only for optional enhancements.

Start testing now:
```bash
python test_mobile_camera.py
```
