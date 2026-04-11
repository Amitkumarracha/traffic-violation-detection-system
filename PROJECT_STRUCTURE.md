# 📁 Project Structure - Traffic Violation Detection System

**Last Updated**: March 31, 2026  
**Status**: ✅ Organized for Easy Contribution

---

## 🎯 Quick Navigation

```
traffic_violation_detection/
│
├── 🚀 QUICK START
│   ├── README.md                    # Main project overview
│   ├── COMMANDS.md                  # Common commands
│   └── .env.example                 # Environment template
│
├── 🤖 model_training/               # MODEL TRAINING (All training-related files)
│   ├── datasets/                    # Raw datasets from various sources
│   ├── merged_dataset/              # Pre-processed merged training dataset
│   ├── models/                      # Trained model weights (.pt files)
│   ├── configs/                     # Training configuration files
│   ├── exports/                     # Exported models (ONNX, TensorFlow, etc.)
│   ├── scripts/                     # Training & dataset processing scripts
│   ├── docs/                        # Training documentation
│   ├── reports/                     # Training reports & metrics
│   ├── training.log                 # Training logs
│   └── README.md                    # Training setup & workflows
│
├── 🔍 inference/                    # INFERENCE & DETECTION (Core system)
│   ├── backend/                     # Core backend modules
│   │   ├── pipeline/                # Main 4-thread pipeline
│   │   ├── core/                    # Detection, tracking, OCR
│   │   ├── api/                     # FastAPI REST API
│   │   ├── database/                # Database layer (SQLite/PostgreSQL)
│   │   ├── config/                  # Configuration management
│   │   └── __init__.py
│   ├── scripts/                     # Utility & inference scripts
│   │   ├── check_environment.py    # System check
│   │   ├── rpi_inference_test.py   # Raspberry Pi testing
│   │   └── README.md
│   ├── output/                      # Inference output (temp)
│   └── README.md
│
├── 📚 examples/                     # EXAMPLES & DEMONSTRATIONS
│   ├── demos/                       # Interactive demo scripts
│   │   ├── demo_main_pipeline.py   # Main 4-thread pipeline demo
│   │   ├── demo_camera_stream.py   # Camera streaming demo
│   │   ├── demo_ocr.py             # OCR recognition demo
│   │   ├── demo_srgan.py           # Image upscaling demo
│   │   ├── demo_tracking.py        # Object tracking demo
│   │   ├── demo_webcam.py          # Webcam capture demo
│   │   └── README.md
│   ├── inference/                   # Inference examples
│   │   ├── example_api_client.py   # API client usage
│   │   ├── example_database.py     # Database operations
│   │   └── README.md
│   └── README.md
│
├── 🧪 tests/                       # TEST SUITE
│   ├── training/                    # Model training tests
│   │   └── test_augmentation.py
│   ├── inference/                   # Inference & core tests
│   │   ├── test_main_pipeline.py
│   │   ├── test_detector.py
│   │   ├── test_tracker.py
│   │   ├── test_ocr.py
│   │   ├── test_srgan.py
│   │   ├── test_violation_gate.py
│   │   ├── test_config.py
│   │   ├── test_camera_stream.py
│   │   └── README.md
│   ├── api/                         # API tests
│   │   └── test_api.py
│   ├── integration/                 # End-to-end tests
│   │   └── test_integrated.py
│   └── README.md
│
├── 📖 docs/                        # COMPREHENSIVE DOCUMENTATION
│   ├── api/                         # API documentation
│   │   ├── API_GUIDE.md            # REST API reference
│   │   ├── FASTAPI_BACKEND_SUMMARY.md
│   │   └── README_FASTAPI_API.md
│   ├── guides/                      # Technical guides
│   │   ├── MAIN_PIPELINE_GUIDE.md
│   │   ├── CAMERA_STREAM_GUIDE.md
│   │   ├── DETECTOR_GUIDE.md
│   │   ├── TRACKER_GUIDE.md
│   │   ├── OCR_GUIDE.md
│   │   ├── SRGAN_GUIDE.md
│   │   ├── VIOLATION_GATE_GUIDE.md
│   │   ├── DATABASE_GUIDE.md
│   │   ├── ISSUE_RESOLUTION.md
│   │   ├── SETUP_VERIFICATION.md
│   │   └── README.md
│   ├── architecture/                # Architecture & design
│   │   ├── ARCHITECTURE.md
│   │   └── PHASE7_OVERVIEW.txt
│   └── README.md
│
├── 📦 backend/                     # MAIN APPLICATION (Mirror of inference/backend)
│   ├── pipeline/                   # Reference: model_training/ for details
│   ├── core/
│   ├── api/
│   ├── database/
│   └── config/
│
├── 🔧 scripts/                     # UTILITY SCRIPTS
│   ├── check_environment.py
│   ├── rpi_inference_test.py
│   └── README.md
│
├── 📋 logs/                        # APPLICATION LOGS
│   ├── inference/                  # Runtime inference logs
│   └── training/                   # Training logs (also in model_training/)
│
├── 🎬 requirements.txt             # Main dependencies (inference)
├── backend_requirements.txt        # Backend-specific dependencies
├── backend_config_requirements.txt # Configuration dependencies
│
├── 🔨 setup.sh                     # Linux/Mac setup script
├── setup.bat                       # Windows setup script
│
└── PHASE7_OVERVIEW.txt             # Latest development phase
```

---

## 📂 Folder Structure by Use Case

### 👨‍💻 For Model Training & Data Preparation

**If you want to train or fine-tune models:**

```
model_training/
├── datasets/              👈 Add raw datasets here
├── merged_dataset/        👈 Pre-processed dataset
├── scripts/
│   ├── train.py          👈 START HERE
│   ├── merge_datasets.py
│   ├── inspect_datasets.py
│   └── verify_dataset.py
├── configs/
│   └── train_config.yaml  👈 Training parameters
├── models/
│   └── *.pt              👈 Model checkpoints
└── docs/
    ├── TRAINING_COMMANDS.md
    └── AUGMENTATION_QUICKSTART.md
```

**Quick Start Commands:**
```bash
cd model_training/
python scripts/train.py
python scripts/merge_datasets.py --help
python scripts/export_onnx.py --model weights.pt
```

---

### 🎥 For Inference & Detection

**If you want to run real-time detection:**

```
backend/
├── pipeline/
│   └── main_pipeline.py   👈 START HERE (4-thread pipeline)
├── core/
│   ├── detector.py        👈 YOLO detection
│   ├── tracker.py         👈 DeepSort tracking
│   ├── ocr.py             👈 Plate OCR
│   └── srgan.py           👈 Image upscaling
├── api/                   👈 FastAPI REST API
│   └── app.py
├── database/              👈 Store violations
│   ├── models.py
│   ├── connection.py
│   └── crud.py
└── config/

examples/
├── demos/
│   └── demo_main_pipeline.py  👈 START HERE
└── inference/
    ├── example_api_client.py
    └── example_database.py
```

**Quick Start:**
```bash
# Run pipeline (real-time detection)
python examples/demos/demo_main_pipeline.py

# Start API server
python backend/run_server.py
# Open: http://localhost:8000/docs

# Query violations
python examples/inference/example_api_client.py
```

---

### 🧪 For Testing & Validation

**If you want to run tests:**

```
tests/
├── training/
│   └── test_augmentation.py
├── inference/              👈 Most tests here
│   ├── test_main_pipeline.py
│   ├── test_detector.py
│   ├── test_tracker.py
│   ├── test_ocr.py
│   └── ...
├── api/
│   └── test_api.py
└── integration/
    └── test_integrated.py
```

**Quick Start:**
```bash
cd tests/
python -m pytest inference/test_detector.py -v
python -m pytest -v                    # Run all tests
```

---

### 📚 For Understanding the System

**Documentation by topic:**

```
docs/
├── api/                         REST API documentation
├── guides/                      Technical deep-dives
│   ├── MAIN_PIPELINE_GUIDE.md   How 4-thread pipeline works
│   ├── DETECTOR_GUIDE.md        YOLO detection details
│   ├── TRACKER_GUIDE.md         DeepSort tracking
│   ├── OCR_GUIDE.md             Plate recognition
│   └── ...
└── architecture/                System design & decisions
```

**Start with:** `docs/guides/MAIN_PIPELINE_GUIDE.md`

---

## 🎓 Getting Started by Role

### 🤖 Machine Learning Engineer (Training)

1. Read: `model_training/docs/TRAINING_COMMANDS.md`
2. Go to: `model_training/`
3. Run:
   ```bash
   cd model_training
   python scripts/train.py --config configs/train_config.yaml
   python scripts/evaluate.py --model models/best.pt
   python scripts/export_onnx.py --model models/best.pt
   ```
4. Check: `model_training/reports/` for results

---

### 🚀 Backend/Infrastructure Engineer (Inference)

1. Read: `docs/guides/MAIN_PIPELINE_GUIDE.md`
2. Go to: `backend/pipeline/`
3. Run:
   ```bash
   # Start API server
   python backend/run_server.py
   
   # Or run inference directly
   python examples/demos/demo_main_pipeline.py
   ```
4. API Docs: `http://localhost:8000/docs`

---

### 🔬 QA / Testing

1. Read: `tests/README.md`
2. Go to: `tests/`
3. Run:
   ```bash
   cd tests
   python -m pytest -v
   python -m pytest inference/ -v
   python -m pytest integration/ -v
   ```

---

### 📖 Data Scientist / Analyst

1. Read: `docs/guides/DATABASE_GUIDE.md`
2. Use: `examples/inference/example_database.py`
3. Query: API endpoints at `http://localhost:8000/docs`

---

## ✅ Project Checklist for New Contributors

- [ ] Read `README.md` for project overview
- [ ] Read `COMMANDS.md` for common commands  
- [ ] Clone/fork the repository
- [ ] Run `./setup.sh` or `setup.bat`
- [ ] Pick your role (Training/Inference/Testing)
- [ ] Read relevant documentation from `docs/`
- [ ] Run examples from `examples/`
- [ ] Read the test files in `tests/` for your area
- [ ] Make your changes
- [ ] Run tests: `python -m pytest tests/ -v`
- [ ] Create PR with clear description

---

## 🎯 Key Files by Purpose

### If you need to...

| Need | File |
|------|------|
| Train a model | `model_training/scripts/train.py` |
| Run detection | `backend/pipeline/main_pipeline.py` |
| Start API | `backend/run_server.py` |
| Query violations | `examples/inference/example_api_client.py` |
| Understand pipeline | `docs/guides/MAIN_PIPELINE_GUIDE.md` |
| Test detector | `tests/inference/test_detector.py` |
| Check database | `examples/inference/example_database.py` |
| Export model | `model_training/scripts/export_onnx.py` |
| See API docs | `http://localhost:8000/docs` |

---

## 📊 Folder Sizes & Purposes

| Folder | Purpose | Size | Frequency |
|--------|---------|------|-----------|
| `model_training/` | Training & datasets | Large (GB) | Development phase |
| `backend/` | Running inference | Medium | Always |
| `examples/` | Quick demos | Small | Learning & demos |
| `tests/` | Validation | Small-Medium | Testing |
| `docs/` | Documentation | Medium | Reference |
| `logs/` | Runtime logs | Grows | Runtime |

---

## 🔄 Common Workflows

### Workflow 1: Training a New Model
```
1. Prepare datasets → model_training/datasets/
2. Configure training → model_training/configs/train_config.yaml
3. Run training → python model_training/scripts/train.py
4. Export model → python model_training/scripts/export_onnx.py
5. Copy to inference → backend/core/models/
```

### Workflow 2: Running Detection
```
1. Check models → backend/core/models/ or model_training/models/
2. Start pipeline → python examples/demos/demo_main_pipeline.py
3. (or) Start API → python backend/run_server.py
4. Access → http://localhost:8000/docs
```

### Workflow 3: Contributing Code
```
1. Create branch → git checkout -b feature/your-feature
2. Make changes → add/modify files
3. Run tests → python -m pytest tests/ -v
4. Run examples → python examples/demos/demo_main_pipeline.py
5. Create PR → describe what changed and why
```

---

## 📞 Questions?

- 📖 Documentation: See `docs/` folder
- 🎬 Examples: See `examples/` folder  
- 🧪 Tests: See `tests/` for how things work
- 🐛 Issues: Check `docs/guides/ISSUE_RESOLUTION.md`

---

## ✨ Project Highlights

✅ **Clean separation** of training vs inference
✅ **Organized documentation** by topic
✅ **Comprehensive examples** for all use cases
✅ **Full test suite** for validation
✅ **Multiple entry points** (pipeline, API, CLI)
✅ **Real-time detection** with 4-thread architecture
✅ **Easy to extend** and contribute to

---

**Happy coding! 🚀**
