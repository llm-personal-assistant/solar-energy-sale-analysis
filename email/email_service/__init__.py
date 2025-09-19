"""
Email Service Package

This package provides email reading, sending, and draft management functionality.
"""

from .email_reader import EmailReader
from .email_sender import EmailSender
from .draft_manager import DraftManager
from .email_service import EmailService

__all__ = ['EmailReader', 'EmailSender', 'DraftManager', 'EmailService']
