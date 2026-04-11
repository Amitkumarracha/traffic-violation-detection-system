#!/usr/bin/env python3
"""
Dataset inspection script - analyzes all 4 raw datasets
"""

import yaml
import os
from pathlib import Path

BASE = Path.home() / "traffic_violation_detection"
RAW = BASE / "raw_datasets"

datasets = {
    "Rider_Helmet": RAW / "Rider_With_Helmet_Without_Helmet_Number_Plate",
    "Riding_v1": RAW / "Riding.v1i.yolo26",
    "Traffic_Violation": RAW / "Traffic_Violation_Detection_Dataset",
    "Triple_Ride": RAW / "Triple_Ride_Detection.v1i.yolo26",
}

for name, path in datasets.items():
    print(f"\n{'='*40}")
    print(f"Dataset: {name}")
    print(f"Path: {path}")
    
    if not path.exists():
        print(f"⚠️ Dataset not found!")
        continue
    
    # Count files
    txt_files = list(path.rglob('*.txt'))
    img_files = list(path.rglob('*.jpg')) + list(path.rglob('*.png')) + list(path.rglob('*.jpeg'))
    
    print(f"Label files: {len(txt_files)}")
    print(f"Image files: {len(img_files)}")
    
    # Find and read YAML
    for yaml_file in ['data.yaml', 'coco128.yaml', 'dataset.yaml']:
        yaml_path = path / yaml_file
        if yaml_path.exists():
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
            print(f"\nYAML: {yaml_file}")
            print(f"Classes ({data.get('nc', 'N/A')}): {data.get('names', 'N/A')}")
            break
    
    # Check classes.txt
    classes_txt = path / 'classes.txt'
    if classes_txt.exists():
        with open(classes_txt) as f:
            print(f"classes.txt: {f.read().strip()}")
    
    print(f"{'='*40}")
