"""
Gemini LLM Verification Module

Uses Google Gemini Flash for AI-powered violation verification.
Only called when YOLO confidence < 0.90 to save API costs.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import time

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logging.warning("google-generativeai not installed. LLM verification disabled.")

from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Result from LLM verification"""
    verified: bool
    confidence: float  # 0-100
    violation_description: str
    reasoning: str
    error: Optional[str] = None
    
    def __str__(self):
        if self.error:
            return f"VerificationResult(error={self.error})"
        return f"VerificationResult(verified={self.verified}, confidence={self.confidence:.1f}%, desc='{self.violation_description[:50]}...')"


class GeminiVerifier:
    """
    Google Gemini Flash LLM verifier for traffic violations.
    
    Usage:
        verifier = GeminiVerifier()
        result = verifier.verify_violation(
            image_path="evidence.jpg",
            violation_type="without_helmet",
            plate_number="MH12AB1234"
        )
        
        if result.verified and result.confidence > 80:
            print(f"Confirmed: {result.violation_description}")
    """
    
    def __init__(self, api_key: Optional[str] = None, skip_threshold: float = 0.90):
        """
        Initialize Gemini verifier.
        
        Args:
            api_key: Gemini API key (if None, loads from settings)
            skip_threshold: Don't call LLM if YOLO confidence >= this (default: 0.90)
        """
        self.skip_threshold = skip_threshold
        self.model = None
        self.api_key = api_key
        self._init_count = 0
        self._verify_count = 0
        self._skip_count = 0
        
        if not GENAI_AVAILABLE:
            logger.warning("[LLM] google-generativeai not installed - verification disabled")
            return
        
        # Lazy init - only load API key when first needed
        if api_key:
            self._initialize_model(api_key)
    
    def _initialize_model(self, api_key: str):
        """Initialize Gemini model (lazy loading)"""
        if self.model is not None:
            return
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self._init_count += 1
            logger.info("[LLM] Gemini Flash model initialized")
        except Exception as e:
            logger.error(f"[LLM] Failed to initialize Gemini: {e}")
            self.model = None
    
    def verify_violation(
        self,
        image_path: str,
        violation_type: str,
        plate_number: Optional[str] = None,
        yolo_confidence: float = 0.0
    ) -> VerificationResult:
        """
        Verify a traffic violation using Gemini vision model.
        
        Args:
            image_path: Path to evidence image
            violation_type: Type of violation (without_helmet, triple_ride, etc.)
            plate_number: Detected plate number (optional)
            yolo_confidence: YOLO detection confidence (0-1)
        
        Returns:
            VerificationResult with verification details
        """
        # Skip if confidence already high
        if yolo_confidence >= self.skip_threshold:
            self._skip_count += 1
            logger.info(f"[LLM] SKIP verification (YOLO conf={yolo_confidence:.2f} >= {self.skip_threshold})")
            return VerificationResult(
                verified=True,
                confidence=yolo_confidence * 100,
                violation_description=f"High-confidence {violation_type} detection",
                reasoning=f"YOLO confidence {yolo_confidence:.2f} exceeds threshold {self.skip_threshold}"
            )
        
        # Check if LLM available
        if not GENAI_AVAILABLE or self.model is None:
            # Try to initialize if we have API key
            if self.api_key:
                self._initialize_model(self.api_key)
            
            if self.model is None:
                logger.warning("[LLM] Verification unavailable - returning YOLO result")
                return VerificationResult(
                    verified=yolo_confidence > 0.75,
                    confidence=yolo_confidence * 100,
                    violation_description=f"{violation_type} (LLM unavailable)",
                    reasoning="LLM verification not available",
                    error="Gemini API not configured"
                )
        
        # Load image
        try:
            image_path_obj = Path(image_path)
            if not image_path_obj.exists():
                logger.error(f"[LLM] Image not found: {image_path}")
                return VerificationResult(
                    verified=False,
                    confidence=0.0,
                    violation_description="",
                    reasoning="",
                    error=f"Image not found: {image_path}"
                )
            
            image = Image.open(image_path)
            
        except Exception as e:
            logger.error(f"[LLM] Failed to load image: {e}")
            return VerificationResult(
                verified=False,
                confidence=0.0,
                violation_description="",
                reasoning="",
                error=f"Failed to load image: {str(e)}"
            )
        
        # Build prompt
        prompt = self._build_prompt(violation_type, plate_number, yolo_confidence)
        
        # Call Gemini API
        try:
            start_time = time.time()
            logger.info(f"[LLM] CALL verification for {violation_type} (YOLO conf={yolo_confidence:.2f})")
            
            response = self.model.generate_content([prompt, image])
            
            elapsed_ms = (time.time() - start_time) * 1000
            self._verify_count += 1
            
            # Parse response
            result = self._parse_response(response.text)
            logger.info(f"[LLM] Response in {elapsed_ms:.0f}ms: verified={result.verified}, conf={result.confidence:.1f}%")
            
            return result
            
        except Exception as e:
            logger.error(f"[LLM] API call failed: {e}")
            return VerificationResult(
                verified=False,
                confidence=0.0,
                violation_description="",
                reasoning="",
                error=f"API call failed: {str(e)}"
            )
    
    def _build_prompt(self, violation_type: str, plate_number: Optional[str], yolo_confidence: float) -> str:
        """Build verification prompt for Gemini"""
        plate_info = f"Detected plate: {plate_number}" if plate_number else "No plate detected"
        
        prompt = f"""You are a traffic enforcement AI assistant. Analyze this image and determine if there is a traffic violation.

Violation type to verify: {violation_type}
{plate_info}
YOLO detection confidence: {yolo_confidence:.2f}

Respond ONLY with valid JSON in this exact format:
{{
    "verified": true or false,
    "confidence": 0-100,
    "violation_description": "brief description of what you see",
    "reasoning": "why you made this determination"
}}

Guidelines:
- without_helmet: Verify rider is not wearing a helmet
- triple_ride: Verify 3 or more people on a motorcycle
- traffic_violation: Verify any traffic rule violation (red light, wrong lane, etc.)
- Be conservative - only verify if clearly visible
- Consider image quality and viewing angle
- Confidence should reflect certainty (0-100)

Respond with JSON only, no other text."""
        
        return prompt
    
    def _parse_response(self, response_text: str) -> VerificationResult:
        """Parse Gemini JSON response"""
        try:
            # Extract JSON from response (handle markdown code blocks)
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            data = json.loads(response_text)
            
            return VerificationResult(
                verified=bool(data.get('verified', False)),
                confidence=float(data.get('confidence', 0.0)),
                violation_description=str(data.get('violation_description', '')),
                reasoning=str(data.get('reasoning', ''))
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"[LLM] Failed to parse JSON response: {e}")
            logger.debug(f"[LLM] Raw response: {response_text[:200]}")
            return VerificationResult(
                verified=False,
                confidence=0.0,
                violation_description="",
                reasoning="",
                error=f"Failed to parse response: {str(e)}"
            )
        except Exception as e:
            logger.error(f"[LLM] Unexpected error parsing response: {e}")
            return VerificationResult(
                verified=False,
                confidence=0.0,
                violation_description="",
                reasoning="",
                error=f"Unexpected error: {str(e)}"
            )
    
    def get_stats(self) -> dict:
        """Get verification statistics"""
        return {
            'initialized': self.model is not None,
            'init_count': self._init_count,
            'verify_count': self._verify_count,
            'skip_count': self._skip_count,
            'skip_threshold': self.skip_threshold,
            'total_calls': self._verify_count + self._skip_count
        }


# Example usage
if __name__ == '__main__':
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    # Test without API key (should gracefully degrade)
    verifier = GeminiVerifier()
    
    print("Gemini Verifier Test")
    print("=" * 50)
    print(f"Available: {GENAI_AVAILABLE}")
    print(f"Stats: {verifier.get_stats()}")
    print()
    
    # Test with high confidence (should skip)
    result = verifier.verify_violation(
        image_path="test.jpg",
        violation_type="without_helmet",
        yolo_confidence=0.95
    )
    print(f"High confidence test: {result}")
    print()
    
    # Test with low confidence (would call API if configured)
    result = verifier.verify_violation(
        image_path="test.jpg",
        violation_type="without_helmet",
        yolo_confidence=0.70
    )
    print(f"Low confidence test: {result}")
    print()
    
    print(f"Final stats: {verifier.get_stats()}")
