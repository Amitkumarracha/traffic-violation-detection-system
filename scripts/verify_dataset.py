#!/usr/bin/env python3
"""
Dataset integrity verification script
"""

from pathlib import Path
from collections import Counter
import os

BASE = Path.home() / "traffic_violation_detection" / "dataset"

for split in ['train', 'val']:
    imgs = list((BASE / 'images' / split).glob('*'))
    lbls = list((BASE / 'labels' / split).glob('*.txt'))
    
    # Check for missing labels
    img_stems = {i.stem for i in imgs}
    lbl_stems = {l.stem for l in lbls}
    
    missing_labels = img_stems - lbl_stems
    orphan_labels = lbl_stems - img_stems
    
    print(f"\n[{split.upper()}]")
    print(f"  Images: {len(imgs)}")
    print(f"  Labels: {len(lbls)}")
    print(f"  Missing labels: {len(missing_labels)}")
    print(f"  Orphan labels:  {len(orphan_labels)}")
    
    if missing_labels:
        print(f"  ⚠️ Sample missing: {list(missing_labels)[:5]}")

# Count class distribution
class_counts = Counter()
for lbl in (BASE / 'labels' / 'train').glob('*.txt'):
    with open(lbl) as f:
        for line in f:
            if line.strip():
                cls = int(line.split()[0])
                class_counts[cls] += 1

print(f"\n[CLASS DISTRIBUTION - TRAIN]")
classes = ["with_helmet","without_helmet","number_plate","riding","triple_ride","traffic_violation","motorcycle","vehicle"]
for cls_id, count in sorted(class_counts.items()):
    name = classes[cls_id] if cls_id < len(classes) else f"class_{cls_id}"
    print(f"  {cls_id}: {name:<25} {count:>6} instances")
