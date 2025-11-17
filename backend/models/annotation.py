"""
Annotation Models
Message annotations (tags and notes) with full audit trail for work product tracking
"""

import json
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from backend.models.base import Base
from backend.config import ANNOTATION_CONFIG


class Annotation(Base):
    """
    Attorney work product annotation for a specific message.
    Contains tags and free-form notes for legal review.
    ALL CHANGES LOGGED IN AUDIT TABLE.
    """

    __tablename__ = "annotations"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Unique Annotation Identifier
    annotation_id = Column(String(100), unique=True, nullable=False, index=True)
    # Format: ANN_<CASEID>_<TIMESTAMP>_<SEQ>

    # Parent Message Reference
    message_id = Column(
        String(100),
        ForeignKey("messages.message_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Conversation Context (denormalized for faster queries)
    conversation_id = Column(String(100), nullable=False, index=True)

    # Tags (JSON array of fixed tag values)
    # Valid tags: "Key", "Timeline", "Privileged", "WorkProduct"
    tags = Column(Text, nullable=False)  # JSON array

    # Free-form Note (work product)
    note = Column(Text)  # Max length enforced in application layer

    # Attribution and Timestamps
    created_by = Column(String(255), nullable=False)  # Email or username
    created_at = Column(Integer, nullable=False)  # Unix timestamp
    updated_by = Column(String(255))  # Email or username
    updated_at = Column(Integer)  # Unix timestamp

    # Relationships
    message = relationship("Message", back_populates="annotations")
    audit_entries = relationship(
        "AnnotationAudit",
        back_populates="annotation",
        cascade="all, delete-orphan",
        order_by="AnnotationAudit.changed_at.desc()",
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_annotation_conversation", "conversation_id", "created_at"),
        Index("idx_annotation_message", "message_id"),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.created_at:
            self.created_at = int(datetime.utcnow().timestamp())

    def get_tags(self) -> List[str]:
        """Parse tags from JSON."""
        if not self.tags:
            return []
        try:
            return json.loads(self.tags)
        except json.JSONDecodeError:
            return []

    def set_tags(self, tag_list: List[str]):
        """
        Store tags as JSON after validation.

        Args:
            tag_list: List of tag names

        Raises:
            ValueError: If any tag is invalid
        """
        valid_tags = ANNOTATION_CONFIG["tags"]
        invalid_tags = [t for t in tag_list if t not in valid_tags]
        if invalid_tags:
            raise ValueError(
                f"Invalid tags: {invalid_tags}. Valid tags: {valid_tags}"
            )

        self.tags = json.dumps(tag_list)

    def validate_note_length(self) -> bool:
        """Check if note length is within limits."""
        if not self.note:
            return True
        max_length = ANNOTATION_CONFIG["note_max_length"]
        return len(self.note) <= max_length

    def has_tag(self, tag: str) -> bool:
        """Check if annotation has a specific tag."""
        return tag in self.get_tags()

    def get_created_datetime(self) -> datetime:
        """Convert created_at timestamp to datetime (UTC)."""
        return datetime.utcfromtimestamp(self.created_at)

    def get_updated_datetime(self) -> Optional[datetime]:
        """Convert updated_at timestamp to datetime (UTC)."""
        if not self.updated_at:
            return None
        return datetime.utcfromtimestamp(self.updated_at)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "annotation_id": self.annotation_id,
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "tags": self.get_tags(),
            "note": self.note,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "created_at_iso": self.get_created_datetime().isoformat() + "Z",
            "updated_by": self.updated_by,
            "updated_at": self.updated_at,
            "updated_at_iso": (
                self.get_updated_datetime().isoformat() + "Z"
                if self.updated_at
                else None
            ),
        }

    def __repr__(self):
        tags_str = ", ".join(self.get_tags())
        return (
            f"<Annotation(id={self.annotation_id}, "
            f"message={self.message_id}, "
            f"tags=[{tags_str}], "
            f"created_by={self.created_by})>"
        )


class AnnotationAudit(Base):
    """
    Immutable audit log of all annotation changes.
    Provides complete chain of custody for work product.
    """

    __tablename__ = "annotation_audit"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Annotation Reference
    annotation_id = Column(String(100), nullable=False, index=True)
    # Note: Not a foreign key to preserve audit trail even if annotation deleted

    # Action Type
    action = Column(String(50), nullable=False)  # 'CREATE', 'UPDATE', 'DELETE'

    # Snapshot Before/After
    old_value = Column(Text)  # JSON snapshot before change (null for CREATE)
    new_value = Column(Text)  # JSON snapshot after change (null for DELETE)

    # Attribution
    changed_by = Column(String(255), nullable=False)  # Email or username
    changed_at = Column(Integer, nullable=False, index=True)  # Unix timestamp

    # Relationship
    annotation = relationship("Annotation", back_populates="audit_entries")

    # Indexes for performance
    __table_args__ = (Index("idx_audit_annotation_time", "annotation_id", "changed_at"),)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.changed_at:
            self.changed_at = int(datetime.utcnow().timestamp())

    def get_old_value(self) -> Optional[dict]:
        """Parse old value from JSON."""
        if not self.old_value:
            return None
        try:
            return json.loads(self.old_value)
        except json.JSONDecodeError:
            return None

    def set_old_value(self, value_dict: Optional[dict]):
        """Store old value as JSON."""
        if value_dict is None:
            self.old_value = None
        else:
            self.old_value = json.dumps(value_dict)

    def get_new_value(self) -> Optional[dict]:
        """Parse new value from JSON."""
        if not self.new_value:
            return None
        try:
            return json.loads(self.new_value)
        except json.JSONDecodeError:
            return None

    def set_new_value(self, value_dict: Optional[dict]):
        """Store new value as JSON."""
        if value_dict is None:
            self.new_value = None
        else:
            self.new_value = json.dumps(value_dict)

    def get_changed_datetime(self) -> datetime:
        """Convert changed_at timestamp to datetime (UTC)."""
        return datetime.utcfromtimestamp(self.changed_at)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "annotation_id": self.annotation_id,
            "action": self.action,
            "old_value": self.get_old_value(),
            "new_value": self.get_new_value(),
            "changed_by": self.changed_by,
            "changed_at": self.changed_at,
            "changed_at_iso": self.get_changed_datetime().isoformat() + "Z",
        }

    def __repr__(self):
        return (
            f"<AnnotationAudit(id={self.id}, "
            f"annotation={self.annotation_id}, "
            f"action={self.action}, "
            f"changed_by={self.changed_by}, "
            f"changed_at={self.get_changed_datetime()})>"
        )
