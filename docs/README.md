# 📚 Documentation

Complete knowledge base for the Traffic Violation Detection system organized by topic.

## 📁 Documentation Structure

```
docs/
├── api/                           REST API Documentation
│   ├── API_GUIDE.md              Complete API reference
│   ├── FASTAPI_BACKEND_SUMMARY.md FastAPI architecture
│   └── API_REFERENCE.json         JSON schema
├── guides/                        Technical Deep Dives
│   ├── PIPELINE_GUIDE.md         4-thread pipeline architecture
│   ├── CAMERA_STREAM_GUIDE.md    Video capture and preprocessing
│   ├── DETECTOR_GUIDE.md         YOLO detection system
│   ├── TRACKER_GUIDE.md          DeepSort tracking implementation
│   ├── OCR_GUIDE.md              Plate recognition
│   ├── SRGAN_GUIDE.md            Image upscaling
│   ├── VIOLATION_GATE_GUIDE.md   Violation detection logic
│   ├── DATABASE_GUIDE.md         Data persistence layer
│   ├── SETUP_VERIFICATION.md     Environment setup verification
│   ├── ISSUE_RESOLUTION.md       Troubleshooting
│   └── CUDA_YOLO_DIAGNOSIS.md    GPU and YOLO diagnostics
├── architecture/                  System Design
│   ├── ARCHITECTURE.md           High-level system design
│   ├── PHASE7_OVERVIEW.txt       Development phase notes
│   └── COMPONENT_INTERACTION.md  Component relationships
└── README.md (this file)
```

---

## 🎯 Documentation by Role

### 👨‍💼 Project Manager

**Want to understand the system?**

1. Start: [docs/architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)
2. Then: [docs/guides/PIPELINE_GUIDE.md](guides/PIPELINE_GUIDE.md)
3. Reference: [docs/api/FASTAPI_BACKEND_SUMMARY.md](api/FASTAPI_BACKEND_SUMMARY.md)

**Summary**: 4-thread pipeline for real-time violation detection with REST API and WebSocket support.

---

### 👨‍💻 Backend Developer

**Want to add API endpoints?**

1. Start: [docs/api/API_GUIDE.md](api/API_GUIDE.md)
2. Reference: [docs/api/FASTAPI_BACKEND_SUMMARY.md](api/FASTAPI_BACKEND_SUMMARY.md)
3. Deep dive: [docs/guides/DATABASE_GUIDE.md](guides/DATABASE_GUIDE.md)

**Key endpoints:**
- POST `/api/violations/detect` - Submit detection
- GET `/api/violations` - Query violations
- WebSocket `/ws/stream` - Real-time updates

---

### 🔬 ML Engineer

**Want to improve model accuracy?**

1. Start: [docs/guides/DETECTOR_GUIDE.md](guides/DETECTOR_GUIDE.md)
2. Training: [../model_training/README.md](../model_training/README.md)
3. Optimization: [docs/guides/CUDA_YOLO_DIAGNOSIS.md](guides/CUDA_YOLO_DIAGNOSIS.md)

**Key models:**
- Detector: YOLOv8n or YOLOv5
- Tracker: DeepSort
- OCR: Custom EasyOCR
- Enhancement: SRGAN (4x upscaling)

---

### 🎮 Demo Developer

**Want to showcase the system?**

1. Start: [../examples/README.md](../examples/README.md)
2. Pipeline: [docs/guides/PIPELINE_GUIDE.md](guides/PIPELINE_GUIDE.md)
3. Camera setup: [docs/guides/CAMERA_STREAM_GUIDE.md](guides/CAMERA_STREAM_GUIDE.md)

**Demo scripts:**
- `examples/demos/demo_main_pipeline.py`
- `examples/demos/demo_camera_stream.py`
- `examples/demos/demo_ocr_pipeline.py`

---

### 🧪 QA Engineer

**Want to test everything?**

1. Start: [../tests/README.md](../tests/README.md)
2. Setup: [docs/guides/SETUP_VERIFICATION.md](guides/SETUP_VERIFICATION.md)
3. Troubleshoot: [docs/guides/ISSUE_RESOLUTION.md](guides/ISSUE_RESOLUTION.md)

**Testing framework:** pytest with 11 test files, 85% coverage

---

### 🆕 New Developer

**Getting started?**

1. **Day 1:**
   - Read: [docs/architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)
   - Run: `python examples/demos/demo_main_pipeline.py`
   - Explore: [docs/guides/PIPELINE_GUIDE.md](guides/PIPELINE_GUIDE.md)

2. **Day 2:**
   - Setup: [docs/guides/SETUP_VERIFICATION.md](guides/SETUP_VERIFICATION.md)
   - Tests: `pytest tests/ -v`
   - Read: [Model Training](../model_training/README.md)

3. **Day 3:**
   - Pick a component: [docs/guides/](guides/)
   - Read implementation: [backend/](../backend/)
   - Contribute: Choose a test or feature to enhance

---

## 📚 Documentation Sections

### 🔌 API Documentation

Located: `docs/api/`

| Document | Purpose | Audience |
|----------|---------|----------|
| [API_GUIDE.md](api/API_GUIDE.md) | Complete REST API reference | Backend devs, Integrators |
| [FASTAPI_BACKEND_SUMMARY.md](api/FASTAPI_BACKEND_SUMMARY.md) | Architecture & setup | Backend devs, DevOps |
| [API_REFERENCE.json](api/API_REFERENCE.json) | Machine-readable schema | Tools, Generators |

**Quick links:**
- 14+ REST endpoints documented
- WebSocket implementation
- Request/response examples
- Error handling
- Authentication flows

```bash
# View API docs
cat docs/api/API_GUIDE.md | less

# Start API server
python backend/run_server.py
# Visit: http://localhost:8000/docs
```

---

### 🎓 Technical Guides

Located: `docs/guides/`

#### Pipeline Architecture
- [PIPELINE_GUIDE.md](guides/PIPELINE_GUIDE.md) - 4-thread pipeline, queue management
- Components: Camera → Preprocess → Inference → Logging

#### Core Components
- [DETECTOR_GUIDE.md](guides/DETECTOR_GUIDE.md) - YOLO detection
- [TRACKER_GUIDE.md](guides/TRACKER_GUIDE.md) - DeepSort tracking
- [OCR_GUIDE.md](guides/OCR_GUIDE.md) - Plate text recognition
- [SRGAN_GUIDE.md](guides/SRGAN_GUIDE.md) - Image upscaling

#### Supporting Systems
- [CAMERA_STREAM_GUIDE.md](guides/CAMERA_STREAM_GUIDE.md) - Video capture
- [VIOLATION_GATE_GUIDE.md](guides/VIOLATION_GATE_GUIDE.md) - Violation logic
- [DATABASE_GUIDE.md](guides/DATABASE_GUIDE.md) - Data persistence

#### Operations & Troubleshooting
- [SETUP_VERIFICATION.md](guides/SETUP_VERIFICATION.md) - Installation checks
- [ISSUE_RESOLUTION.md](guides/ISSUE_RESOLUTION.md) - Common problems
- [CUDA_YOLO_DIAGNOSIS.md](guides/CUDA_YOLO_DIAGNOSIS.md) - GPU issues

---

### 🏗️ Architecture Documentation

Located: `docs/architecture/`

| Document | Coverage |
|----------|----------|
| [ARCHITECTURE.md](architecture/ARCHITECTURE.md) | System overview, components, data flow |
| [PHASE7_OVERVIEW.txt](architecture/PHASE7_OVERVIEW.txt) | Development history, milestones |
| [COMPONENT_INTERACTION.md](architecture/COMPONENT_INTERACTION.md) | Component relationships, interfaces |

---

## 🔍 Quick Reference

### Find What You Need

| Need | Location | Start Reading |
|------|----------|---|
| Deploy API | docs/api/ | [FASTAPI_BACKEND_SUMMARY.md](api/FASTAPI_BACKEND_SUMMARY.md) |
| Improve detections | docs/guides/ | [DETECTOR_GUIDE.md](guides/DETECTOR_GUIDE.md) |
| Fix GPU issues | docs/guides/ | [CUDA_YOLO_DIAGNOSIS.md](guides/CUDA_YOLO_DIAGNOSIS.md) |
| Understand pipeline | docs/guides/ | [PIPELINE_GUIDE.md](guides/PIPELINE_GUIDE.md) |
| Setup new dev machine | docs/guides/ | [SETUP_VERIFICATION.md](guides/SETUP_VERIFICATION.md) |
| Solve a problem | docs/guides/ | [ISSUE_RESOLUTION.md](guides/ISSUE_RESOLUTION.md) |
| Check API details | docs/api/ | [API_GUIDE.md](api/API_GUIDE.md) |
| Understand system | docs/architecture/ | [ARCHITECTURE.md](architecture/ARCHITECTURE.md) |

---

## 📖 Reading Paths by Topic

### 🚀 Getting Started (First Time)

1. [docs/architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md) (15 min)
2. [docs/guides/PIPELINE_GUIDE.md](guides/PIPELINE_GUIDE.md) (20 min)
3. [../examples/README.md](../examples/README.md) (10 min)
4. Run demo: `python examples/demos/demo_main_pipeline.py` (5 min)

**Total: ~50 minutes to understand the system**

---

### 🔧 Setting Up (New Machine)

1. [docs/guides/SETUP_VERIFICATION.md](guides/SETUP_VERIFICATION.md) (20 min)
2. [docs/guides/CUDA_YOLO_DIAGNOSIS.md](guides/CUDA_YOLO_DIAGNOSIS.md) (15 min)
3. [../model_training/README.md](../model_training/README.md) (10 min)

**Total: ~45 minutes to get ready to code**

---

### 📡 Building API Features

1. [docs/api/API_GUIDE.md](api/API_GUIDE.md) (30 min)
2. [docs/guides/DATABASE_GUIDE.md](guides/DATABASE_GUIDE.md) (20 min)
3. [docs/api/FASTAPI_BACKEND_SUMMARY.md](api/FASTAPI_BACKEND_SUMMARY.md) (15 min)

**Total: ~60 minutes to understand API system**

---

### 🤖 Improving ML Models

1. [docs/guides/DETECTOR_GUIDE.md](guides/DETECTOR_GUIDE.md) (25 min)
2. [../model_training/README.md](../model_training/README.md) (30 min)
3. [docs/guides/CUDA_YOLO_DIAGNOSIS.md](guides/CUDA_YOLO_DIAGNOSIS.md) (15 min)

**Total: ~70 minutes to get ML context**

---

### 🐛 Fixing Issues

1. [docs/guides/ISSUE_RESOLUTION.md](guides/ISSUE_RESOLUTION.md) - Start here
2. [docs/guides/CUDA_YOLO_DIAGNOSIS.md](guides/CUDA_YOLO_DIAGNOSIS.md) - If GPU related
3. [../tests/README.md](../tests/README.md) - If test failures

---

## 📋 Document Index by Type

### Conceptual (Understanding)
- [docs/architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)
- [docs/guides/PIPELINE_GUIDE.md](guides/PIPELINE_GUIDE.md)
- [docs/architecture/COMPONENT_INTERACTION.md](architecture/COMPONENT_INTERACTION.md)

### Practical (Doing)
- [docs/guides/DETECTOR_GUIDE.md](guides/DETECTOR_GUIDE.md)
- [docs/guides/DATABASE_GUIDE.md](guides/DATABASE_GUIDE.md)
- [docs/api/API_GUIDE.md](api/API_GUIDE.md)

### Troubleshooting (Fixing)
- [docs/guides/ISSUE_RESOLUTION.md](guides/ISSUE_RESOLUTION.md)
- [docs/guides/CUDA_YOLO_DIAGNOSIS.md](guides/CUDA_YOLO_DIAGNOSIS.md)
- [docs/guides/SETUP_VERIFICATION.md](guides/SETUP_VERIFICATION.md)

---

## 🎯 Common Questions

### "Where do I start?"
→ Read [docs/architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)

### "How do I run the API?"
→ See [docs/api/FASTAPI_BACKEND_SUMMARY.md](api/FASTAPI_BACKEND_SUMMARY.md)

### "How does detection work?"
→ See [docs/guides/DETECTOR_GUIDE.md](guides/DETECTOR_GUIDE.md)

### "My GPU isn't working"
→ See [docs/guides/CUDA_YOLO_DIAGNOSIS.md](guides/CUDA_YOLO_DIAGNOSIS.md)

### "How do I train models?"
→ See [../model_training/README.md](../model_training/README.md)

### "What endpoints exist?"
→ See [docs/api/API_GUIDE.md](api/API_GUIDE.md)

### "How do I test my changes?"
→ See [../tests/README.md](../tests/README.md)

### "What are the components?"
→ See [docs/architecture/COMPONENT_INTERACTION.md](architecture/COMPONENT_INTERACTION.md)

---

## 📊 Documentation Statistics

| Category | Files | Pages | Est. Read Time |
|----------|-------|-------|-----------------|
| API | 3 | 25 | 60 min |
| Guides | 10 | 80 | 200 min |
| Architecture | 3 | 20 | 50 min |
| **Total** | **16** | **125** | **310 min** |

Read selectively based on your role - you don't need to read everything!

---

## 🔄 How Documentation is Organized

### By Topic (What You're Learning)
- What is the system? → `architecture/`
- How do I use it? → `guides/`
- How do I integrate with it? → `api/`

### By Audience (Who You Are)
- Project Manager → `architecture/` + `api/`
- Backend Dev → `api/` + `guides/database`
- ML Engineer → `guides/detector` + training docs
- New Developer → Start with `architecture/` + `guides/pipeline`

### By Problem (What You're Solving)
- Broken system → `guides/ISSUE_RESOLUTION.md`
- Slow models → `guides/DETECTOR_GUIDE.md`
- API confusion → `api/API_GUIDE.md`
- GPU problems → `guides/CUDA_YOLO_DIAGNOSIS.md`

---

## ✏️ Contributing Documentation

### Add a Guide
1. Create file: `docs/guides/TOPIC_GUIDE.md`
2. Follow template in existing guides
3. Update this README.md
4. Link from relevant sections

### Update Existing Docs
- Make changes directly
- Test all links still work
- Update table of contents

### Suggest Improvement
- Open an issue
- Describe missing content
- Submit PR with changes

---

## 🚀 Next Steps

### For First-Time Users
1. Read [docs/architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)
2. Run example: `python examples/demos/demo_main_pipeline.py`
3. Read [docs/guides/PIPELINE_GUIDE.md](guides/PIPELINE_GUIDE.md)

### For Developers
1. Complete setup: [docs/guides/SETUP_VERIFICATION.md](guides/SETUP_VERIFICATION.md)
2. Choose component to work on
3. Read component guide in `docs/guides/`
4. Check tests in `tests/`

### For DevOps/Infra
1. Read [docs/api/FASTAPI_BACKEND_SUMMARY.md](api/FASTAPI_BACKEND_SUMMARY.md)
2. Check deployment guides
3. Setup monitoring/logging

---

## 📞 Document Navigation Tips

- **Ctrl+F** to search within a document
- Look at **table of contents** at top of guides
- Follow **blue links** to related docs
- Check **examples/** for working code
- See **[../PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md)** for file locations

---

**Happy learning! 🎓**
