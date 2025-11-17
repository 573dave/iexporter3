"""
ID Generation Utilities
Forensically stable ID generation for messages, annotations, attachments, and exports
"""

import hashlib
import logging
import re
from datetime import datetime
from typing import Optional, Dict, Any

from backend.config import MESSAGE_ID_FORMAT

logger = logging.getLogger("iexporter3.utils.id_generator")


def generate_message_id(
    case_id: str,
    extraction_timestamp: int,
    conversation_hash: str,
    sequence: int,
) -> str:
    """
    Generate stable, unique message ID.

    Format: MSG_<CASEID>_<EXTRACTION_TS>_<CONV_HASH>_<SEQ>
    Example: MSG_ABC2024_20241117120000_A3F2B91C_00001

    Args:
        case_id: Case identifier (max 20 chars, alphanumeric)
        extraction_timestamp: Unix timestamp of extraction
        conversation_hash: SHA-256 hash of conversation identifier
        sequence: Sequential message number (1-based)

    Returns:
        Message ID string

    Raises:
        ValueError: If parameters are invalid
    """
    # Validate case_id
    if not case_id or len(case_id) > MESSAGE_ID_FORMAT["case_id_max_length"]:
        raise ValueError(
            f"Invalid case_id: must be 1-{MESSAGE_ID_FORMAT['case_id_max_length']} chars"
        )

    # Sanitize case_id (alphanumeric only)
    case_id_clean = re.sub(r"[^A-Za-z0-9]", "", case_id)

    # Format extraction timestamp
    extraction_dt = datetime.utcfromtimestamp(extraction_timestamp)
    timestamp_str = extraction_dt.strftime(MESSAGE_ID_FORMAT["timestamp_format"])

    # Truncate conversation hash to first N characters
    conv_hash_short = conversation_hash[: MESSAGE_ID_FORMAT["hash_length"]].upper()

    # Format sequence number with zero padding
    seq_digits = MESSAGE_ID_FORMAT["sequence_digits"]
    sequence_str = str(sequence).zfill(seq_digits)

    # Combine components
    sep = MESSAGE_ID_FORMAT["separator"]
    prefix = MESSAGE_ID_FORMAT["prefix"]

    message_id = f"{prefix}{sep}{case_id_clean}{sep}{timestamp_str}{sep}{conv_hash_short}{sep}{sequence_str}"

    logger.debug(f"Generated message ID: {message_id}")

    return message_id


def generate_annotation_id(case_id: str, timestamp: int, sequence: int) -> str:
    """
    Generate stable, unique annotation ID.

    Format: ANN_<CASEID>_<TIMESTAMP>_<SEQ>
    Example: ANN_ABC2024_20241117143000_00001

    Args:
        case_id: Case identifier
        timestamp: Unix timestamp when annotation created
        sequence: Sequential annotation number (1-based)

    Returns:
        Annotation ID string
    """
    # Sanitize case_id
    case_id_clean = re.sub(r"[^A-Za-z0-9]", "", case_id)

    # Format timestamp
    dt = datetime.utcfromtimestamp(timestamp)
    timestamp_str = dt.strftime("%Y%m%d%H%M%S")

    # Format sequence
    sequence_str = str(sequence).zfill(5)

    annotation_id = f"ANN_{case_id_clean}_{timestamp_str}_{sequence_str}"

    logger.debug(f"Generated annotation ID: {annotation_id}")

    return annotation_id


def generate_attachment_id(case_id: str, extraction_timestamp: int, sequence: int) -> str:
    """
    Generate stable, unique attachment ID.

    Format: ATT_<CASEID>_<EXTRACTION_TS>_<SEQ>
    Example: ATT_ABC2024_20241117120000_00001

    Args:
        case_id: Case identifier
        extraction_timestamp: Unix timestamp of extraction
        sequence: Sequential attachment number (1-based)

    Returns:
        Attachment ID string
    """
    # Sanitize case_id
    case_id_clean = re.sub(r"[^A-Za-z0-9]", "", case_id)

    # Format timestamp
    dt = datetime.utcfromtimestamp(extraction_timestamp)
    timestamp_str = dt.strftime("%Y%m%d%H%M%S")

    # Format sequence
    sequence_str = str(sequence).zfill(5)

    attachment_id = f"ATT_{case_id_clean}_{timestamp_str}_{sequence_str}"

    logger.debug(f"Generated attachment ID: {attachment_id}")

    return attachment_id


def generate_export_id(case_id: str, export_timestamp: int) -> str:
    """
    Generate stable, unique export ID.

    Format: EXP_<CASEID>_<EXPORT_TS>
    Example: EXP_ABC2024_20241117150000

    Args:
        case_id: Case identifier
        export_timestamp: Unix timestamp of export

    Returns:
        Export ID string
    """
    # Sanitize case_id
    case_id_clean = re.sub(r"[^A-Za-z0-9]", "", case_id)

    # Format timestamp
    dt = datetime.utcfromtimestamp(export_timestamp)
    timestamp_str = dt.strftime("%Y%m%d%H%M%S")

    export_id = f"EXP_{case_id_clean}_{timestamp_str}"

    logger.debug(f"Generated export ID: {export_id}")

    return export_id


def generate_conversation_hash(conversation_identifier: str) -> str:
    """
    Generate deterministic hash for a conversation.

    Args:
        conversation_identifier: Unique conversation identifier
                                (e.g., phone number, chat ID)

    Returns:
        SHA-256 hash (64 characters)
    """
    hash_obj = hashlib.sha256()
    hash_obj.update(conversation_identifier.encode("utf-8"))
    conv_hash = hash_obj.hexdigest()

    logger.debug(
        f"Conversation hash: {conversation_identifier[:20]}... -> {conv_hash[:16]}..."
    )

    return conv_hash


def parse_message_id(message_id: str) -> Optional[Dict[str, Any]]:
    """
    Parse components from a message ID.

    Args:
        message_id: Message ID string (e.g., MSG_ABC2024_20241117120000_A3F2B91C_00001)

    Returns:
        Dictionary with parsed components:
        {
            'prefix': 'MSG',
            'case_id': 'ABC2024',
            'extraction_timestamp': '20241117120000',
            'conversation_hash': 'A3F2B91C',
            'sequence': 1
        }
        Returns None if ID format is invalid
    """
    # Pattern: MSG_<CASEID>_<TIMESTAMP>_<HASH>_<SEQ>
    pattern = r"^MSG_([A-Za-z0-9]+)_(\d{14})_([A-Fa-f0-9]{8})_(\d{5})$"
    match = re.match(pattern, message_id)

    if not match:
        logger.warning(f"Invalid message ID format: {message_id}")
        return None

    components = {
        "prefix": "MSG",
        "case_id": match.group(1),
        "extraction_timestamp": match.group(2),
        "conversation_hash": match.group(3),
        "sequence": int(match.group(4)),
    }

    logger.debug(f"Parsed message ID: {message_id} -> {components}")

    return components


def validate_message_id(message_id: str) -> bool:
    """
    Validate message ID format.

    Args:
        message_id: Message ID string

    Returns:
        True if valid format, False otherwise
    """
    return parse_message_id(message_id) is not None


if __name__ == "__main__":
    # Test ID generation
    import time

    print("Testing ID Generation Utilities")
    print("=" * 50)

    # Test message ID generation
    case_id = "ABC2024"
    extraction_ts = int(time.time())
    conversation_id = "+15551234567"
    conv_hash = generate_conversation_hash(conversation_id)

    msg_id = generate_message_id(case_id, extraction_ts, conv_hash, 1)
    print(f"Message ID: {msg_id}")

    # Validate and parse
    is_valid = validate_message_id(msg_id)
    print(f"Valid format: {is_valid}")

    parsed = parse_message_id(msg_id)
    print(f"Parsed components: {parsed}")

    # Test annotation ID
    ann_id = generate_annotation_id(case_id, extraction_ts, 1)
    print(f"\nAnnotation ID: {ann_id}")

    # Test attachment ID
    att_id = generate_attachment_id(case_id, extraction_ts, 1)
    print(f"Attachment ID: {att_id}")

    # Test export ID
    exp_id = generate_export_id(case_id, extraction_ts)
    print(f"Export ID: {exp_id}")

    # Test conversation hash stability
    print(f"\nConversation hash stability test:")
    hash1 = generate_conversation_hash(conversation_id)
    hash2 = generate_conversation_hash(conversation_id)
    print(f"Hash 1: {hash1}")
    print(f"Hash 2: {hash2}")
    print(f"Stable: {hash1 == hash2}")

    # Test message ID stability (same inputs)
    msg_id_1 = generate_message_id(case_id, extraction_ts, conv_hash, 1)
    msg_id_2 = generate_message_id(case_id, extraction_ts, conv_hash, 1)
    print(f"\nMessage ID stability test:")
    print(f"ID 1: {msg_id_1}")
    print(f"ID 2: {msg_id_2}")
    print(f"Stable: {msg_id_1 == msg_id_2}")

    print("\nAll ID generation utilities tested successfully!")
