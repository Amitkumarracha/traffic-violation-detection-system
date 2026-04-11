"""
Email Notification Module

Sends violation reports via SendGrid email service.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
    import base64
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    logging.warning("sendgrid not installed. Email notifications disabled.")

logger = logging.getLogger(__name__)


class EmailSender:
    """
    SendGrid email sender for violation reports.
    
    Usage:
        sender = EmailSender(api_key="your_key", from_email="alerts@example.com")
        sender.send_violation_report(
            violation=violation_data,
            pdf_path="report.pdf",
            recipient_email="officer@police.gov.in"
        )
    """
    
    def __init__(self, api_key: Optional[str] = None, from_email: str = "noreply@trafficviolation.ai"):
        """
        Initialize email sender.
        
        Args:
            api_key: SendGrid API key (if None, email disabled)
            from_email: Sender email address
        """
        self.api_key = api_key
        self.from_email = from_email
        self.client = None
        self._sent_count = 0
        self._failed_count = 0
        
        if not SENDGRID_AVAILABLE:
            logger.warning("[Email] sendgrid not installed - email notifications disabled")
            return
        
        if api_key:
            try:
                self.client = SendGridAPIClient(api_key)
                logger.info("[Email] SendGrid client initialized")
            except Exception as e:
                logger.error(f"[Email] Failed to initialize SendGrid: {e}")
                self.client = None
    
    def send_violation_report(
        self,
        violation: Dict[str, Any],
        pdf_path: Optional[str],
        recipient_email: str
    ) -> bool:
        """
        Send violation report email with PDF attachment.
        
        Args:
            violation: Violation data dictionary
            pdf_path: Path to PDF report (optional)
            recipient_email: Recipient email address
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not SENDGRID_AVAILABLE or self.client is None:
            logger.warning("[Email] Cannot send - SendGrid not configured")
            return False
        
        try:
            # Build email subject
            violation_type = violation.get('violation_type', 'Unknown').replace('_', ' ').title()
            plate = violation.get('plate_number', 'Unknown')
            timestamp = violation.get('timestamp', datetime.now())
            
            subject = f"Traffic Violation Report — {plate} — {timestamp.strftime('%Y-%m-%d %H:%M')}"
            
            # Build HTML body
            html_content = self._build_html_body(violation)
            
            # Create email
            message = Mail(
                from_email=self.from_email,
                to_emails=recipient_email,
                subject=subject,
                html_content=html_content
            )
            
            # Attach PDF if available
            if pdf_path and Path(pdf_path).exists():
                try:
                    with open(pdf_path, 'rb') as f:
                        pdf_data = f.read()
                    
                    encoded_pdf = base64.b64encode(pdf_data).decode()
                    
                    attachment = Attachment(
                        FileContent(encoded_pdf),
                        FileName(Path(pdf_path).name),
                        FileType('application/pdf'),
                        Disposition('attachment')
                    )
                    message.attachment = attachment
                    logger.info(f"[Email] Attached PDF: {Path(pdf_path).name}")
                    
                except Exception as e:
                    logger.error(f"[Email] Failed to attach PDF: {e}")
            
            # Send email
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                self._sent_count += 1
                logger.info(f"[Email] Sent successfully to {recipient_email} (status: {response.status_code})")
                return True
            else:
                self._failed_count += 1
                logger.error(f"[Email] Send failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self._failed_count += 1
            logger.error(f"[Email] Failed to send email: {e}")
            return False
    
    def _build_html_body(self, violation: Dict[str, Any]) -> str:
        """Build HTML email body"""
        violation_type = violation.get('violation_type', 'Unknown').replace('_', ' ').title()
        plate = violation.get('plate_number', 'Not detected')
        timestamp = violation.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M:%S UTC')
        confidence = violation.get('confidence', 0) * 100
        
        lat = violation.get('latitude')
        lon = violation.get('longitude')
        location_html = ""
        if lat and lon:
            maps_url = f"https://maps.google.com/maps?q={lat},{lon}"
            location_html = f"""
            <tr>
                <td style="padding: 8px; background-color: #f9f9f9; font-weight: bold;">Location:</td>
                <td style="padding: 8px;">{lat:.6f}°N, {lon:.6f}°E 
                    <a href="{maps_url}" style="color: #0066cc;">View on Google Maps</a>
                </td>
            </tr>
            """
        
        llm_html = ""
        if violation.get('llm_verified'):
            llm_conf = violation.get('llm_confidence', 0)
            llm_html = f"""
            <tr>
                <td style="padding: 8px; background-color: #f9f9f9; font-weight: bold;">AI Verification:</td>
                <td style="padding: 8px;">✓ Verified ({llm_conf:.1f}% confidence)</td>
            </tr>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Traffic Violation Report</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #d32f2f; color: white; padding: 20px; text-align: center;">
                    <h1 style="margin: 0;">Traffic Violation Detected</h1>
                </div>
                
                <div style="background-color: #f5f5f5; padding: 20px; margin-top: 20px;">
                    <h2 style="color: #d32f2f; margin-top: 0;">Violation Summary</h2>
                    
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px; background-color: #f9f9f9; font-weight: bold;">Violation Type:</td>
                            <td style="padding: 8px;">{violation_type}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; background-color: #f9f9f9; font-weight: bold;">Date & Time:</td>
                            <td style="padding: 8px;">{timestamp}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; background-color: #f9f9f9; font-weight: bold;">License Plate:</td>
                            <td style="padding: 8px;">{plate}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; background-color: #f9f9f9; font-weight: bold;">Confidence:</td>
                            <td style="padding: 8px;">{confidence:.1f}%</td>
                        </tr>
                        {location_html}
                        {llm_html}
                    </table>
                </div>
                
                <div style="margin-top: 20px; padding: 15px; background-color: #fff3cd; border-left: 4px solid #ffc107;">
                    <p style="margin: 0;"><strong>Note:</strong> A detailed PDF report is attached to this email.</p>
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; text-align: center;">
                    <p>This is an automated message from the Traffic Violation Detection System.</p>
                    <p>Generated by AI-powered detection system | YOLOv26n | mAP50: 85.9%</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def get_stats(self) -> dict:
        """Get email statistics"""
        return {
            'configured': self.client is not None,
            'sent_count': self._sent_count,
            'failed_count': self._failed_count,
            'success_rate': self._sent_count / max(1, self._sent_count + self._failed_count)
        }


def send_violation_report(
    violation: Dict[str, Any],
    pdf_path: Optional[str],
    recipient_email: str,
    api_key: Optional[str] = None,
    from_email: str = "noreply@trafficviolation.ai"
) -> bool:
    """
    Convenience function to send a violation report email.
    
    Args:
        violation: Violation data dictionary
        pdf_path: Path to PDF report
        recipient_email: Recipient email address
        api_key: SendGrid API key
        from_email: Sender email address
    
    Returns:
        True if sent successfully, False otherwise
    """
    sender = EmailSender(api_key=api_key, from_email=from_email)
    return sender.send_violation_report(violation, pdf_path, recipient_email)


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
        'llm_verified': True,
        'llm_confidence': 88.5,
    }
    
    print("Email Sender Test")
    print("=" * 50)
    print(f"SendGrid available: {SENDGRID_AVAILABLE}")
    print()
    
    # Test without API key (should gracefully fail)
    sender = EmailSender()
    print(f"Stats: {sender.get_stats()}")
    print()
    
    # Try to send (will fail without API key)
    success = sender.send_violation_report(
        violation=test_violation,
        pdf_path="test_report.pdf",
        recipient_email="test@example.com"
    )
    
    print(f"Send result: {success}")
    print(f"Final stats: {sender.get_stats()}")
    print()
    print("To enable email: Set SENDGRID_API_KEY in .env file")
