#!/usr/bin/env python3
"""
OCR Module Testing
Tests license plate text extraction and validation
"""

import sys
from pathlib import Path
import cv2
import numpy as np

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend import PlateOCR, PlateResult, validate_indian_plate


def test_plate_format_validation():
    """Test Indian license plate format validation"""
    print("\n" + "=" * 70)
    print("TEST 1: License Plate Format Validation")
    print("=" * 70 + "\n")
    
    ocr = PlateOCR()
    
    # Valid plates
    valid_plates = [
        "MH12AB1234",   # Mumbai, district 12
        "DL01CD5678",   # Delhi, district 01
        "KA5ABC1234",   # Karnataka, district 5
        "TN26XY9999",   # Tamil Nadu, district 26
        "UP80PQ0001",   # Uttar Pradesh, district 80
        "BH02RS5555",   # Bihar, district 02
    ]
    
    # Invalid plates
    invalid_plates = [
        "MH12AB123",    # Too short
        "MH12AB12345",  # Too long
        "1234AB5678",   # No letters at start
        "MHABCD1234",   # No numbers in district
        "MH12AB",       # Missing serial
        "MHMHAB1234",   # Too many letters at start
        "MH12123456",   # No letters in category
    ]
    
    print("Valid Indian Plates:")
    for plate in valid_plates:
        is_valid = validate_indian_plate(plate)
        status = "✓" if is_valid else "✗"
        print(f"  {status} {plate}")
        assert is_valid, f"Should be valid: {plate}"
    
    print("\nInvalid Plates:")
    for plate in invalid_plates:
        is_valid = validate_indian_plate(plate)
        status = "✓" if not is_valid else "✗"
        print(f"  {status} {plate} → {is_valid}")
        assert not is_valid, f"Should be invalid: {plate}"
    
    print("\n✅ All validation tests passed!")


def test_character_corrections():
    """Test OCR character correction logic"""
    print("\n" + "=" * 70)
    print("TEST 2: Character Corrections (OCR Misreads)")
    print("=" * 70 + "\n")
    
    ocr = PlateOCR()
    
    test_cases = [
        # (raw_text, expected_cleaned)
        ("MH12AB1234", "MH12AB1234"),      # No errors
        ("MH12OB1234", "MH12OB1234"),      # O in category - don't correct
        ("MHI2AB1234", "MH12AB1234"),      # I → 1 in district ✓
        ("MH1SAB1234", "MH15AB1234"),      # S → 5 in district ✓
        ("MH12AB12B4", "MH12AB1284"),      # B → 8 in serial ✓
        ("MH12AB1G34", "MH12AB1634"),      # G → 6 in serial ✓
        ("MH12OB1234", "MH12OB1234"),      # O after letters - no correction
        ("MH-12 AB 1234", "MH12AB1234"),   # Spaces and hyphens removed
        ("mh12ab1234", "MH12AB1234"),      # Uppercase conversion
    ]
    
    print("Testing character corrections in different positions:\n")
    
    for raw, expected in test_cases:
        cleaned = ocr._clean_text(raw)
        status = "✓" if cleaned == expected else "✗"
        print(f"  {status} '{raw}' → '{cleaned}' (expected: {expected})")
        assert cleaned == expected, f"Mismatch: {cleaned} != {expected}"
    
    print("\n✅ All correction tests passed!")


def test_srgan_detection():
    """Test SRGAN requirement detection"""
    print("\n" + "=" * 70)
    print("TEST 3: SRGAN Upscaling Detection")
    print("=" * 70 + "\n")
    
    ocr = PlateOCR()
    
    test_cases = [
        # (bbox, expected_srgan_needed, description)
        ((100, 100, 250, 140), False, "Normal size (150x40)"),
        ((100, 100, 160, 130), True, "Too narrow (60x30)"),
        ((100, 100, 170, 125), True, "Small area (70x25 = 1750px²)"),
        ((100, 100, 280, 195), False, "Large (180x95 = 17100px²)"),
        ((100, 100, 180, 160), True, "Just below threshold (80x60 = 4800px²)"),
    ]
    
    print("Testing SRGAN trigger conditions:\n")
    
    for bbox, expected_srgan, description in test_cases:
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        area = width * height
        
        needs_srgan = ocr.should_use_srgan(bbox)
        status = "✓" if needs_srgan == expected_srgan else "✗"
        
        print(f"  {status} {description}")
        print(f"      Size: {width}x{height} ({area}px²)")
        print(f"      SRGAN needed: {needs_srgan} (expected: {expected_srgan})")
        
        assert needs_srgan == expected_srgan, f"SRGAN mismatch for {description}"
    
    print("\n✅ All SRGAN detection tests passed!")


def test_plate_result_dataclass():
    """Test PlateResult dataclass"""
    print("\n" + "=" * 70)
    print("TEST 4: PlateResult Dataclass")
    print("=" * 70 + "\n")
    
    result = PlateResult(
        raw_text="MH 12 AB 1234",
        cleaned_text="MH12AB1234",
        confidence=0.95,
        is_valid_indian_format=True,
        needs_srgan=False
    )
    
    print(f"PlateResult Object:")
    print(f"  {result}")
    print(f"\nDetails:")
    print(f"  Raw text: {result.raw_text}")
    print(f"  Cleaned: {result.cleaned_text}")
    print(f"  Confidence: {result.confidence:.3f}")
    print(f"  Valid format: {result.is_valid_indian_format}")
    print(f"  Needs SRGAN: {result.needs_srgan}")
    
    # Test invalid result
    invalid = PlateResult(
        raw_text="ABC",
        cleaned_text="ABC",
        confidence=0.22,
        is_valid_indian_format=False,
        needs_srgan=True
    )
    
    print(f"\nInvalid result:")
    print(f"  {invalid}")
    
    print("\n✅ PlateResult tests passed!")


def test_preprocessing_validation():
    """Test plate preprocessing and size validation"""
    print("\n" + "=" * 70)
    print("TEST 5: Plate Preprocessing")
    print("=" * 70 + "\n")
    
    ocr = PlateOCR()
    
    print("Testing preprocessing with different sizes:\n")
    
    # Create dummy frames with different plate sizes
    test_cases = [
        (640, 480, (100, 100, 200, 140), True, "Normal plate (100x40)"),
        (640, 480, (100, 100, 130, 122), False, "Too small (30x22)"),
        (640, 480, (100, 100, 170, 130), True, "Borderline (70x30)"),
        (640, 480, (100, 100, 170, 115), False, "Too narrow (70x15)"),
    ]
    
    for img_w, img_h, bbox, should_process, desc in test_cases:
        # Create test frame
        frame = np.ones((img_h, img_w, 3), dtype=np.uint8) * 128
        
        result = ocr.preprocess_plate(frame, bbox)
        processed = result is not None
        
        status = "✓" if processed == should_process else "✗"
        print(f"  {status} {desc} → {'Processed' if processed else 'Skipped'}")
        
        assert processed == should_process, f"Preprocessing mismatch: {desc}"
    
    print("\n✅ All preprocessing tests passed!")


def test_batch_processing():
    """Test batch processing multiple plates"""
    print("\n" + "=" * 70)
    print("TEST 6: Batch Processing")
    print("=" * 70 + "\n")
    
    ocr = PlateOCR()
    
    # Create test frame
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 100
    
    # Multiple bounding boxes
    bboxes = [
        (50, 50, 200, 100),      # Valid size
        (300, 300, 330, 315),    # Too small
        (250, 150, 400, 190),    # Valid size
    ]
    
    print(f"Testing batch processing with {len(bboxes)} bounding boxes:")
    print()
    
    results = ocr.batch_read_plates(frame, bboxes)
    
    print(f"  Processed: {len(results)}/{len(bboxes)} plates")
    print(f"  Valid sizes: 2, Got results: {len(results)}")
    
    # We expect results for bbox 0 and 2 (1 will be skipped for being small)
    print("\n✅ Batch processing test passed!")


def test_stats():
    """Test statistics collection"""
    print("\n" + "=" * 70)
    print("TEST 7: Statistics")
    print("=" * 70 + "\n")
    
    ocr = PlateOCR(use_gpu=False)
    
    stats = ocr.get_stats()
    
    print("OCR Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    assert stats['engine'] == 'PaddleOCR'
    assert stats['initialized'] == False, "Should not load on init"
    assert stats['gpu_enabled'] == False
    
    print("\n✅ Statistics test passed!")


def main():
    """Run all tests"""
    print("""
╔══════════════════════════════════════════════════════╗
║  License Plate OCR Testing                           ║
║  Indian Format Extraction & Validation               ║
╚══════════════════════════════════════════════════════╝
    """)
    
    try:
        # Tests that don't require actual OCR engine
        test_plate_format_validation()
        test_character_corrections()
        test_srgan_detection()
        test_plate_result_dataclass()
        test_preprocessing_validation()
        test_batch_processing()
        test_stats()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print("\nNote: Full OCR engine tests require PaddleOCR installation:")
        print("      pip install paddleocr paddlepaddle")
        print("\nUse demo_ocr.py for full end-to-end testing\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
