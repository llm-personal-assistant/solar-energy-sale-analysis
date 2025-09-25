"""
Data models for email data sync tables.
Defines Pydantic models for email_lead and email_message tables.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class SentimentLabel(str, Enum):
    """Sentiment label enumeration."""
    POSITIVE = "Positive"
    NEUTRAL = "Neutral"
    NEGATIVE = "Negative"


class UrgencyLevel(str, Enum):
    """Urgency level enumeration."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class PriorityLevel(str, Enum):
    """Priority level enumeration."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class DiscountSensitivityLevel(str, Enum):
    """Discount sensitivity level enumeration."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class EmailLeadBase(BaseModel):
    """Base model for email lead data."""
    lead_id: str = Field(..., description="Unique identifier for the lead")
    owner: Optional[str] = Field(None, max_length=255, description="Owner of the lead")
    subject: Optional[str] = Field(None, description="Email subject")
    summary: Optional[str] = Field(None, description="Summary of the lead")
    internal_date: Optional[int] = Field(None, description="Internal date timestamp")
    
    # Intent analysis
    intent_category: str = Field(..., description="Category of the intent")
    intent_confidence: float = Field(..., ge=0, le=1, description="Confidence score for intent (0-1)")
    intent_reason: str = Field(..., description="Reason for intent classification")
    
    # Purchase intent
    purchase_intent_score: int = Field(..., ge=0, le=100, description="Purchase intent score (0-100)")
    purchase_intent_reason: str = Field(..., description="Reason for purchase intent score")
    
    # Sentiment analysis
    sentiment_label: SentimentLabel = Field(..., description="Sentiment label")
    sentiment_score: float = Field(..., ge=-1, le=1, description="Sentiment score (-1 to 1)")
    sentiment_reason: str = Field(..., description="Reason for sentiment classification")
    
    # Urgency analysis
    urgency_level: UrgencyLevel = Field(..., description="Urgency level")
    urgency_reason: str = Field(..., description="Reason for urgency level")
    
    # Keywords and pain points
    pain_points: List[str] = Field(default_factory=list, description="List of pain points")
    keywords: List[str] = Field(default_factory=list, description="List of keywords")
    
    # Sales opportunity
    upsell_value: bool = Field(..., description="Whether there's upsell value")
    upsell_reason: Optional[str] = Field(None, description="Reason for upsell value")
    cross_sell_value: bool = Field(..., description="Whether there's cross-sell value")
    cross_sell_reason: Optional[str] = Field(None, description="Reason for cross-sell value")
    
    # Discount sensitivity
    discount_sensitivity_level: DiscountSensitivityLevel = Field(..., description="Discount sensitivity level")
    discount_sensitivity_reason: Optional[str] = Field(None, description="Reason for discount sensitivity")
    
    # Recommendations and priority
    recommended_steps: List[str] = Field(default_factory=list, description="List of recommended steps")
    priority_level: PriorityLevel = Field(..., description="Priority level")


class EmailLeadCreate(EmailLeadBase):
    """Model for creating a new email lead."""
    pass


class EmailLeadUpdate(BaseModel):
    """Model for updating an email lead."""
    owner: Optional[str] = Field(None, max_length=255)
    subject: Optional[str] = None
    summary: Optional[str] = None
    internal_date: Optional[int] = None
    
    intent_category: Optional[str] = None
    intent_confidence: Optional[float] = Field(None, ge=0, le=1)
    intent_reason: Optional[str] = None
    
    purchase_intent_score: Optional[int] = Field(None, ge=0, le=100)
    purchase_intent_reason: Optional[str] = None
    
    sentiment_label: Optional[SentimentLabel] = None
    sentiment_score: Optional[float] = Field(None, ge=-1, le=1)
    sentiment_reason: Optional[str] = None
    
    urgency_level: Optional[UrgencyLevel] = None
    urgency_reason: Optional[str] = None
    
    pain_points: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    
    upsell_value: Optional[bool] = None
    upsell_reason: Optional[str] = None
    cross_sell_value: Optional[bool] = None
    cross_sell_reason: Optional[str] = None
    
    discount_sensitivity_level: Optional[DiscountSensitivityLevel] = None
    discount_sensitivity_reason: Optional[str] = None
    
    recommended_steps: Optional[List[str]] = None
    priority_level: Optional[PriorityLevel] = None


class EmailLead(EmailLeadBase):
    """Complete email lead model with metadata."""
    user_id: str = Field(..., description="User ID who owns this lead")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class EmailMessageBase(BaseModel):
    """Base model for email message data."""
    message_id: str = Field(..., description="Unique identifier for the message")
    lead_id: Optional[str] = Field(None, description="ID of the associated lead")
    owner: Optional[str] = Field(None, max_length=255, description="Owner of the message")
    sender: Optional[str] = Field(None, max_length=255, description="Message sender")
    receiver: Optional[str] = Field(None, description="Message receiver")
    subject: Optional[str] = Field(None, description="Message subject")
    body: Optional[str] = Field(None, description="Message body content")
    is_read: bool = Field(False, description="Whether the message has been read")
    folder: Optional[str] = Field(None, description="Folder where the message is located (inbox, sent, etc.)")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw message data as JSON")
    summary: Optional[str] = Field(None, description="Message summary")
    internal_date: Optional[int] = Field(None, description="Internal date timestamp")
    history_id: Optional[int] = Field(None, description="History ID")


class EmailMessageCreate(EmailMessageBase):
    """Model for creating a new email message."""
    pass


class EmailMessageUpdate(BaseModel):
    """Model for updating an email message."""
    lead_id: Optional[str] = None
    owner: Optional[str] = Field(None, max_length=255)
    sender: Optional[str] = Field(None, max_length=255)
    receiver: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    is_read: Optional[bool] = None
    folder: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    internal_date: Optional[int] = None
    history_id: Optional[int] = None


class EmailMessage(EmailMessageBase):
    """Complete email message model with metadata."""
    user_id: str = Field(..., description="User ID who owns this message")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class EmailLeadWithMessages(EmailLead):
    """Email lead model with associated messages."""
    messages: List[EmailMessage] = Field(default_factory=list, description="Associated email messages")


class DataSyncResponse(BaseModel):
    """Response model for data sync operations."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    errors: Optional[List[str]] = Field(None, description="List of errors if any")


class BulkSyncRequest(BaseModel):
    """Model for bulk sync operations."""
    leads: List[EmailLeadCreate] = Field(..., description="List of leads to sync")
    messages: List[EmailMessageCreate] = Field(..., description="List of messages to sync")
    user_id: str = Field(..., description="User ID for the sync operation")


class SyncStats(BaseModel):
    """Statistics for sync operations."""
    leads_processed: int = Field(0, description="Number of leads processed")
    messages_processed: int = Field(0, description="Number of messages processed")
    leads_created: int = Field(0, description="Number of leads created")
    leads_updated: int = Field(0, description="Number of leads updated")
    messages_created: int = Field(0, description="Number of messages created")
    messages_updated: int = Field(0, description="Number of messages updated")
    errors: List[str] = Field(default_factory=list, description="List of errors encountered")


# Email Account models for provider integration
class EmailAccount(BaseModel):
    """Email account model from provider module."""
    id: str
    user_id: str
    email: str
    provider: str  # 'google', 'outlook', 'yahoo'
    access_token: str
    refresh_token: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class EmailSyncRequest(BaseModel):
    """Request model for email synchronization."""
    user_id: str = Field(..., description="User ID for the sync operation")
    max_messages: int = Field(100, description="Maximum number of messages to sync")
    folder: Optional[str] = Field(None, description="Specific folder to sync")


class EmailSyncResult(BaseModel):
    """Result model for email synchronization."""
    success: bool = Field(..., description="Whether the sync was successful")
    messages_synced: int = Field(0, description="Number of messages synced")
    messages_created: int = Field(0, description="Number of new messages created")
    messages_updated: int = Field(0, description="Number of messages updated")
    errors: List[str] = Field(default_factory=list, description="List of errors encountered")
    sync_time: datetime = Field(default_factory=datetime.utcnow, description="Sync completion time")
