"""
Database Models for iExporter3
SQLAlchemy ORM models for forensic message extraction and annotation
"""

from backend.models.base import Base, get_engine, get_session, init_database
from backend.models.message import Message
from backend.models.attachment import Attachment
from backend.models.annotation import Annotation, AnnotationAudit
from backend.models.metadata import ExtractionMetadata, ExportMetadata

__all__ = [
    "Base",
    "get_engine",
    "get_session",
    "init_database",
    "Message",
    "Attachment",
    "Annotation",
    "AnnotationAudit",
    "ExtractionMetadata",
    "ExportMetadata",
]
