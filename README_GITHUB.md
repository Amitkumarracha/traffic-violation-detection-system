# 🚦 Traffic Violation Detection System - YOLO Training

Complete YOLO training environment for traffic violation detection, optimized for NVIDIA A4000 GPU.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-red)](https://pytorch.org/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-green)](https://github.com/ultralytics/ultralytics)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📊 Overview

This project provides a complete training pipeline for:
1. **Number Plate Character Recognition** - OCR for license plates (A-Z, 0-9)
2. **Traffic Violation Detection** - Multi-task detection (helmet, riding, traffic violations)

### Features
- ✅ **9 Datasets** (7,078 images total)
- ✅ **GPU Optimized** for NVIDIA A4000 (16GB VRAM)
- ✅ **Automatic Checkpointing** (saves every 10 epochs)
- ✅ **Early Stopping** (prevents overfitting)
- ✅ **Portable Setup** (laptop ↔ GPU station)
- ✅ **Complete Documentation**

---

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/Amitkumarracha/traffic-violation-detection-system.git
cd traffic-violation-detection-system
```

### 2. Setup Environment
```bash
setup_venv.bat          # Windows
# or
./setup_venv.sh         # Linux/Mac
```

### 3. Optimize Project
```bash
optimize_project.bat    # Merges datasets, cleans files
```

### 4. Start Training
```bash
train.bat              # Train number plate model (2-3 hours)
# or
train_violations_merged.bat  # Train violations model (8-12 hours)
```

---

## 📁 Project Structure

```
traffic-violation-detection-system/
├── config/                    # Training configurations
│   ├── training_config.yaml
│   └── training_config_violations_merged.yaml
├── datasets/                  # Training datasets (7,078 images)
│   ├── Number Plate Char.v2i.yolo26/
│   ├── Red Light Violation Detect dataset.v3i.yolo26/
│   ├── TVD.v11i.yolo26/
│   └── [6 more datasets]
├── scripts/                   # Training & utility scripts
│   ├── train_yolo.py
│   ├── validate_model.py
│   ├── plot_results.py
│   ├── optimize_project.py
│   ├── merge_datasets.py
│   └── check_setup.py
├── models/                    # Model storage
├── runs/                      # Training outputs (created during training)
├── checkpoints/               # Best models backup
├── requirements.txt           # Python dependencies
├── setup_venv.bat            # Environment setup
├── train.bat                 # Training launcher
└── README.md                 # This file
```

---

## 📊 Datasets

### Included Datasets (7,078 images total):

| Dataset | Images | Classes | Purpose |
|---------|--------|---------|---------|
| Number Plate Char | 429 | 42 | Character recognition (A-Z, 0-9) |
| Red Light Violation | 3,395 | 9 | Traffic light violations |
| TVD | 1,675 | 4 | Helmet, triple riding, mobile, wheeling |
| Wrong Way Driving | 600 | 2 | Wrong-side driving detection |
| Riding | 435 | 3 | Multi-rider detection |
| Violation | 282 | 7 | Helmet, seatbelt, mobile violations |
| Rider Helmet | 124 | 4 | Helmet detection |
| Traffic Management | 88 | 6 | General violations |
| Triple Ride Detection | 50 | 5 | Triple riding + helmet |

### After Optimization:
- **Number Plate Char**: 429 images, 42 classes
- **Violations Merged**: ~6,600 images, 25 classes (merged from 8 datasets)

---

## 🎯 Training Options

### Option 1: Number Plate Character Recognition
```bash
train.bat
```
- **Model**: YOLOv8n (nano - fast)
- **Dataset**: 429 images, 42 classes
- **Time**: 2-3 hours on A4000
- **Expected mAP**: 85-95%

### Option 2: Traffic Violations Detection
```bash
train_violations_merged.bat
```
- **Model**: YOLOv8m (medium - accurate)
- **Dataset**: ~6,600 images, 25 classes
- **Time**: 8-12 hours on A4000
- **Expected mAP**: 75-85%

---

## 💻 Requirements

### Hardware
- **GPU**: NVIDIA A4000 (16GB VRAM) or similar
- **RAM**: 16GB+ recommended
- **Storage**: 10GB+ free space

### Software
- **OS**: Windows 10/11, Linux, or macOS
- **Python**: 3.8 or higher
- **CUDA**: 11.8 (for GPU training)
- **Git**: For cloning repository

---

## 📦 Installation

### Windows
```bash
# 1. Clone repository
git clone https://github.com/Amitkumarracha/traffic-violation-detection-system.git
cd traffic-violation-detection-system

# 2. Setup environment
setup_venv.bat

# 3. Verify setup
check_setup.bat

# 4. Optimize project
optimize_project.bat

# 5. Start training
train.bat
```

### Linux/Mac
```bash
# 1. Clone repository
git clone https://github.com/Amitkumarracha/traffic-violation-detection-system.git
cd traffic-violation-detection-system

# 2. Setup environment
chmod +x setup_venv.sh
./setup_venv.sh

# 3. Activate environment
source venv/bin/activate

# 4. Optimize project
python scripts/optimize_project.py

# 5. Start training
python scripts/train_yolo.py
```

---

## 🔧 Configuration

### Training Parameters

Edit `config/training_config.yaml` or `config/training_config_violations_merged.yaml`:

```yaml
# Model
model: yolov8n.pt  # Options: yolov8n, yolov8s, yolov8m, yolov8l, yolov8x

# Training
epochs: 100
batch: 16
imgsz: 640
device: 0  # GPU device (0 for first GPU, cpu for CPU)

# Optimization
optimizer: AdamW
lr0: 0.01
```

### GPU Memory Optimization

If you encounter out-of-memory errors:
1. Reduce `batch` size (try 8 or 4)
2. Use smaller model (`yolov8n.pt`)
3. Reduce `imgsz` (try 416 or 320)

---

## 📈 Training Progress

### Monitor Training
- Console shows: epoch, loss, mAP, precision, recall
- Plots saved in: `runs/train/[name]/results.png`
- Checkpoints saved every 10 epochs

### Resume Training
```bash
python scripts/train_yolo.py --resume runs/train/[name]/weights/last.pt
```

### Validate Model
```bash
python scripts/validate_model.py --model runs/train/[name]/weights/best.pt
```

---

## 📊 Results

### Expected Performance

| Model | mAP@0.5 | Training Time | Use Case |
|-------|---------|---------------|----------|
| Number Plate | 85-95% | 2-3 hours | License plate OCR |
| Violations | 75-85% | 8-12 hours | Violation detection |

### Output Files
```
runs/train/[name]/
├── weights/
│   ├── best.pt          # Best model checkpoint
│   ├── last.pt          # Latest checkpoint
│   └── epoch_*.pt       # Periodic checkpoints
├── results.png          # Training curves
├── confusion_matrix.png
├── F1_curve.png
├── P_curve.png
├── R_curve.png
└── results.csv          # Raw metrics
```

---

## 🚀 Deployment

### Export to ONNX
```bash
python -c "from ultralytics import YOLO; YOLO('runs/train/[name]/weights/best.pt').export(format='onnx')"
```

### Export to TensorRT
```bash
python -c "from ultralytics import YOLO; YOLO('runs/train/[name]/weights/best.pt').export(format='engine')"
```

---

## 📚 Documentation

- **PASTE_IN_TERMINAL.txt** - Quick copy-paste commands
- **GPU_SYSTEM_COMMANDS.txt** - Detailed GPU training guide
- **COMMANDS.md** - All commands reference
- **START_HERE.md** - Complete setup guide
- **QUICK_START.md** - 3-step quick start
- **PROJECT_STATUS.txt** - Project verification status

---

## 🔄 Workflow

```
Setup → Optimize → Train → Validate → Deploy
  ↓         ↓         ↓         ↓         ↓
10min     5min    2-12hrs   1-2min   Ready!
```

---

## 🆘 Troubleshooting

### GPU Not Detected
```bash
# Check CUDA installation
nvidia-smi

# Reinstall PyTorch with CUDA
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Out of Memory
- Reduce batch size in config
- Use smaller model (yolov8n.pt)
- Reduce image size

### Training Interrupted
```bash
# Resume from last checkpoint
python scripts/train_yolo.py --resume runs/train/[name]/weights/last.pt
```

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [Roboflow](https://roboflow.com/) for datasets
- NVIDIA for GPU optimization

---

## 📞 Contact

- **Author**: Amit Kumar Racha
- **GitHub**: [@Amitkumarracha](https://github.com/Amitkumarracha)
- **Repository**: [traffic-violation-detection-system](https://github.com/Amitkumarracha/traffic-violation-detection-system)

---

## ⭐ Star This Repository

If you find this project helpful, please give it a star! ⭐

---

**Ready to train? Run: `setup_venv.bat && optimize_project.bat && train.bat`**
