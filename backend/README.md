# Backend Configuration Module

Complete platform auto-detection and settings management for Traffic Violation Detection system.

## Features

### 🖥️ Platform Auto-Detection (`platform_detector.py`)

Automatically detects the running platform and optimizes inference settings:

- **Raspberry Pi** — Lightweight edge inference
  - Image size: 320x320 (speed optimized)
  - Target FPS: 10
  - CPU threads: 4
  - Use case: Real-time camera feeds

- **Laptop CPU** — Balanced performance
  - Image size: 416x416 (balanced)
  - Target FPS: 30
  - CPU threads: 4
  - Use case: Development and testing

- **Desktop GPU** — High-performance inference
  - Image size: 640x640 (accuracy optimized)
  - Target FPS: 60
  - CPU threads: 8
  - Use case: Training and batch processing

### ⚙️ Requirements Management (`settings.py`)

Loads configuration from environment variables with:

- **API Keys**
  - Google Gemini (AI analysis)
  - SendGrid (email notifications)

- **Database**
  - SQLite (default, zero setup)
  - PostgreSQL (production)
  - MySQL (alternative)

- **Cloud Integration**
  - Supabase (optional backup)

- **Application Settings**
  - Server configuration
  - Model settings
  - Notification preferences

---

## Installation

### Step 1: Install Dependencies

```bash
pip install -r backend_config_requirements.txt
```

This installs:
- `pydantic` — Settings validation
- `pydantic-settings` — Environment loading
- `python-dotenv` — .env file support
- `torch` (optional) — GPU detection
- `pyusb` (optional) — Coral TPU detection

### Step 2: Setup Environment Variables

```bash
# Copy example to actual .env
cp .env.example .env

# Edit .env with your values
nano .env
```

Example `.env`:
```bash
GEMINI_API_KEY=your_key_here
SENDGRID_API_KEY=your_key_here
DATABASE_URL=sqlite:///./violations.db
API_HOST=0.0.0.0
API_PORT=8000
```

### Step 3: Add to .gitignore

```bash
echo ".env" >> .gitignore
```

---

## Usage

### Platform Detection

```python
from backend.config import get_platform_config

# Auto-detect platform and get optimized config
config = get_platform_config()

print(f"Platform: {config.platform}")
print(f"Inference size: {config.inference_size}x{config.inference_size}")
print(f"Target FPS: {config.max_fps_target}")
print(f"Confidence threshold: {config.confidence_threshold}")

# Use in inference engine
model = load_model(config.model_path)
results = model.infer(
    image,
    imgsz=config.inference_size,
    conf=config.confidence_threshold,
)
```

### Settings Management

```python
from backend.config import get_settings

# Get application settings (singleton pattern)
settings = get_settings()

# Database connection
db_url = settings.database_url

# API server
app.run(host=settings.api_host, port=settings.api_port)

# Model inference
model.conf_threshold = settings.model_confidence_threshold

# Notifications
if settings.alert_on_violation:
    send_email(settings.notification_email)
```

### Summary Printing

```python
from backend.config import (
    print_platform_summary,
    print_settings_summary,
)

# Print platform configuration
print_platform_summary()

# Print application settings
print_settings_summary()
```

---

## File Structure

```
backend/
├── __init__.py                 # Package initialization
├── config/
│   ├── __init__.py            # Config package exports
│   ├── platform_detector.py   # Platform auto-detection
│   └── settings.py            # Environment settings loader
└── requirements.txt           # Dependencies
```

---

## Platform Detection Logic

### Raspberry Pi Detection

```python
def is_raspberry_pi() -> bool:
    # Check /proc/device-tree/model for "Raspberry Pi"
    if Path("/proc/device-tree/model").exists():
        with open("/proc/device-tree/model", "rb") as f:
            return "Raspberry Pi" in f.read().decode()
    return False
```

### GPU Detection

```python
def is_desktop_gpu_available() -> bool:
    # Check torch.cuda.is_available()
    import torch
    return torch.cuda.is_available()
```

### Coral TPU Detection

```python
def detect_coral_usb_tpu() -> bool:
    # Check for Coral USB TPU via USB vendor/product IDs
    import usb.core
    device = usb.core.find(idVendor=0x1a6e, idProduct=0x089a)
    return device is not None
```

---

## PlatformConfig Dataclass

```python
@dataclass
class PlatformConfig:
    platform: str              # 'raspberry_pi' | 'laptop_cpu' | 'desktop_gpu'
    inference_size: int        # 320 | 416 | 640
    num_threads: int           # 4 | 4 | 8
    use_coral: bool            # Coral TPU available
    max_fps_target: int        # 10 | 30 | 60
    confidence_threshold: float # 0.75 (always)
    model_path: str            # Path to ONNX model
    device_name: str           # Human-readable name
```

---

## Settings Fields

```python
class Settings(BaseSettings):
    # API Keys
    gemini_api_key: Optional[str]
    sendgrid_api_key: Optional[str]
    
    # Database
    database_url: str = "sqlite:///./violations.db"
    
    # Cloud (Optional)
    supabase_url: Optional[str]
    supabase_key: Optional[str]
    
    # Application
    app_name: str = "Traffic Violation Detection"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Model
    model_confidence_threshold: float = 0.75
    max_violations_to_store: int = 10000
    
    # Notifications
    notification_email: Optional[str]
    alert_on_violation: bool = True
```

---

## Testing

Run the test script to verify configuration:

```bash
cd ~/traffic_violation_detection
source tvd_env/bin/activate
python test_config.py
```

Expected output:
```
Platform Detection: ✅ PASS
Settings Loading: ✅ PASS
Singleton Pattern: ✅ PASS
```

---

## Common Issues

### Issue: `ModuleNotFoundError: No module named 'pydantic_settings'`

**Solution:** Install with `pip install pydantic-settings`

```bash
pip install -r backend_config_requirements.txt
```

### Issue: Platform detected as "laptop_cpu" instead of GPU

**Solution:** Ensure PyTorch is installed with CUDA support

```bash
# For CUDA 11.8
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Verify
python -c "import torch; print(torch.cuda.is_available())"
```

### Issue: Settings not loading from .env file

**Solution:** Ensure .env is in project root and file exists

```bash
# Check .env location
ls -la .env

# Verify contents
cat .env | grep -i gemini
```

### Issue: Coral TPU not detected

**Solution:** Install pyusb and check USB connection

```bash
pip install pyusb

# Check connected devices
lsusb | grep -i coral
```

---

## Best Practices

✅ **Do:**
- Copy `.env.example` to `.env` for first setup
- Add `.env` to `.gitignore` before committing
- Use environment-specific .env files for different deployments
- Call `get_settings()` once at app startup
- Use `validate_settings()` during initialization

❌ **Don't:**
- Commit `.env` to version control
- Hardcode API keys or credentials
- Change settings at runtime (use dataclass instead)
- Call `get_settings()` repeatedly in tight loops

---

## Integration Examples

### FastAPI Integration

```python
from fastapi import FastAPI
from backend.config import get_settings, get_platform_config

app = FastAPI()
settings = get_settings()
platform_config = get_platform_config()

@app.on_event("startup")
async def startup():
    print(f"Running on: {platform_config.device_name}")
    print(f"API: {settings.api_host}:{settings.api_port}")

@app.get("/health")
def health():
    return {
        "platform": platform_config.platform,
        "database": settings.database_url,
    }
```

### Model Inference Integration

```python
from backend.config import get_platform_config
from ultralytics import YOLO

config = get_platform_config()
model = YOLO(config.model_path)

def detect_violations(image):
    results = model(
        image,
        imgsz=config.inference_size,
        conf=config.confidence_threshold,
        verbose=False,
    )
    return results[0].boxes
```

### Database Integration

```python
from backend.config import get_settings
from sqlalchemy import create_engine

settings = get_settings()
engine = create_engine(settings.database_url)

with engine.connect() as conn:
    # Execute queries
    pass
```

---

## Environment-Specific Configurations

### Development

```bash
# .env.dev
DEBUG=true
DATABASE_URL=sqlite:///./violations.db
API_PORT=8000
ALERT_ON_VIOLATION=false
```

### Production

```bash
# .env.prod
DEBUG=false
DATABASE_URL=postgresql://user:pass@prod-db:5432/violations
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=***
ALERT_ON_VIOLATION=true
```

Load with:
```bash
# Using environment
export ENV=prod
python app.py

# Or manually
cp .env.prod .env
python app.py
```

---

## Support & Troubleshooting

For issues, check:
1. `test_config.py` output for diagnostics
2. `.env` file exists and is readable
3. All required dependencies installed
4. No tilde expansions needed (`~` auto-expanded by code)

---

## Next Steps

After configuration is working:

1. **Create Data Models** — Database schema
2. **Build API Server** — FastAPI/Flask
3. **Implement Inference Engine** — Model loading and prediction
4. **Setup Monitoring** — Logging and alerts
5. **Deploy to RPi** — Edge deployment

---

## License

Part of Traffic Violation Detection System
