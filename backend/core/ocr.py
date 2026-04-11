"""
Indian License Plate OCR Module
Extracts and validates license plate text from bounding boxes using PaddleOCR
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import cv2
import numpy as np
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class PlateResult:
    """Result from license plate OCR"""
    
    raw_text: str                       # Text as returned by OCR
    cleaned_text: str                   # After cleaning and corrections
    confidence: float                   # OCR confidence (0-1)
    is_valid_indian_format: bool       # Matches Indian plate regex
    needs_srgan: bool                   # True if plate too small, needs upscaling
    
    def __str__(self):
        status = "✓" if self.is_valid_indian_format else "✗"
        return (
            f"PlateOCR({status} {self.cleaned_text} "
            f"conf={self.confidence:.2f} "
            f"srgan={self.needs_srgan})"
        )


class PlateOCR:
    """
    Indian license plate OCR using PaddleOCR
    
    Supports lazy initialization to save memory on import.
    Includes preprocessing, text cleaning, and format validation.
    """
    
    # Indian license plate regex pattern
    # Format: State(2) + District(1-2) + Category(1-3) + Serial(4)
    # Example: MH12AB1234, DL01CD5678
    PLATE_REGEX = r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}$'
    
    # Character correction mapping (OCR often misreads certain chars)
    # Only applied in numeric positions (2,3,6,7,8,9)
    CHAR_CORRECTIONS = {
        'O': '0',  # Letter O → zero
        'I': '1',  # Letter I → one
        'S': '5',  # Letter S → five
        'B': '8',  # Letter B → eight
        'G': '6',  # Letter G → six
    }
    
    # Minimum plate size thresholds
    MIN_PLATE_WIDTH = 80      # pixels
    MIN_PLATE_HEIGHT = 25     # pixels
    SRGAN_THRESHOLD = 3000    # pixels² - area below this triggers SRGAN
    
    def __init__(self, use_gpu: bool = False):
        """
        Initialize PlateOCR with lazy loading.
        
        Args:
            use_gpu: Whether to use GPU for OCR (requires CUDA)
        
        Note: PaddleOCR is NOT loaded until first read_plate call (lazy init)
        """
        self.use_gpu = use_gpu
        self.ocr = None  # Lazy initialized
        
        logger.info(f"PlateOCR initialized (GPU: {use_gpu}, lazy-loaded)")
    
    def _init_ocr(self):
        """Lazy initialization of PaddleOCR"""
        if self.ocr is not None:
            return
        
        try:
            from paddleocr import PaddleOCR
            
            logger.info("Initializing PaddleOCR engine...")
            self.ocr = PaddleOCR(
                use_angle_cls=False,      # Don't detect text orientation
                lang='en',                 # English language (for alphanumeric)
                use_gpu=self.use_gpu,     # GPU acceleration if available
                show_log=False             # Suppress PaddleOCR logs
            )
            logger.info("✓ PaddleOCR engine loaded")
        
        except ImportError as e:
            logger.error(
                f"Failed to import PaddleOCR: {e}\n"
                f"Install with: pip install paddleocr paddlepaddle"
            )
            raise
    
    def should_use_srgan(self, bbox: Tuple[int, int, int, int]) -> bool:
        """
        Determine if plate region is too small and needs SRGAN upscaling.
        
        Args:
            bbox: Bounding box (x1, y1, x2, y2)
        
        Returns:
            True if plate area < 3000 px² or width < 80px
        """
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        area = width * height
        
        needs_srgan = area < self.SRGAN_THRESHOLD or width < self.MIN_PLATE_WIDTH
        
        return needs_srgan
    
    def preprocess_plate(
        self,
        frame: np.ndarray,
        bbox: Tuple[int, int, int, int]
    ) -> Optional[np.ndarray]:
        """
        Preprocess license plate region for OCR.
        
        Extracts region, applies grayscale + Otsu threshold for better text visibility.
        
        Args:
            frame: Input frame (BGR)
            bbox: Bounding box (x1, y1, x2, y2)
        
        Returns:
            Preprocessed plate image or None if too small
        """
        x1, y1, x2, y2 = bbox
        
        # Add padding around plate (help with edge detection)
        padding = 10
        x1_padded = max(0, x1 - padding)
        y1_padded = max(0, y1 - padding)
        x2_padded = min(frame.shape[1], x2 + padding)
        y2_padded = min(frame.shape[0], y2 + padding)
        
        # Extract plate region
        plate_crop = frame[y1_padded:y2_padded, x1_padded:x2_padded]
        
        # Get actual dimensions
        height, width = plate_crop.shape[:2]
        
        # Validate size
        if width < self.MIN_PLATE_WIDTH or height < self.MIN_PLATE_HEIGHT:
            logger.debug(f"OCR SKIP: plate too small ({width}x{height}px)")
            return None
        
        # Convert to grayscale
        gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
        
        # Apply Otsu threshold for better text contrast
        _, threshold = cv2.threshold(
            gray, 0, 255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        
        return threshold
    
    def _clean_text(self, raw_text: str) -> str:
        """
        Clean and normalize OCR output.
        
        Steps:
        1. Convert to uppercase
        2. Remove spaces and hyphens
        3. Apply character corrections in numeric positions only
        
        Args:
            raw_text: Raw OCR output
        
        Returns:
            Cleaned text
        """
        # Step 1 & 2: Uppercase and remove spaces/hyphens
        cleaned = raw_text.upper().replace(' ', '').replace('-', '')
        
        # Step 3: Apply character corrections ONLY in numeric positions
        # Indian plate format: AA 00 ABC 0000
        # Positions: 0-1 (state), 2-3 (district), 4-6 (category), 7-10 (serial)
        # Numeric positions: 2, 3, 7, 8, 9, 10 (0-indexed)
        # But serial can be 3-4 digits, so positions 6-9 can be numeric
        
        numeric_position_ranges = [
            (2, 4),    # District number (positions 2-3)
            (6, 10),   # Serial number (positions 6-9)
        ]
        
        cleaned_list = list(cleaned)
        
        for i, char in enumerate(cleaned_list):
            # Check if this position should be numeric
            is_numeric_position = any(
                start <= i < end for start, end in numeric_position_ranges
            )
            
            # Only correct if in numeric position and is a correctable char
            if is_numeric_position and char in self.CHAR_CORRECTIONS:
                cleaned_list[i] = self.CHAR_CORRECTIONS[char]
        
        cleaned = ''.join(cleaned_list)
        
        return cleaned
    
    def _validate_format(self, text: str) -> bool:
        """
        Validate text against Indian license plate format.
        
        Format: [A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}
        Examples:
        - MH12AB1234 (district: 12)
        - DL01CD5678 (district: 01)
        - KA5ABC1234 (district: 5)
        
        Args:
            text: Cleaned plate text
        
        Returns:
            True if matches Indian plate format
        """
        return bool(re.match(self.PLATE_REGEX, text))
    
    def read_plate(
        self,
        frame: np.ndarray,
        bbox: Tuple[int, int, int, int]
    ) -> Optional[PlateResult]:
        """
        Extract and validate license plate text from frame.
        
        Args:
            frame: Input frame (BGR)
            bbox: Bounding box (x1, y1, x2, y2)
        
        Returns:
            PlateResult with extracted text and metadata, or None if preprocessing failed
        """
        
        # Lazy init OCR on first call
        if self.ocr is None:
            self._init_ocr()
        
        # Check if SRGAN needed
        needs_srgan = self.should_use_srgan(bbox)
        
        # Preprocess plate
        preprocessed = self.preprocess_plate(frame, bbox)
        
        if preprocessed is None:
            x1, y1, x2, y2 = bbox
            width = x2 - x1
            height = y2 - y1
            logger.debug(f"OCR SKIP: plate too small ({width}x{height}px)")
            return None
        
        try:
            # Run OCR on preprocessed image
            ocr_result = self.ocr.ocr(preprocessed, cls=False)
            
            # Extract text and confidence from first line
            # PaddleOCR returns: [((x,y), (x,y), (x,y), (x,y)), text, confidence]
            if not ocr_result or not ocr_result[0]:
                logger.debug("OCR: No text detected in plate region")
                return PlateResult(
                    raw_text="",
                    cleaned_text="",
                    confidence=0.0,
                    is_valid_indian_format=False,
                    needs_srgan=needs_srgan
                )
            
            # Extract text and confidence
            raw_text = ocr_result[0][0][1]  # Second element is text
            confidence = float(ocr_result[0][0][2])  # Third element is confidence
            
            # Clean text
            cleaned_text = self._clean_text(raw_text)
            
            # Validate format
            is_valid = self._validate_format(cleaned_text)
            
            # Create result
            result = PlateResult(
                raw_text=raw_text,
                cleaned_text=cleaned_text,
                confidence=confidence,
                is_valid_indian_format=is_valid,
                needs_srgan=needs_srgan
            )
            
            # Log result
            status = "✓" if is_valid else "✗"
            logger.info(
                f"OCR: {status} {cleaned_text} conf={confidence:.2f} "
                f"srgan={needs_srgan}"
            )
            
            return result
        
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return None
    
    def batch_read_plates(
        self,
        frame: np.ndarray,
        bboxes: list
    ) -> list:
        """
        Extract text from multiple plate bounding boxes.
        
        Args:
            frame: Input frame
            bboxes: List of bounding boxes
        
        Returns:
            List of PlateResult objects
        """
        results = []
        for bbox in bboxes:
            result = self.read_plate(frame, bbox)
            if result is not None:
                results.append(result)
        
        return results
    
    def get_stats(self) -> dict:
        """
        Get OCR statistics.
        
        Returns:
            Dictionary with stats (if tracking enabled)
        """
        return {
            'pipelinename': 'PlateOCR',
            'engine': 'PaddleOCR',
            'initialized': self.ocr is not None,
            'gpu_enabled': self.use_gpu,
        }


# Utility functions for integration

def extract_plate_text(frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> Optional[str]:
    """
    Convenience function to extract plate text (creates temporary PlateOCR).
    
    Note: Creates new instance each time - use PlateOCR class for repeated calls.
    """
    ocr = PlateOCR(use_gpu=False)
    result = ocr.read_plate(frame, bbox)
    return result.cleaned_text if result else None


def validate_indian_plate(text: str) -> bool:
    """
    Quick validation of Indian license plate format.
    
    Args:
        text: Plate text to validate
    
    Returns:
        True if matches Indian format
    """
    return bool(re.match(PlateOCR.PLATE_REGEX, text))
