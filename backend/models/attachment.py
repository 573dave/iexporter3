"""
Attachment Model
Represents file attachments with forensic metadata and hash verification
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from backend.models.base import Base


class Attachment(Base):
    """
    File attachment (image, video, document, etc.) with forensic tracking.
    All files hashed with SHA-256 for integrity verification.
    """

    __tablename__ = "attachments"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Unique Attachment Identifier
    attachment_id = Column(String(100), unique=True, nullable=False, index=True)
    # Format: ATT_<CASEID>_<EXTRACTION_TS>_<SEQ>

    # Parent Message Reference
    message_id = Column(
        String(100),
        ForeignKey("messages.message_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # File Metadata
    original_filename = Column(String(500))
    mime_type = Column(String(100))
    file_size = Column(Integer)  # Bytes

    # Forensic Hash
    hash = Column(String(64), nullable=False)  # SHA-256 of original file

    # File Paths (relative to export root)
    original_path = Column(String(1000))  # Path to original file in export
    thumbnail_path = Column(String(1000))  # Path to thumbnail in export

    # Media Dimensions (for images/videos)
    width = Column(Integer)
    height = Column(Integer)

    # Creation Timestamp
    created_at = Column(Integer, nullable=False)

    # Relationship
    message = relationship("Message", back_populates="attachments")

    # Indexes
    __table_args__ = (Index("idx_attachment_message", "message_id", "attachment_id"),)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.created_at:
            self.created_at = int(datetime.utcnow().timestamp())

    def get_file_extension(self) -> str:
        """Extract file extension from original filename."""
        if not self.original_filename:
            return ""
        return Path(self.original_filename).suffix.lower()

    def is_image(self) -> bool:
        """Check if attachment is an image based on MIME type."""
        if not self.mime_type:
            return False
        return self.mime_type.startswith("image/")

    def is_video(self) -> bool:
        """Check if attachment is a video based on MIME type."""
        if not self.mime_type:
            return False
        return self.mime_type.startswith("video/")

    def is_audio(self) -> bool:
        """Check if attachment is audio based on MIME type."""
        if not self.mime_type:
            return False
        return self.mime_type.startswith("audio/")

    def is_document(self) -> bool:
        """Check if attachment is a document."""
        if not self.mime_type:
            return False
        document_types = [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument",
            "text/",
        ]
        return any(self.mime_type.startswith(dt) for dt in document_types)

    def get_human_readable_size(self) -> str:
        """Convert file size to human-readable format."""
        if not self.file_size:
            return "Unknown"

        size = self.file_size
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "attachment_id": self.attachment_id,
            "message_id": self.message_id,
            "original_filename": self.original_filename,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "file_size_human": self.get_human_readable_size(),
            "hash": self.hash,
            "original_path": self.original_path,
            "thumbnail_path": self.thumbnail_path,
            "width": self.width,
            "height": self.height,
            "is_image": self.is_image(),
            "is_video": self.is_video(),
            "is_audio": self.is_audio(),
            "is_document": self.is_document(),
        }

    def __repr__(self):
        return (
            f"<Attachment(id={self.attachment_id}, "
            f"filename={self.original_filename}, "
            f"size={self.get_human_readable_size()}, "
            f"type={self.mime_type})>"
        )
