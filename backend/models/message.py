"""
Message Model
Represents an individual iMessage or SMS message with forensic metadata
"""

import json
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Index,
)
from sqlalchemy.orm import relationship

from backend.models.base import Base


class Message(Base):
    """
    Individual message from iMessage/SMS database.
    All timestamps stored in UTC with timezone preservation.
    """

    __tablename__ = "messages"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Unique Message Identifier (forensically stable)
    message_id = Column(String(100), unique=True, nullable=False, index=True)
    # Format: MSG_<CASEID>_<EXTRACTION_TS>_<CONV_HASH>_<SEQ>

    # Conversation Context
    conversation_id = Column(String(100), nullable=False, index=True)

    # Participants
    sender_id = Column(String(255))  # Phone number or email
    sender_name = Column(String(255))
    recipient_ids = Column(Text)  # JSON array of recipient IDs

    # Message Content
    message_text = Column(Text)
    message_type = Column(String(50))  # 'text', 'attachment', 'reaction', etc.
    service_name = Column(String(50))  # 'iMessage', 'SMS', etc.

    # Timestamps (all in UTC, original timezone preserved separately)
    timestamp = Column(Integer, nullable=False, index=True)  # Unix timestamp
    timezone = Column(String(50))  # Original timezone (e.g., "America/New_York")

    # Attachment References
    has_attachment = Column(Boolean, default=False)
    attachment_ids = Column(Text)  # JSON array of attachment IDs

    # Message Metadata
    is_from_me = Column(Boolean, default=False)
    read_receipt = Column(Boolean, default=False)

    # Forensic Data
    hash = Column(String(64), nullable=False)  # SHA-256 of message content
    extraction_timestamp = Column(Integer, nullable=False)  # When message was extracted

    # Export Partitioning
    part_number = Column(Integer, default=1, index=True)
    sequence_in_part = Column(Integer)

    # Creation Timestamp
    created_at = Column(Integer, nullable=False)

    # Relationships
    attachments = relationship(
        "Attachment",
        back_populates="message",
        cascade="all, delete-orphan",
    )
    annotations = relationship(
        "Annotation",
        back_populates="message",
        cascade="all, delete-orphan",
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_conversation_timestamp", "conversation_id", "timestamp"),
        Index("idx_part_sequence", "part_number", "sequence_in_part"),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.created_at:
            self.created_at = int(datetime.utcnow().timestamp())

    def get_recipient_ids(self) -> List[str]:
        """Parse recipient IDs from JSON."""
        if not self.recipient_ids:
            return []
        try:
            return json.loads(self.recipient_ids)
        except json.JSONDecodeError:
            return []

    def set_recipient_ids(self, recipient_list: List[str]):
        """Store recipient IDs as JSON."""
        self.recipient_ids = json.dumps(recipient_list)

    def get_attachment_ids(self) -> List[str]:
        """Parse attachment IDs from JSON."""
        if not self.attachment_ids:
            return []
        try:
            return json.loads(self.attachment_ids)
        except json.JSONDecodeError:
            return []

    def set_attachment_ids(self, attachment_list: List[str]):
        """Store attachment IDs as JSON."""
        self.attachment_ids = json.dumps(attachment_list)
        self.has_attachment = bool(attachment_list)

    def get_timestamp_datetime(self) -> datetime:
        """Convert Unix timestamp to datetime object (UTC)."""
        return datetime.utcfromtimestamp(self.timestamp)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "recipient_ids": self.get_recipient_ids(),
            "message_text": self.message_text,
            "message_type": self.message_type,
            "service_name": self.service_name,
            "timestamp": self.timestamp,
            "timezone": self.timezone,
            "has_attachment": self.has_attachment,
            "attachment_ids": self.get_attachment_ids(),
            "is_from_me": self.is_from_me,
            "read_receipt": self.read_receipt,
            "hash": self.hash,
            "part_number": self.part_number,
            "sequence_in_part": self.sequence_in_part,
        }

    def __repr__(self):
        return (
            f"<Message(id={self.message_id}, "
            f"conversation={self.conversation_id}, "
            f"timestamp={self.get_timestamp_datetime()}, "
            f"from_me={self.is_from_me})>"
        )
