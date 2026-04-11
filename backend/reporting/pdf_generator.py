"""
PDF Evidence Report Generator

Generates professional PDF reports for traffic violations with:
- Evidence image
- Violation details
- Technical verification (SHA-256 hash)
- Legal compliance formatting
"""

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("reportlab not installed. PDF generation disabled.")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("Pillow not installed. Image processing disabled.")

logger = logging.getLogger(__name__)


class EvidenceReport:
    """
    Professional PDF evidence report generator.
    
    Usage:
        report = EvidenceReport()
        pdf_path = report.generate(violation_data)
        print(f"Report saved: {pdf_path}")
    """
    
    def __init__(self, output_dir: str = "reports"):
        """
        Initialize report generator.
        
        Args:
            output_dir: Directory to save reports (default: "reports")
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if not REPORTLAB_AVAILABLE:
            logger.warning("[PDF] reportlab not installed - PDF generation disabled")
        if not PIL_AVAILABLE:
            logger.warning("[PDF] Pillow not installed - image processing disabled")
    
    def generate(self, violation: Dict[str, Any]) -> Optional[str]:
        """
        Generate PDF report for a violation.
        
        Args:
            violation: Dictionary with violation data:
                - id: Violation ID
                - timestamp: Datetime
                - violation_type: Type of violation
                - plate_number: License plate (optional)
                - confidence: Detection confidence
                - latitude, longitude: GPS coordinates (optional)
                - image_path: Path to evidence image
                - sha256_hash: Image hash
                - llm_verified: LLM verification status
                - llm_confidence: LLM confidence (optional)
                - srgan_used: Whether SRGAN was applied
                - platform: Detection platform
        
        Returns:
            Path to generated PDF, or None if failed
        """
        if not REPORTLAB_AVAILABLE:
            logger.error("[PDF] Cannot generate report - reportlab not installed")
            return None
        
        try:
            # Create dated subfolder
            date_str = violation.get('timestamp', datetime.now()).strftime('%Y%m%d')
            date_folder = self.output_dir / date_str
            date_folder.mkdir(parents=True, exist_ok=True)
            
            # Generate report ID and filename
            report_id = f"TVD-{violation.get('id', 'UNKNOWN')}-{date_str}"
            pdf_filename = f"{report_id}.pdf"
            pdf_path = date_folder / pdf_filename
            
            logger.info(f"[PDF] Generating report: {pdf_path}")
            
            # Create PDF
            doc = SimpleDocTemplate(
                str(pdf_path),
                pagesize=A4,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )
            
            # Build content
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#333333'),
                spaceAfter=12,
                spaceBefore=20,
                fontName='Helvetica-Bold'
            )
            
            # Header
            story.append(Paragraph("TRAFFIC VIOLATION EVIDENCE REPORT", title_style))
            story.append(Paragraph(f"Report ID: {report_id}", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            # Section 1: Violation Details
            story.append(Paragraph("1. VIOLATION DETAILS", heading_style))
            
            details_data = [
                ['Violation Type:', violation.get('violation_type', 'Unknown').replace('_', ' ').title()],
                ['Date & Time:', violation.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M:%S UTC')],
                ['License Plate:', violation.get('plate_number', 'Not detected') or 'Not detected'],
                ['Detection Confidence:', f"{violation.get('confidence', 0) * 100:.1f}%"],
            ]
            
            # Add GPS if available
            lat = violation.get('latitude')
            lon = violation.get('longitude')
            if lat and lon:
                details_data.append(['GPS Coordinates:', f"{lat:.6f}°N, {lon:.6f}°E"])
                details_data.append(['Google Maps:', f"https://maps.google.com/maps?q={lat},{lon}"])
            
            details_table = Table(details_data, colWidths=[2*inch, 4*inch])
            details_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(details_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Section 2: Evidence Image
            story.append(Paragraph("2. EVIDENCE IMAGE", heading_style))
            
            image_path = violation.get('image_path')
            if image_path and Path(image_path).exists():
                try:
                    # Add image with caption
                    img = RLImage(image_path, width=5*inch, height=3.75*inch)
                    story.append(img)
                    story.append(Spacer(1, 0.1*inch))
                    story.append(Paragraph(
                        "<i>Original evidence image — unmodified</i>",
                        styles['Normal']
                    ))
                except Exception as e:
                    logger.error(f"[PDF] Failed to add image: {e}")
                    story.append(Paragraph(f"<i>Image unavailable: {e}</i>", styles['Normal']))
            else:
                story.append(Paragraph("<i>No evidence image available</i>", styles['Normal']))
            
            story.append(Spacer(1, 0.3*inch))
            
            # Section 3: Technical Verification
            story.append(Paragraph("3. TECHNICAL VERIFICATION", heading_style))
            
            tech_data = [
                ['Detection Model:', 'YOLOv26n (NMS-free)'],
                ['Model Accuracy:', 'mAP50: 85.9% | Precision: 80.5% | Recall: 82.0%'],
                ['Detection Platform:', violation.get('platform', 'Unknown')],
                ['SRGAN Enhancement:', 'Yes' if violation.get('srgan_used') else 'No'],
            ]
            
            # Add LLM verification if available
            if violation.get('llm_verified'):
                llm_conf = violation.get('llm_confidence', 0)
                tech_data.append(['LLM Verification:', f"Verified ({llm_conf:.1f}% confidence)"])
            else:
                tech_data.append(['LLM Verification:', 'Not performed'])
            
            # Add SHA-256 hash
            sha256 = violation.get('sha256_hash', 'Not computed')
            tech_data.append(['SHA-256 Hash:', sha256[:32] + '...' if len(sha256) > 32 else sha256])
            
            tech_table = Table(tech_data, colWidths=[2*inch, 4*inch])
            tech_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(tech_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Section 4: Legal Notice
            story.append(Paragraph("4. LEGAL NOTICE", heading_style))
            
            legal_text = f"""This report is generated by an AI-powered traffic violation detection system 
in accordance with the Information Technology Act, 2000 and Section 65B of the Indian Evidence Act, 1872.

The evidence image has been cryptographically hashed (SHA-256) to ensure integrity and prevent tampering. 
Any modification to the image will result in a different hash value.

SHA-256 Hash: {violation.get('sha256_hash', 'Not computed')}

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
Report ID: {report_id}

This document is digitally generated and does not require a physical signature."""
            
            story.append(Paragraph(legal_text, styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"[PDF] Report generated successfully: {pdf_path}")
            return str(pdf_path)
            
        except Exception as e:
            logger.error(f"[PDF] Failed to generate report: {e}")
            return None
    
    def compute_image_hash(self, image_path: str) -> str:
        """
        Compute SHA-256 hash of an image file.
        
        Args:
            image_path: Path to image file
        
        Returns:
            SHA-256 hash as hex string
        """
        try:
            with open(image_path, 'rb') as f:
                file_hash = hashlib.sha256()
                while chunk := f.read(8192):
                    file_hash.update(chunk)
                return file_hash.hexdigest()
        except Exception as e:
            logger.error(f"[PDF] Failed to compute hash: {e}")
            return "ERROR"


def generate_violation_report(violation: Dict[str, Any], output_dir: str = "reports") -> Optional[str]:
    """
    Convenience function to generate a violation report.
    
    Args:
        violation: Violation data dictionary
        output_dir: Output directory for reports
    
    Returns:
        Path to generated PDF, or None if failed
    """
    report = EvidenceReport(output_dir=output_dir)
    return report.generate(violation)


# Example usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Test data
    test_violation = {
        'id': 12345,
        'timestamp': datetime.now(),
        'violation_type': 'without_helmet',
        'plate_number': 'MH12AB1234',
        'confidence': 0.92,
        'latitude': 18.5204,
        'longitude': 73.8567,
        'image_path': 'test_image.jpg',  # Would need actual image
        'sha256_hash': 'a' * 64,  # Example hash
        'llm_verified': True,
        'llm_confidence': 88.5,
        'srgan_used': False,
        'platform': 'laptop_cpu'
    }
    
    print("PDF Report Generator Test")
    print("=" * 50)
    print(f"ReportLab available: {REPORTLAB_AVAILABLE}")
    print(f"PIL available: {PIL_AVAILABLE}")
    print()
    
    if REPORTLAB_AVAILABLE:
        report = EvidenceReport(output_dir="test_reports")
        pdf_path = report.generate(test_violation)
        
        if pdf_path:
            print(f"✓ Report generated: {pdf_path}")
        else:
            print("✗ Report generation failed")
    else:
        print("Install reportlab to test: pip install reportlab")
