"""
Reporting Module

Provides PDF report generation and email notifications for violations.
"""

from .pdf_generator import EvidenceReport, generate_violation_report
from .email_sender import send_violation_report, EmailSender

__all__ = [
    'EvidenceReport',
    'generate_violation_report',
    'send_violation_report',
    'EmailSender'
]
