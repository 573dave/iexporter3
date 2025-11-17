"""
Metadata Models
Extraction and export metadata for forensic chain of custody
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Index,
)

from backend.models.base import Base


class ExtractionMetadata(Base):
    """
    Metadata about the extraction process.
    Provides forensic documentation of the extraction operation.
    """

    __tablename__ = "extraction_metadata"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Case Information
    case_id = Column(String(100), nullable=False, index=True)

    # Extraction Details
    extraction_timestamp = Column(Integer, nullable=False)  # Unix timestamp
    extractor_name = Column(String(255))  # User or system performing extraction
    extractor_version = Column(String(50))  # Tool version

    # Source Database Information
    source_db_path = Column(String(1000))  # Path to original iMessage database
    source_db_hash = Column(String(64), nullable=False)  # SHA-256 of source DB

    # Extraction Statistics
    total_messages = Column(Integer, default=0)
    total_attachments = Column(Integer, default=0)
    total_conversations = Column(Integer, default=0)

    # Configuration (JSON)
    extraction_config = Column(Text)  # JSON of extraction parameters

    # Creation Timestamp
    created_at = Column(Integer, nullable=False)

    # Indexes
    __table_args__ = (Index("idx_extraction_case", "case_id", "extraction_timestamp"),)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.created_at:
            self.created_at = int(datetime.utcnow().timestamp())

    def get_extraction_datetime(self) -> datetime:
        """Convert extraction timestamp to datetime (UTC)."""
        return datetime.utcfromtimestamp(self.extraction_timestamp)

    def get_extraction_config(self) -> Optional[Dict[str, Any]]:
        """Parse extraction configuration from JSON."""
        if not self.extraction_config:
            return None
        try:
            return json.loads(self.extraction_config)
        except json.JSONDecodeError:
            return None

    def set_extraction_config(self, config_dict: Dict[str, Any]):
        """Store extraction configuration as JSON."""
        self.extraction_config = json.dumps(config_dict, indent=2)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "case_id": self.case_id,
            "extraction_timestamp": self.extraction_timestamp,
            "extraction_timestamp_iso": self.get_extraction_datetime().isoformat()
            + "Z",
            "extractor_name": self.extractor_name,
            "extractor_version": self.extractor_version,
            "source_db_path": self.source_db_path,
            "source_db_hash": self.source_db_hash,
            "total_messages": self.total_messages,
            "total_attachments": self.total_attachments,
            "total_conversations": self.total_conversations,
            "extraction_config": self.get_extraction_config(),
        }

    def __repr__(self):
        return (
            f"<ExtractionMetadata(case={self.case_id}, "
            f"timestamp={self.get_extraction_datetime()}, "
            f"messages={self.total_messages}, "
            f"attachments={self.total_attachments})>"
        )


class ExportMetadata(Base):
    """
    Metadata about export operations.
    Tracks all exports for forensic documentation and chain of custody.
    """

    __tablename__ = "export_metadata"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Export Identifier
    export_id = Column(String(100), unique=True, nullable=False, index=True)
    # Format: EXP_<CASEID>_<TIMESTAMP>

    # Export Details
    export_timestamp = Column(Integer, nullable=False)  # Unix timestamp
    export_type = Column(String(50), nullable=False)  # 'clean', 'annotated', 'report'
    exported_by = Column(String(255), nullable=False)  # User performing export

    # Case and Conversation Context
    case_id = Column(String(100), nullable=False, index=True)
    conversation_id = Column(String(100))  # Null if exporting all conversations
    part_number = Column(Integer)  # Conversation part number (for multi-part)
    total_parts = Column(Integer)  # Total number of parts

    # Export Statistics
    message_count = Column(Integer, default=0)
    annotation_count = Column(Integer, default=0)

    # Forensic Hash
    export_hash = Column(String(64), nullable=False)  # SHA-256 of export package

    # Creation Timestamp
    created_at = Column(Integer, nullable=False)

    # Indexes
    __table_args__ = (
        Index("idx_export_case_type", "case_id", "export_type", "export_timestamp"),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.created_at:
            self.created_at = int(datetime.utcnow().timestamp())

    def get_export_datetime(self) -> datetime:
        """Convert export timestamp to datetime (UTC)."""
        return datetime.utcfromtimestamp(self.export_timestamp)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "export_id": self.export_id,
            "export_timestamp": self.export_timestamp,
            "export_timestamp_iso": self.get_export_datetime().isoformat() + "Z",
            "export_type": self.export_type,
            "exported_by": self.exported_by,
            "case_id": self.case_id,
            "conversation_id": self.conversation_id,
            "part_number": self.part_number,
            "total_parts": self.total_parts,
            "message_count": self.message_count,
            "annotation_count": self.annotation_count,
            "export_hash": self.export_hash,
        }

    def __repr__(self):
        return (
            f"<ExportMetadata(id={self.export_id}, "
            f"type={self.export_type}, "
            f"case={self.case_id}, "
            f"timestamp={self.get_export_datetime()})>"
        )
