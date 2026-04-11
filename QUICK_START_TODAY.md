# ⚡ QUICK START - Get Running in 10 Minutes

## 🎯 Goal: Test with mobile camera TODAY, then deploy to Raspberry Pi

---

## ✅ What You Need

1. Python 3.8+ installed
2. Mobile phone with camera
3. Same WiFi network for phone and PC
4. YOLO model file (best.pt)

---

## 🚀 3 Simple Steps

### STEP 1: Install (3 minutes)

```bash
cd ~/traffic_violation_detection
pip install -r backend_requirements.txt
```

### STEP 2: Test Mobile Camera (2 minutes)

Install "IP Webcam" app on Android, start server, then:

```bash
python test_mobile_camera.py --ip YOUR_PHONE_IP:8080
```

Example: `python test_mobile_camera.py --ip 192.168.1.100:8080`

### STEP 3: Run System (1 minute)

```bash
python run_with_mobile.py --ip YOUR_PHONE_IP:8080
```

---

## 🎉 That's It!

Access the API at: http://localhost:8000/docs

---

## 📱 Mobile Camera Options

### Option 1: IP Webcam (Easiest)
1. Install "IP Webcam" from Play Store
2. Open app, scroll down, click "Start server"
3. Note the IP address (e.g., 192.168.1.100:8080)
4. Run: `python test_mobile_camera.py --ip 192.168.1.100:8080`

### Option 2: DroidCam
1. Install DroidCam on phone and PC
2. Connect via WiFi or USB
3. Run: `python test_mobile_camera.py --source 1`

### Option 3: USB Connection
1. Connect phone via USB
2. Enable USB tethering
3. Run: `python test_mobile_camera.py --source 1`

---

## 🍓 Deploy to Raspberry Pi (5 minutes)

```bash
# Make script executable
chmod +x deploy_to_rpi.sh

# Deploy (replace with your RPi IP if needed)
./deploy_to_rpi.sh raspberrypi.local

# SSH into RPi
ssh pi@raspberrypi.local

# Start system
cd traffic_violation_detection
python backend/run_server.py --host 0.0.0.0 --port 8000
```

---

## ❓ FAQ

### Do I need API keys?
NO! System works completely without API keys. They're only for optional features:
- Gemini API: AI verification (optional)
- SendGrid API: Email alerts (optional)

### Where do I get the YOLO model?
You need a trained model file (best.pt). Place it in `model/checkpoints/best.pt`

### What if camera doesn't work?
Try different source numbers:
```bash
python test_mobile_camera.py --source 0  # Built-in webcam
python test_mobile_camera.py --source 1  # External camera
python test_mobile_camera.py --source 2  # USB camera
```

### How do I access from another device?
The API runs on `0.0.0.0:8000`, accessible from any device on your network:
- From phone: http://YOUR_PC_IP:8000/docs
- From RPi: http://YOUR_PC_IP:8000/docs

---

## 🔧 Troubleshooting

### "No module named X"
```bash
pip install -r backend_requirements.txt
```

### "Model not found"
```bash
# Make sure best.pt exists
mkdir -p model/checkpoints
# Copy your best.pt file there
```

### "Camera not found"
```bash
# Test camera first
python test_mobile_camera.py --source 0
```

### "Port 8000 already in use"
```bash
# Use different port
python run_with_mobile.py --port 8001
```

---

## 📊 System Status

✅ NO API keys required
✅ Works with mobile camera
✅ Works with webcam
✅ Works on Raspberry Pi
✅ Production ready

---

## 🎯 Commands Cheat Sheet

```bash
# Test camera
python test_mobile_camera.py --ip 192.168.1.100:8080

# Run with mobile camera
python run_with_mobile.py --ip 192.168.1.100:8080

# Run with webcam
python run_with_mobile.py --source 0

# Run headless (no display)
python run_with_mobile.py --no-display

# Deploy to RPi
./deploy_to_rpi.sh

# Check installation
python verify_installation.py
```

---

## 🚀 You're Ready!

Start now:
```bash
python test_mobile_camera.py --ip YOUR_PHONE_IP:8080
```

Then:
```bash
python run_with_mobile.py --ip YOUR_PHONE_IP:8080
```

Access API: http://localhost:8000/docs
