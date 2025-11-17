"""
Base Extractor Class
Abstract base class for all message extractors with forensic requirements
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import time

from sqlalchemy.orm import Session

from backend.models import (
    get_session,
    init_database,
    ExtractionMetadata,
)
from backend.utils import AuditLogger, hash_file
from backend.config import FORENSIC_CONFIG, DATABASE_DIR

logger = logging.getLogger("iexporter3.extractors")


class BaseExtractor(ABC):
    """
    Abstract base class for message extractors.
    Enforces forensic requirements and provides common functionality.
    """

    def __init__(
        self,
        case_id: str,
        output_db_path: Optional[str] = None,
        user: str = "system",
    ):
        """
        Initialize extractor.

        Args:
            case_id: Case identifier
            output_db_path: Path to output database (auto-generated if None)
            user: User performing extraction
        """
        self.case_id = case_id
        self.user = user
        self.extraction_timestamp = int(datetime.utcnow().timestamp())

        # Set up output database path
        if output_db_path is None:
            timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            db_filename = f"case_{case_id}_{timestamp_str}.db"
            self.output_db_path = str(DATABASE_DIR / db_filename)
        else:
            self.output_db_path = output_db_path

        # Initialize audit logger
        self.audit_logger = AuditLogger(case_id=case_id, user=user)

        # Statistics
        self.stats = {
            "total_messages": 0,
            "total_attachments": 0,
            "total_conversations": 0,
            "extraction_errors": 0,
            "start_time": None,
            "end_time": None,
            "duration_seconds": None,
        }

        # Database session (initialized during extraction)
        self.session: Optional[Session] = None

        logger.info(
            f"Initialized {self.__class__.__name__} for case {case_id}, "
            f"output: {self.output_db_path}"
        )

    @abstractmethod
    def get_source_db_path(self) -> Path:
        """
        Get path to source database.

        Returns:
            Path to source database file

        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def extract_messages(self, session: Session) -> int:
        """
        Extract messages from source database.

        Args:
            session: SQLAlchemy session for output database

        Returns:
            Number of messages extracted

        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def extract_attachments(self, session: Session) -> int:
        """
        Extract attachments from source.

        Args:
            session: SQLAlchemy session for output database

        Returns:
            Number of attachments extracted

        Must be implemented by subclasses.
        """
        pass

    def validate_source(self) -> bool:
        """
        Validate that source database exists and is accessible.

        Returns:
            True if source is valid, False otherwise
        """
        source_path = self.get_source_db_path()

        if not source_path.exists():
            logger.error(f"Source database not found: {source_path}")
            return False

        if not source_path.is_file():
            logger.error(f"Source is not a file: {source_path}")
            return False

        try:
            # Test read access
            with open(source_path, "rb") as f:
                f.read(1)
            return True
        except PermissionError:
            logger.error(f"Permission denied reading source: {source_path}")
            return False
        except Exception as e:
            logger.error(f"Error validating source: {e}")
            return False

    def hash_source_database(self) -> str:
        """
        Calculate SHA-256 hash of source database for forensic verification.

        Returns:
            Hexadecimal hash string

        Raises:
            FileNotFoundError: If source database not found
        """
        source_path = self.get_source_db_path()
        logger.info(f"Hashing source database: {source_path}")

        source_hash = hash_file(source_path)

        logger.info(f"Source database hash: {source_hash}")
        return source_hash

    def create_extraction_metadata(
        self,
        session: Session,
        source_db_hash: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> ExtractionMetadata:
        """
        Create extraction metadata record.

        Args:
            session: Database session
            source_db_hash: Hash of source database
            config: Extraction configuration

        Returns:
            ExtractionMetadata instance
        """
        from backend import __version__

        metadata = ExtractionMetadata(
            case_id=self.case_id,
            extraction_timestamp=self.extraction_timestamp,
            extractor_name=self.user,
            extractor_version=__version__,
            source_db_path=str(self.get_source_db_path()),
            source_db_hash=source_db_hash,
            total_messages=self.stats["total_messages"],
            total_attachments=self.stats["total_attachments"],
            total_conversations=self.stats["total_conversations"],
        )

        if config:
            metadata.set_extraction_config(config)

        session.add(metadata)
        session.commit()

        logger.info(f"Created extraction metadata: {metadata.id}")
        return metadata

    def extract(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute complete extraction process with forensic logging.

        Args:
            config: Optional extraction configuration

        Returns:
            Dictionary with extraction results and statistics
        """
        logger.info(f"Starting extraction for case {self.case_id}")
        self.stats["start_time"] = time.time()

        try:
            # Validate source
            if not self.validate_source():
                raise ValueError("Source validation failed")

            # Hash source database
            source_db_hash = self.hash_source_database()

            # Log extraction start
            self.audit_logger.log_extraction_start(
                source_db_path=str(self.get_source_db_path()),
                source_db_hash=source_db_hash,
                config=config or {},
            )

            # Initialize output database
            logger.info(f"Initializing output database: {self.output_db_path}")
            init_database(self.output_db_path)
            self.session = get_session(self.output_db_path)

            # Extract messages
            logger.info("Extracting messages...")
            message_count = self.extract_messages(self.session)
            self.stats["total_messages"] = message_count
            logger.info(f"Extracted {message_count} messages")

            # Extract attachments
            logger.info("Extracting attachments...")
            attachment_count = self.extract_attachments(self.session)
            self.stats["total_attachments"] = attachment_count
            logger.info(f"Extracted {attachment_count} attachments")

            # Create extraction metadata
            self.create_extraction_metadata(
                self.session,
                source_db_hash,
                config,
            )

            # Calculate duration
            self.stats["end_time"] = time.time()
            self.stats["duration_seconds"] = (
                self.stats["end_time"] - self.stats["start_time"]
            )

            # Log extraction complete
            self.audit_logger.log_extraction_complete(
                total_messages=self.stats["total_messages"],
                total_attachments=self.stats["total_attachments"],
                total_conversations=self.stats["total_conversations"],
                duration_seconds=self.stats["duration_seconds"],
            )

            logger.info(
                f"Extraction complete: {self.stats['total_messages']} messages, "
                f"{self.stats['total_attachments']} attachments, "
                f"{self.stats['duration_seconds']:.2f}s"
            )

            return {
                "success": True,
                "output_db_path": self.output_db_path,
                "stats": self.stats,
                "source_db_hash": source_db_hash,
            }

        except Exception as e:
            logger.error(f"Extraction failed: {e}", exc_info=True)

            # Log error
            self.audit_logger.log_extraction_error(
                error_message=str(e),
                error_details={"exception_type": type(e).__name__},
            )

            # Calculate duration even on failure
            if self.stats["start_time"]:
                self.stats["end_time"] = time.time()
                self.stats["duration_seconds"] = (
                    self.stats["end_time"] - self.stats["start_time"]
                )

            return {
                "success": False,
                "error": str(e),
                "stats": self.stats,
            }

        finally:
            # Close session
            if self.session:
                self.session.close()

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}(case={self.case_id}, "
            f"output={self.output_db_path})>"
        )
