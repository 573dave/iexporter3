"""
Utility Functions for iExporter3
Forensic utilities, hashing, ID generation, and helpers
"""

from backend.utils.hash_utils import (
    hash_file,
    hash_string,
    hash_message,
    verify_hash,
    normalize_content_for_hash,
)
from backend.utils.id_generator import (
    generate_message_id,
    generate_annotation_id,
    generate_attachment_id,
    generate_export_id,
    parse_message_id,
)
from backend.utils.audit_logger import AuditLogger

__all__ = [
    "hash_file",
    "hash_string",
    "hash_message",
    "verify_hash",
    "normalize_content_for_hash",
    "generate_message_id",
    "generate_annotation_id",
    "generate_attachment_id",
    "generate_export_id",
    "parse_message_id",
    "AuditLogger",
]
