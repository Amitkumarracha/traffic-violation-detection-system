# 🚀 START HERE - Traffic Violation Detection

## ⚡ Get Running in 10 Minutes

This system is **production-ready** and works **WITHOUT any API keys**.

---

## 📋 What You Need

- ✅ Python 3.8+
- ✅ Mobile phone OR webcam
- ✅ YOLO model file (best.pt)
- ❌ NO API keys needed!

---

## 🎯 Quick Start (3 Commands)

```bash
# 1. Install dependencies
pip install -r backend_requirements.txt

# 2. Test camera
python test_mobile_camera.py --ip YOUR_PHONE_IP:8080

# 3. Run system
python run_with_mobile.py --ip YOUR_PHONE_IP:8080
```

**Done!** Access API at: http://localhost:8000/docs

---

## 📱 Mobile Camera Setup (2 minutes)

1. Install "IP Webcam" app on Android
2. Open app → Start server
3. Note IP address (e.g., 192.168.1.100:8080)
4. Use that IP in commands above

---

## 🍓 Raspberry Pi Deployment (5 minutes)

```bash
# Deploy
chmod +x deploy_to_rpi.sh
./deploy_to_rpi.sh

# SSH and run
ssh pi@raspberrypi.local
cd traffic_violation_detection
python backend/run_server.py --host 0.0.0.0
```

---

## 🔑 API Keys (Optional)

System works **completely without API keys**. Add them only for extras:

Edit `.env` file:
```env
GEMINI_API_KEY=your_key      # Optional: AI verification
SENDGRID_API_KEY=your_key    # Optional: Email alerts
```

---

## 📚 Documentation

- **QUICK_START_TODAY.md** ← Read this first (10 min guide)
- **PRODUCTION_SETUP.md** ← Detailed setup guide
- **.env** ← Configuration file (already created)

---

## 🎯 What Works Without API Keys

✅ Vehicle detection
✅ Violation detection  
✅ License plate OCR
✅ Tracking & speed estimation
✅ Database storage
✅ REST API
✅ Mobile camera support
✅ Raspberry Pi deployment

---

## 🔧 Troubleshooting

```bash
# Check installation
python verify_installation.py

# Test camera
python test_mobile_camera.py --source 0

# Different port
python run_with_mobile.py --port 8001
```

---

## 🚀 Commands

```bash
# Verify installation
python verify_installation.py

# Test mobile camera
python test_mobile_camera.py --ip 192.168.1.100:8080

# Test webcam
python test_mobile_camera.py --source 0

# Run with mobile camera
python run_with_mobile.py --ip 192.168.1.100:8080

# Run with webcam
python run_with_mobile.py --source 0

# Run headless (RPi)
python run_with_mobile.py --no-display

# Deploy to RPi
./deploy_to_rpi.sh
```

---

## ✅ You're Ready!

1. Install: `pip install -r backend_requirements.txt`
2. Test: `python test_mobile_camera.py`
3. Run: `python run_with_mobile.py`

**That's it!** 🎉

For detailed guide, see: **QUICK_START_TODAY.md**
