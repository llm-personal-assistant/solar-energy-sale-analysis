"""
Data sync module for email leads and messages.

This module provides functionality for synchronizing email data with Supabase,
including AI-analyzed lead information and associated email messages.
Supports Gmail and Outlook email providers.
"""

from .models import (
    EmailLead, EmailLeadCreate, EmailLeadUpdate,
    EmailMessage, EmailMessageCreate, EmailMessageUpdate,
    EmailLeadWithMessages, DataSyncResponse, BulkSyncRequest, SyncStats,
    SentimentLabel, UrgencyLevel, PriorityLevel, DiscountSensitivityLevel,
    EmailAccount, EmailSyncRequest, EmailSyncResult
)
from .sync_service import EmailDataSyncService
from .gmail_service import GmailService
from .outlook_service import OutlookService
from .email_sync_service import EmailSyncService
from .data_sync_routes import router as data_sync_router

__all__ = [
    # Models
    "EmailLead",
    "EmailLeadCreate", 
    "EmailLeadUpdate",
    "EmailMessage",
    "EmailMessageCreate",
    "EmailMessageUpdate",
    "EmailLeadWithMessages",
    "DataSyncResponse",
    "BulkSyncRequest",
    "SyncStats",
    "EmailAccount",
    "EmailSyncRequest",
    "EmailSyncResult",
    
    # Enums
    "SentimentLabel",
    "UrgencyLevel", 
    "PriorityLevel",
    "DiscountSensitivityLevel",
    
    # Services
    "EmailDataSyncService",
    "GmailService",
    "OutlookService",
    "EmailSyncService",
    
    # Routes
    "data_sync_router"
]
