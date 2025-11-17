"""
iMessage Extractor
Forensic extraction from macOS iMessage database (chat.db)
"""

import logging
import sqlite3
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
import shutil

from sqlalchemy.orm import Session

from backend.extractors.base_extractor import BaseExtractor
from backend.models import Message, Attachment
from backend.utils import (
    generate_message_id,
    generate_attachment_id,
    generate_conversation_hash,
    hash_message,
    hash_file,
)
from backend.config import (
    IMESSAGE_DB_PATH,
    IMESSAGE_ATTACHMENTS_PATH,
    ATTACHMENTS_DIR,
    EXPORT_CONFIG,
)

logger = logging.getLogger("iexporter3.extractors.imessage")


class iMessageExtractor(BaseExtractor):
    """
    Extract messages and attachments from macOS iMessage database.

    macOS iMessage Database Structure (chat.db):
    - message table: Contains message text, timestamps, and metadata
    - handle table: Contains participant information (phone/email)
    - chat table: Contains conversation information
    - chat_message_join: Links messages to conversations
    - attachment table: Contains file attachment metadata
    - message_attachment_join: Links messages to attachments

    Apple Timestamp Format:
    - iMessage uses Cocoa/Apple timestamps (seconds since 2001-01-01)
    - Must convert to Unix timestamps (seconds since 1970-01-01)
    """

    # Apple timestamp epoch offset (seconds between 1970 and 2001)
    APPLE_TIMESTAMP_OFFSET = 978307200

    def __init__(
        self,
        case_id: str,
        output_db_path: Optional[str] = None,
        user: str = "system",
        source_db_path: Optional[Path] = None,
    ):
        """
        Initialize iMessage extractor.

        Args:
            case_id: Case identifier
            output_db_path: Path to output database
            user: User performing extraction
            source_db_path: Custom source database path (default: macOS iMessage DB)
        """
        super().__init__(case_id, output_db_path, user)

        self._source_db_path = source_db_path or IMESSAGE_DB_PATH
        self.conversation_map: Dict[str, str] = {}  # chat_id -> conversation_hash
        self.message_sequence_counters: Dict[str, int] = {}  # conversation_hash -> counter

        logger.info(f"iMessage extractor initialized, source: {self._source_db_path}")

    def get_source_db_path(self) -> Path:
        """Get path to iMessage database."""
        return Path(self._source_db_path)

    @staticmethod
    def convert_apple_timestamp(apple_timestamp: Optional[int]) -> Optional[int]:
        """
        Convert Apple/Cocoa timestamp to Unix timestamp.

        Args:
            apple_timestamp: Seconds since 2001-01-01 (can be None)

        Returns:
            Unix timestamp (seconds since 1970-01-01) or None
        """
        if apple_timestamp is None:
            return None

        # Apple timestamps are in nanoseconds in some versions, check magnitude
        if apple_timestamp > 1e12:
            apple_timestamp = apple_timestamp / 1e9

        unix_timestamp = int(apple_timestamp + iMessageExtractor.APPLE_TIMESTAMP_OFFSET)
        return unix_timestamp

    def get_conversation_identifier(
        self,
        source_conn: sqlite3.Connection,
        chat_id: int,
    ) -> Tuple[str, str]:
        """
        Get conversation identifier and generate hash.

        Args:
            source_conn: Connection to source iMessage database
            chat_id: Chat ID from iMessage database

        Returns:
            Tuple of (conversation_id_string, conversation_hash)
        """
        # Check cache first
        if chat_id in self.conversation_map:
            cached_hash = self.conversation_map[chat_id]
            return f"CHAT_{chat_id}", cached_hash

        # Query chat table for conversation details
        cursor = source_conn.cursor()
        cursor.execute(
            """
            SELECT chat_identifier, display_name, service_name
            FROM chat
            WHERE ROWID = ?
            """,
            (chat_id,),
        )
        row = cursor.fetchone()

        if row:
            chat_identifier, display_name, service_name = row
            conversation_id = chat_identifier or f"CHAT_{chat_id}"
        else:
            conversation_id = f"CHAT_{chat_id}"

        # Generate stable hash
        conv_hash = generate_conversation_hash(conversation_id)

        # Cache the mapping
        self.conversation_map[chat_id] = conv_hash

        logger.debug(f"Conversation {chat_id} -> {conversation_id} -> {conv_hash[:8]}...")

        return conversation_id, conv_hash

    def get_next_message_sequence(self, conversation_hash: str) -> int:
        """
        Get next message sequence number for a conversation.

        Args:
            conversation_hash: Hash of conversation identifier

        Returns:
            Next sequence number (1-based)
        """
        if conversation_hash not in self.message_sequence_counters:
            self.message_sequence_counters[conversation_hash] = 0

        self.message_sequence_counters[conversation_hash] += 1
        return self.message_sequence_counters[conversation_hash]

    def extract_messages(self, session: Session) -> int:
        """
        Extract all messages from iMessage database.

        Args:
            session: SQLAlchemy session for output database

        Returns:
            Number of messages extracted
        """
        logger.info("Connecting to iMessage database...")

        # Connect to source database (read-only)
        source_conn = sqlite3.connect(f"file:{self._source_db_path}?mode=ro", uri=True)
        source_cursor = source_conn.cursor()

        # Query messages with conversation and participant information
        query = """
        SELECT
            m.ROWID as message_rowid,
            m.text as message_text,
            m.date as apple_timestamp,
            m.is_from_me,
            m.is_read,
            m.service as service_name,
            h.id as sender_id,
            h.uncanonicalized_id as sender_name,
            c.ROWID as chat_id,
            c.chat_identifier as conversation_id,
            m.cache_has_attachments as has_attachment
        FROM message m
        LEFT JOIN handle h ON m.handle_id = h.ROWID
        LEFT JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
        LEFT JOIN chat c ON cmj.chat_id = c.ROWID
        ORDER BY m.date ASC
        """

        logger.info("Querying messages...")
        source_cursor.execute(query)

        message_count = 0
        batch_messages = []
        batch_size = 1000

        for row in source_cursor.fetchall():
            (
                message_rowid,
                message_text,
                apple_timestamp,
                is_from_me,
                is_read,
                service_name,
                sender_id,
                sender_name,
                chat_id,
                conversation_id_str,
                has_attachment,
            ) = row

            # Convert timestamp
            unix_timestamp = self.convert_apple_timestamp(apple_timestamp)
            if unix_timestamp is None:
                logger.warning(f"Skipping message {message_rowid}: invalid timestamp")
                continue

            # Get conversation hash
            if chat_id:
                conv_id, conv_hash = self.get_conversation_identifier(source_conn, chat_id)
            else:
                conv_id = "UNKNOWN"
                conv_hash = generate_conversation_hash(conv_id)

            # Generate message ID
            sequence = self.get_next_message_sequence(conv_hash)
            message_id = generate_message_id(
                case_id=self.case_id,
                extraction_timestamp=self.extraction_timestamp,
                conversation_hash=conv_hash,
                sequence=sequence,
            )

            # Calculate message hash
            msg_hash = hash_message(
                message_text=message_text,
                sender_id=sender_id or "unknown",
                timestamp=unix_timestamp,
                service_name=service_name or "iMessage",
            )

            # Determine sender name
            if is_from_me:
                final_sender_name = "Me"
                final_sender_id = "me"
            else:
                final_sender_name = sender_name or sender_id or "Unknown"
                final_sender_id = sender_id or "unknown"

            # Create message object
            message = Message(
                message_id=message_id,
                conversation_id=conv_id,
                sender_id=final_sender_id,
                sender_name=final_sender_name,
                message_text=message_text,
                timestamp=unix_timestamp,
                timezone="UTC",  # Will improve timezone detection in future
                has_attachment=bool(has_attachment),
                message_type="text" if not has_attachment else "attachment",
                service_name=service_name or "iMessage",
                is_from_me=bool(is_from_me),
                read_receipt=bool(is_read),
                hash=msg_hash,
                extraction_timestamp=self.extraction_timestamp,
                part_number=1,  # Will handle multi-part splitting in export phase
                sequence_in_part=sequence,
            )

            batch_messages.append(message)
            message_count += 1

            # Batch insert for performance
            if len(batch_messages) >= batch_size:
                session.bulk_save_objects(batch_messages)
                session.commit()
                logger.info(f"Inserted {message_count} messages...")
                batch_messages = []

        # Insert remaining messages
        if batch_messages:
            session.bulk_save_objects(batch_messages)
            session.commit()

        # Update conversation count
        self.stats["total_conversations"] = len(self.conversation_map)

        source_conn.close()
        logger.info(f"Message extraction complete: {message_count} messages extracted")

        return message_count

    def extract_attachments(self, session: Session) -> int:
        """
        Extract attachment metadata and copy files.

        Args:
            session: SQLAlchemy session for output database

        Returns:
            Number of attachments extracted
        """
        logger.info("Extracting attachments...")

        # Create attachment directories
        attachments_original_dir = ATTACHMENTS_DIR / "original"
        attachments_thumb_dir = ATTACHMENTS_DIR / "thumbs"
        attachments_original_dir.mkdir(parents=True, exist_ok=True)
        attachments_thumb_dir.mkdir(parents=True, exist_ok=True)

        # Connect to source database
        source_conn = sqlite3.connect(f"file:{self._source_db_path}?mode=ro", uri=True)
        source_cursor = source_conn.cursor()

        # Query attachments with associated messages
        query = """
        SELECT
            a.ROWID as attachment_rowid,
            a.filename as file_path,
            a.mime_type,
            a.total_bytes as file_size,
            maj.message_id
        FROM attachment a
        LEFT JOIN message_attachment_join maj ON a.ROWID = maj.attachment_id
        WHERE a.filename IS NOT NULL
        ORDER BY a.ROWID ASC
        """

        source_cursor.execute(query)

        attachment_count = 0
        attachment_sequence = 0

        for row in source_cursor.fetchall():
            attachment_rowid, file_path, mime_type, file_size, message_rowid = row

            # Skip if no file path
            if not file_path:
                continue

            # Resolve full file path (iMessage stores relative paths)
            if file_path.startswith("~"):
                full_path = Path(file_path).expanduser()
            elif file_path.startswith("/"):
                full_path = Path(file_path)
            else:
                # Relative to attachments directory
                full_path = IMESSAGE_ATTACHMENTS_PATH / file_path

            # Skip if file doesn't exist
            if not full_path.exists():
                logger.warning(f"Attachment file not found: {full_path}")
                continue

            # Generate attachment ID
            attachment_sequence += 1
            attachment_id = generate_attachment_id(
                case_id=self.case_id,
                extraction_timestamp=self.extraction_timestamp,
                sequence=attachment_sequence,
            )

            # Find corresponding message ID in our database
            if message_rowid:
                # Query our database for the message
                # Note: This requires knowing the message_id, which we'll need to map
                # For now, we'll store message_rowid and resolve later
                # This is a simplification; production code would maintain a rowid -> message_id map
                message_id_query = (
                    session.query(Message)
                    .filter(Message.sequence_in_part == message_rowid)
                    .first()
                )
                if message_id_query:
                    parent_message_id = message_id_query.message_id
                else:
                    # Skip attachment if we can't find parent message
                    logger.warning(
                        f"Could not find parent message for attachment {attachment_rowid}"
                    )
                    continue
            else:
                logger.warning(
                    f"Attachment {attachment_rowid} has no associated message"
                )
                continue

            # Copy original file
            original_filename = full_path.name
            destination_filename = f"{attachment_id}_{original_filename}"
            destination_path = attachments_original_dir / destination_filename

            try:
                shutil.copy2(full_path, destination_path)
                logger.debug(f"Copied attachment: {original_filename}")
            except Exception as e:
                logger.error(f"Failed to copy attachment {original_filename}: {e}")
                continue

            # Calculate file hash
            try:
                file_hash = hash_file(destination_path)
            except Exception as e:
                logger.error(f"Failed to hash attachment {destination_filename}: {e}")
                continue

            # Create attachment record
            attachment = Attachment(
                attachment_id=attachment_id,
                message_id=parent_message_id,
                original_filename=original_filename,
                mime_type=mime_type,
                file_size=file_size or destination_path.stat().st_size,
                hash=file_hash,
                original_path=f"attachments/original/{destination_filename}",
                thumbnail_path=f"attachments/thumbs/{attachment_id}_thumb.jpg",  # TODO: Generate thumbnails
            )

            session.add(attachment)
            attachment_count += 1

            # Commit in batches
            if attachment_count % 100 == 0:
                session.commit()
                logger.info(f"Extracted {attachment_count} attachments...")

        # Final commit
        session.commit()

        source_conn.close()
        logger.info(f"Attachment extraction complete: {attachment_count} attachments")

        return attachment_count


if __name__ == "__main__":
    # Test iMessage extraction
    print("Testing iMessage Extractor")
    print("=" * 50)

    # Create test extractor
    extractor = iMessageExtractor(
        case_id="TEST2024",
        user="test.user@example.com",
    )

    # Check if iMessage database exists
    if not extractor.validate_source():
        print(f"⚠️  iMessage database not found at: {IMESSAGE_DB_PATH}")
        print("This is expected on non-macOS systems or without Full Disk Access.")
        print("\nTo test extraction:")
        print("1. Run on macOS with Full Disk Access enabled")
        print("2. Or provide a test iMessage database with source_db_path parameter")
    else:
        print(f"✓ iMessage database found: {IMESSAGE_DB_PATH}")
        print("\nReady for extraction. Run extractor.extract() to begin.")
