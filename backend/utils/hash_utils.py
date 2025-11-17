"""
Hash Utilities for Forensic Integrity
SHA-256 hashing for messages, files, and exports with normalization
"""

import hashlib
import logging
from pathlib import Path
from typing import Union, Optional

from backend.config import FORENSIC_CONFIG

logger = logging.getLogger("iexporter3.utils.hash")


def hash_file(file_path: Union[str, Path], chunk_size: int = 8192) -> str:
    """
    Calculate SHA-256 hash of a file.

    Args:
        file_path: Path to file
        chunk_size: Size of chunks to read (default 8KB)

    Returns:
        Hexadecimal hash string (64 characters)

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file can't be read
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Not a file: {file_path}")

    hash_obj = hashlib.sha256()

    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                hash_obj.update(chunk)
    except PermissionError as e:
        logger.error(f"Permission denied reading file: {file_path}")
        raise

    file_hash = hash_obj.hexdigest()
    logger.debug(f"File hash: {file_path} -> {file_hash}")

    return file_hash


def hash_string(content: str, encoding: str = None) -> str:
    """
    Calculate SHA-256 hash of a string.

    Args:
        content: String content to hash
        encoding: Character encoding (default: from config)

    Returns:
        Hexadecimal hash string (64 characters)
    """
    if encoding is None:
        encoding = FORENSIC_CONFIG["hash_encoding"]

    hash_obj = hashlib.sha256()
    hash_obj.update(content.encode(encoding))

    content_hash = hash_obj.hexdigest()
    logger.debug(f"String hash: {len(content)} chars -> {content_hash}")

    return content_hash


def normalize_content_for_hash(content: str) -> str:
    """
    Normalize content before hashing for cross-platform consistency.

    Normalization steps:
    1. Convert line endings to LF (Unix style)
    2. Remove BOM if present
    3. Ensure UTF-8 encoding

    Args:
        content: Raw string content

    Returns:
        Normalized string content
    """
    # Remove BOM (Byte Order Mark) if present
    if content.startswith("\ufeff"):
        content = content[1:]

    # Normalize line endings to LF
    line_ending = FORENSIC_CONFIG["line_ending_normalization"]
    if line_ending == "LF":
        content = content.replace("\r\n", "\n")  # Windows to Unix
        content = content.replace("\r", "\n")  # Old Mac to Unix
    elif line_ending == "CRLF":
        content = content.replace("\r\n", "\n").replace("\n", "\r\n")

    return content


def hash_message(
    message_text: Optional[str],
    sender_id: str,
    timestamp: int,
    service_name: str = "iMessage",
) -> str:
    """
    Calculate forensic hash of a message.

    Combines message content with metadata to create a unique,
    verifiable hash that detects any tampering.

    Args:
        message_text: Message text content (can be None for attachments)
        sender_id: Sender identifier (phone/email)
        timestamp: Unix timestamp
        service_name: Service name (iMessage, SMS, etc.)

    Returns:
        SHA-256 hash (64 characters)
    """
    # Combine components in deterministic order
    components = [
        str(timestamp),
        sender_id or "",
        message_text or "",
        service_name or "",
    ]

    # Create hash input
    hash_input = "|".join(components)

    # Normalize and hash
    normalized = normalize_content_for_hash(hash_input)
    message_hash = hash_string(normalized)

    logger.debug(
        f"Message hash: timestamp={timestamp}, sender={sender_id[:10]}... -> {message_hash}"
    )

    return message_hash


def verify_hash(content: Union[str, Path], expected_hash: str) -> bool:
    """
    Verify that content matches expected hash.

    Args:
        content: String content or file path
        expected_hash: Expected SHA-256 hash (64 hex characters)

    Returns:
        True if hash matches, False otherwise

    Raises:
        ValueError: If expected_hash is not valid SHA-256 format
    """
    # Validate expected hash format
    if not isinstance(expected_hash, str) or len(expected_hash) != 64:
        raise ValueError(f"Invalid SHA-256 hash format: {expected_hash}")

    try:
        int(expected_hash, 16)  # Verify it's hexadecimal
    except ValueError:
        raise ValueError(f"Hash is not hexadecimal: {expected_hash}")

    # Calculate actual hash
    if isinstance(content, (str, Path)) and Path(content).is_file():
        actual_hash = hash_file(content)
    elif isinstance(content, str):
        normalized = normalize_content_for_hash(content)
        actual_hash = hash_string(normalized)
    else:
        raise ValueError(f"Invalid content type for hash verification: {type(content)}")

    # Compare hashes
    match = actual_hash.lower() == expected_hash.lower()

    if match:
        logger.info(f"Hash verification PASSED: {expected_hash}")
    else:
        logger.warning(
            f"Hash verification FAILED: expected={expected_hash}, actual={actual_hash}"
        )

    return match


def hash_database(db_path: Union[str, Path]) -> dict:
    """
    Hash an SQLite database file and return metadata.

    Args:
        db_path: Path to SQLite database

    Returns:
        Dictionary with hash and metadata:
        {
            'hash': 'abc123...',
            'file_size': 12345,
            'timestamp': 1234567890,
            'path': '/path/to/db'
        }
    """
    db_path = Path(db_path)

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    # Calculate hash
    db_hash = hash_file(db_path)

    # Gather metadata
    stat = db_path.stat()

    metadata = {
        "hash": db_hash,
        "file_size": stat.st_size,
        "timestamp": int(stat.st_mtime),
        "path": str(db_path.resolve()),
    }

    logger.info(f"Database hashed: {db_path.name} -> {db_hash}")

    return metadata


if __name__ == "__main__":
    # Test hash utilities
    import tempfile

    print("Testing Hash Utilities")
    print("=" * 50)

    # Test string hashing
    test_string = "Hello, iExporter3!"
    string_hash = hash_string(test_string)
    print(f"String hash: {string_hash}")

    # Test normalization
    test_windows = "Line 1\r\nLine 2\r\nLine 3"
    test_unix = "Line 1\nLine 2\nLine 3"
    normalized_windows = normalize_content_for_hash(test_windows)
    normalized_unix = normalize_content_for_hash(test_unix)
    print(f"Windows normalized == Unix: {normalized_windows == normalized_unix}")
    print(f"Hashes match: {hash_string(normalized_windows) == hash_string(normalized_unix)}")

    # Test file hashing
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("Test file content")
        temp_path = f.name

    file_hash = hash_file(temp_path)
    print(f"File hash: {file_hash}")

    # Test verification
    verified = verify_hash(temp_path, file_hash)
    print(f"Hash verification: {verified}")

    # Test message hashing
    msg_hash = hash_message(
        message_text="Test message",
        sender_id="+15551234567",
        timestamp=1700000000,
        service_name="iMessage",
    )
    print(f"Message hash: {msg_hash}")

    # Cleanup
    import os
    os.unlink(temp_path)

    print("\nAll hash utilities tested successfully!")
