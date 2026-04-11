# Traffic Violation Detection - Complete Deployment Guide

## 🚀 Quick Start (5 Minutes)

### 1. Install Dependencies

```bash
cd ~/traffic_violation_detection
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy and edit .env file
cp .env.example .env
# Edit .env and add your API keys (optional)
```

### 3. Export Model (if not already done)

```bash
python scripts/export_model.py
```

### 4. Run System

```bash
# Test with webcam
python run.py

# Or start API server
python run.py --mode api

# Or run both
python run.py --mode full
```

---

## 📋 Complete Installation

### Prerequisites

- Python 3.8+
- Webcam or video file for testing
- (Optional) NVIDIA GPU for faster inference
- (Optional) Raspberry Pi 4/5 for edge deployment

### Step 1: Clone and Setup

```bash
cd ~/traffic_violation_detection
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
# Core dependencies
pip install --upgrade pip
pip install -r requirements.txt

# For GPU support (optional)
pip install onnxruntime-gpu

# For Raspberry Pi (on RPi only)
pip install gpsd-py3
sudo apt install python3-picamera2
```

### Step 3: Configure API Keys

Edit `.env` file:

```bash
# Google Gemini (for LLM verification)
GEMINI_API_KEY=your_key_here

# SendGrid (for email notifications)
SENDGRID_API_KEY=your_key_here

# Database (default SQLite, or use PostgreSQL)
DATABASE_URL=sqlite:///./violations.db
```

### Step 4: Export Model

```bash
# Export to ONNX (if not already done)
python scripts/export_model.py

# For Raspberry Pi, also quantize to INT8
python scripts/quantize_for_rpi.py
```

---

## 🎯 Usage Modes

### Mode 1: Real-Time Detection Pipeline

```bash
# Webcam
python run.py

# External camera
python run.py --source 1

# Video file
python run.py --source traffic_video.mp4

# Headless (no display)
python run.py --no-display
```

### Mode 2: API Server Only

```bash
python run.py --mode api --port 8000
```

Then open: http://localhost:8000/docs

### Mode 3: Full System (Pipeline + API)

```bash
python run.py --mode full
```

### Mode 4: Test Mode (Detector Only)

```bash
python run.py --mode test --source 0
```

### Mode 5: Benchmark

```bash
python run.py --benchmark
```

---

## 🔧 Platform-Specific Setup

### Windows (Laptop/Desktop)

```powershell
# Install dependencies
pip install -r requirements.txt

# Run with webcam
python run.py

# Or with video file
python run.py --source D:\videos\traffic.mp4
```

### Linux (Desktop/Server)

```bash
# Install dependencies
pip install -r requirements.txt

# For GPU support
pip install onnxruntime-gpu

# Run
python run.py
```

### Raspberry Pi 4/5

```bash
# Install system dependencies
sudo apt update
sudo apt install python3-pip python3-venv
sudo apt install python3-picamera2
sudo apt install gpsd gpsd-clients

# Install Python dependencies
pip install -r requirements.txt

# Quantize model for better performance
python scripts/quantize_for_rpi.py

# Run headless
python run.py --no-display
```

---

## 📊 API Endpoints

### Violations

```bash
# Get all violations
GET /api/violations?skip=0&limit=100

# Get single violation
GET /api/violations/{id}

# Get violation statistics
GET /api/violations/stats

# Get violation image
GET /api/violations/{id}/image

# Verify with LLM
POST /api/violations/{id}/verify
```

### Fraud Detection

```bash
# Check for fraud
POST /api/fraud/check
{
  "timestamp": "2026-04-08T10:30:00",
  "latitude": 18.5204,
  "longitude": 73.8567,
  "plate_number": "MH12AB1234",
  "claim_description": "Vehicle was parked"
}
```

### Health

```bash
# Health check
GET /api/health

# Database check
GET /api/health/db
```

### WebSocket (Live Stream)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/live');
ws.onmessage = (event) => {
  const violation = JSON.parse(event.data);
  console.log('New violation:', violation);
};
```

---

## 🎨 Web Dashboard (Optional)

### React Frontend

```bash
cd frontend
npm install
npm start
```

Then open: http://localhost:3000

---

## 🐳 Docker Deployment

### Laptop/Desktop (CPU)

```bash
docker build -f docker/Dockerfile.laptop -t tvd:laptop .
docker run -p 8000:8000 --device /dev/video0 tvd:laptop
```

### Desktop (GPU)

```bash
docker build -f docker/Dockerfile.gpu -t tvd:gpu .
docker run --gpus all -p 8000:8000 --device /dev/video0 tvd:gpu
```

### Docker Compose (Full Stack)

```bash
docker-compose up -d
```

---

## 🔍 Troubleshooting

### Model Not Found

```bash
# Export model first
python scripts/export_model.py

# Check exports folder
ls exports/
```

### Camera Not Working

```bash
# Test camera
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera FAIL')"

# Try different camera index
python run.py --source 1
```

### Low FPS on Raspberry Pi

```bash
# Quantize model to INT8
python scripts/quantize_for_rpi.py

# Use smaller input size
# Edit backend/config/platform_detector.py
# Change inference_size to 320 or 416
```

### API Key Errors

```bash
# Check .env file
cat .env

# Verify API keys are set
python -c "from backend.config.settings import get_settings; print(get_settings())"
```

### Database Errors

```bash
# Reset database
rm violations.db

# Or use PostgreSQL
# Edit .env:
# DATABASE_URL=postgresql://user:pass@localhost/violations_db
```

---

## 📈 Performance Optimization

### Laptop/Desktop

- Use GPU if available: `pip install onnxruntime-gpu`
- Increase threads in `platform_detector.py`
- Use larger input size (640px) for better accuracy

### Raspberry Pi

- Use INT8 quantized model
- Reduce input size to 320px or 416px
- Disable display: `--no-display`
- Use hardware acceleration if available

---

## 🔐 Security Best Practices

1. Never commit `.env` file to git
2. Use environment-specific secrets manager in production
3. Enable HTTPS for API in production
4. Restrict API access with authentication
5. Regularly update dependencies

---

## 📝 Logging

Logs are written to:
- Console (INFO level)
- `logs/violations.log` (all violations)
- `logs/errors.log` (errors only)

Configure logging in `backend/config/settings.py`

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/inference/test_detector.py -v

# Run with coverage
pytest --cov=backend tests/
```

---

## 📦 Production Deployment

### Cloud Platforms

#### Render

```bash
# Create render.yaml
# Deploy: git push
```

#### Railway

```bash
railway init
railway up
```

#### AWS/GCP/Azure

Use Docker containers with provided Dockerfiles

### Raspberry Pi (Edge)

```bash
# Install as systemd service
sudo cp deployment/tvd.service /etc/systemd/system/
sudo systemctl enable tvd
sudo systemctl start tvd

# Check status
sudo systemctl status tvd
```

---

## 🆘 Support

- Documentation: `docs/`
- Issues: Check `docs/guides/ISSUE_RESOLUTION.md`
- Examples: `examples/`
- Tests: `tests/`

---

## 📄 License

See LICENSE file for details.

---

## 🎉 Success Checklist

- [ ] Dependencies installed
- [ ] .env configured
- [ ] Model exported to ONNX
- [ ] Webcam test works: `python run.py --mode test`
- [ ] Benchmark completed: `python run.py --benchmark`
- [ ] API server starts: `python run.py --mode api`
- [ ] Full pipeline runs: `python run.py`
- [ ] (Optional) Raspberry Pi deployment
- [ ] (Optional) Docker deployment
- [ ] (Optional) Web dashboard

---

**You're all set! 🚀**

Run `python run.py` to start detecting violations.
