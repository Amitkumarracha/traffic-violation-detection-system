#!/usr/bin/env python3
"""
AI Traffic Violation Detection - Dataset Merger
Merges 4 datasets with class remapping to unified labels
"""

import os, shutil, yaml, random, glob
from pathlib import Path
from collections import defaultdict
import cv2

# ==============================================
# CONFIGURATION — Edit paths to match yours
# ==============================================
BASE = Path.home() / "traffic_violation_detection"
RAW = BASE / "raw_datasets"

DATASETS = {
    "rider_helmet": {
        "path": RAW / "Rider_With_Helmet_Without_Helmet_Number_Plate",
        "splits": ["train", "val"],
        "classes": ["With Helmet", "Without Helmet", "Number Plate"]
    },
    "riding_v1": {
        "path": RAW / "Riding.v1i.yolo26",
        "splits": ["train", "valid"],
        "classes": ["riding"]
    },
    "traffic_violation": {
        "path": RAW / "Traffic_Violation_Detection_Dataset",
        "splits": ["images/train", "images/val"],
        "classes": []  # auto-read from yaml
    },
    "triple_ride": {
        "path": RAW / "Triple_Ride_Detection.v1i.yolo26",
        "splits": ["train", "valid", "test"],
        "classes": []  # auto-read from yaml
    },
}

# ==============================================
# UNIFIED CLASS MAP — Define all merged classes
# ==============================================
UNIFIED_CLASSES = [
    "with_helmet",          # 0
    "without_helmet",       # 1
    "number_plate",         # 2
    "riding",               # 3
    "triple_ride",          # 4
    "traffic_violation",    # 5
    "motorcycle",           # 6
    "vehicle",              # 7
]

OUT = BASE / "dataset"
MERGED_IMAGES_TRAIN = OUT / "images" / "train"
MERGED_IMAGES_VAL = OUT / "images" / "val"
MERGED_LABELS_TRAIN = OUT / "labels" / "train"
MERGED_LABELS_VAL = OUT / "labels" / "val"

for d in [MERGED_IMAGES_TRAIN, MERGED_IMAGES_VAL, MERGED_LABELS_TRAIN, MERGED_LABELS_VAL]:
    d.mkdir(parents=True, exist_ok=True)

def load_yaml_classes(dataset_path):
    """Load class names from YAML config"""
    for yf in ['data.yaml', 'coco128.yaml', 'dataset.yaml']:
        yp = dataset_path / yf
        if yp.exists():
            with open(yp) as f:
                d = yaml.safe_load(f)
            return d.get('names', [])
    return []

def remap_label(label_path, src_classes, dst_classes, class_map):
    """Remap class IDs in a label file to unified class IDs"""
    lines = []
    if not os.path.exists(label_path):
        return lines
    with open(label_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            old_id = int(parts[0])
            if old_id < len(src_classes):
                src_class = src_classes[old_id].lower().replace(' ', '_')
                if src_class in class_map:
                    new_id = class_map[src_class]
                    lines.append(f"{new_id} {' '.join(parts[1:])}")
    return lines

def process_dataset(ds_name, ds_config, split_type='train'):
    """Process a single dataset split"""
    path = ds_config['path']
    src_classes = ds_config['classes'] if ds_config['classes'] else load_yaml_classes(path)
    
    # Handle both dict and list formats for classes
    if isinstance(src_classes, dict):
        src_classes = [v for k, v in sorted(src_classes.items())]
    
    # Build class mapping from source classes to unified classes
    class_map = {}
    for i, cls in enumerate(src_classes):
        cls_normalized = cls.lower().replace(' ', '_')
        # Fuzzy match to unified classes
        for j, unified in enumerate(UNIFIED_CLASSES):
            if cls_normalized in unified or unified in cls_normalized:
                class_map[cls_normalized] = j
                break
        if cls_normalized not in class_map:
            # Try to find closest
            if 'helmet' in cls_normalized and 'without' in cls_normalized:
                class_map[cls_normalized] = 1
            elif 'helmet' in cls_normalized:
                class_map[cls_normalized] = 0
            elif 'plate' in cls_normalized or 'number' in cls_normalized:
                class_map[cls_normalized] = 2
            elif 'triple' in cls_normalized:
                class_map[cls_normalized] = 4
            elif 'riding' in cls_normalized or 'rider' in cls_normalized:
                class_map[cls_normalized] = 3
            elif 'violation' in cls_normalized:
                class_map[cls_normalized] = 5
            elif 'motor' in cls_normalized or 'bike' in cls_normalized:
                class_map[cls_normalized] = 6
            else:
                class_map[cls_normalized] = 7
    
    print(f"\n[{ds_name}] Class mapping: {class_map}")
    
    copied = 0
    skipped = 0
    
    for split in ds_config['splits']:
        # Find images - check multiple possible locations
        img_dir = None
        lbl_dir = None
        
        # Try to find image directory
        possible_img_dirs = [
            path / split / "images",
            path / "images" / split,
            path / split,
        ]
        
        for candidate in possible_img_dirs:
            if candidate.exists():
                # Check if it contains image files
                img_files = list(candidate.glob("*.jpg")) + list(candidate.glob("*.png")) + list(candidate.glob("*.jpeg"))
                if img_files:
                    img_dir = candidate
                    break
        
        # Try to find label directory - check parallel structure first
        if img_dir:
            possible_lbl_dirs = []
            
            # For parallel structure like images/train and labels/train
            if img_dir.parent.name == "images":
                possible_lbl_dirs.append(img_dir.parent.parent / "labels" / split)
            
            # For nested structure like train/images and train/labels
            if "images" in img_dir.parts:
                idx = list(img_dir.parts).index("images")
                lbl_candidate = Path(*img_dir.parts[:idx]) / "labels" / Path(*img_dir.parts[idx+1:])
                possible_lbl_dirs.append(lbl_candidate)
            
            # Standard locations
            possible_lbl_dirs.extend([
                path / split / "labels",
                path / "labels" / split,
                img_dir.parent / "labels",
            ])
            
            for candidate in possible_lbl_dirs:
                if candidate.exists():
                    lbl_files = list(candidate.glob("*.txt"))
                    if lbl_files:
                        lbl_dir = candidate
                        break
        
        if not img_dir:
            print(f"  ⚠️ No image dir found for {ds_name}/{split}")
            continue
        
        if not lbl_dir:
            print(f"  ⚠️ No label dir found for {ds_name}/{split}")
            continue
        
        # Determine output split
        is_val = any(v in split for v in ['val', 'valid', 'test'])
        out_img = MERGED_IMAGES_VAL if is_val else MERGED_IMAGES_TRAIN
        out_lbl = MERGED_LABELS_VAL if is_val else MERGED_LABELS_TRAIN
        
        for img_path in img_dir.glob('*'):
            if img_path.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.bmp']:
                continue
            
            # Create unique filename
            new_name = f"{ds_name}_{img_path.stem}{img_path.suffix}"
            
            # Copy image
            shutil.copy2(img_path, out_img / new_name)
            
            # Process label
            if lbl_dir:
                lbl_path = lbl_dir / (img_path.stem + '.txt')
                new_lines = remap_label(lbl_path, src_classes, UNIFIED_CLASSES, class_map)
                if new_lines:
                    with open(out_lbl / (Path(new_name).stem + '.txt'), 'w') as f:
                        f.write('\n'.join(new_lines))
                    copied += 1
                else:
                    # Write empty label (background image)
                    open(out_lbl / (Path(new_name).stem + '.txt'), 'w').close()
                    copied += 1
            else:
                skipped += 1
    
    print(f"  ✅ {ds_name}: {copied} images processed, {skipped} skipped")
    return copied

# ==============================================
# MAIN EXECUTION
# ==============================================
if __name__ == '__main__':
    total = 0
    for ds_name, ds_config in DATASETS.items():
        n = process_dataset(ds_name, ds_config)
        total += n
    
    # Count final dataset
    train_imgs = len(list(MERGED_IMAGES_TRAIN.glob('*')))
    val_imgs = len(list(MERGED_IMAGES_VAL.glob('*')))
    train_lbls = len(list(MERGED_LABELS_TRAIN.glob('*')))
    val_lbls = len(list(MERGED_LABELS_VAL.glob('*')))
    
    print(f"\n{'='*50}")
    print(f"MERGE COMPLETE")
    print(f"Train images: {train_imgs} | Train labels: {train_lbls}")
    print(f"Val images:   {val_imgs}  | Val labels:   {val_lbls}")
    print(f"Total:        {train_imgs + val_imgs}")
    print(f"{'='*50}")
    
    # Write unified data.yaml
    data_yaml = {
        'path': str(OUT),
        'train': 'images/train',
        'val': 'images/val',
        'nc': len(UNIFIED_CLASSES),
        'names': UNIFIED_CLASSES
    }
    with open(OUT / 'data.yaml', 'w') as f:
        yaml.dump(data_yaml, f, default_flow_style=False)
    print(f"✅ data.yaml written to {OUT / 'data.yaml'}")
