"""
Audit Logger for Forensic Chain of Custody
Specialized logging for all forensic operations with immutable audit trail
"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from backend.config import PROJECT_ROOT

# Create audit log directory
AUDIT_LOG_DIR = PROJECT_ROOT / "logs" / "audit"
AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)


class AuditLogger:
    """
    Forensic audit logger with structured logging.
    Creates immutable audit trail for all operations.
    """

    def __init__(self, case_id: str, user: str):
        """
        Initialize audit logger for a specific case and user.

        Args:
            case_id: Case identifier
            user: User performing operations (email or username)
        """
        self.case_id = case_id
        self.user = user

        # Create case-specific audit log
        log_filename = f"audit_{case_id}_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
        self.log_path = AUDIT_LOG_DIR / log_filename

        # Set up logger
        self.logger = logging.getLogger(f"iexporter3.audit.{case_id}")
        self.logger.setLevel(logging.INFO)

        # File handler (append mode for immutability)
        handler = logging.FileHandler(self.log_path, mode="a", encoding="utf-8")
        handler.setLevel(logging.INFO)

        # JSON formatter
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)
        self.logger.propagate = False

    def _log_event(
        self,
        event_type: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
    ):
        """
        Log a forensic event in structured JSON format.

        Args:
            event_type: Type of event (extraction, annotation, export, etc.)
            action: Specific action performed
            details: Additional details (JSON-serializable)
            status: Operation status (success, failure, warning)
        """
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "timestamp_unix": int(datetime.utcnow().timestamp()),
            "case_id": self.case_id,
            "user": self.user,
            "event_type": event_type,
            "action": action,
            "status": status,
            "details": details or {},
        }

        # Log as single JSON line (JSONL format)
        self.logger.info(json.dumps(event))

    def log_extraction_start(
        self,
        source_db_path: str,
        source_db_hash: str,
        config: Dict[str, Any],
    ):
        """Log extraction operation start."""
        self._log_event(
            event_type="extraction",
            action="start",
            details={
                "source_db_path": source_db_path,
                "source_db_hash": source_db_hash,
                "extraction_config": config,
            },
        )

    def log_extraction_complete(
        self,
        total_messages: int,
        total_attachments: int,
        total_conversations: int,
        duration_seconds: float,
    ):
        """Log extraction operation completion."""
        self._log_event(
            event_type="extraction",
            action="complete",
            details={
                "total_messages": total_messages,
                "total_attachments": total_attachments,
                "total_conversations": total_conversations,
                "duration_seconds": duration_seconds,
            },
        )

    def log_extraction_error(self, error_message: str, error_details: Optional[Dict] = None):
        """Log extraction error."""
        self._log_event(
            event_type="extraction",
            action="error",
            status="failure",
            details={
                "error_message": error_message,
                "error_details": error_details or {},
            },
        )

    def log_annotation_create(self, annotation_id: str, message_id: str, tags: list, note: str):
        """Log annotation creation."""
        self._log_event(
            event_type="annotation",
            action="create",
            details={
                "annotation_id": annotation_id,
                "message_id": message_id,
                "tags": tags,
                "note_length": len(note) if note else 0,
            },
        )

    def log_annotation_update(
        self,
        annotation_id: str,
        old_value: Dict[str, Any],
        new_value: Dict[str, Any],
    ):
        """Log annotation update."""
        self._log_event(
            event_type="annotation",
            action="update",
            details={
                "annotation_id": annotation_id,
                "old_value": old_value,
                "new_value": new_value,
            },
        )

    def log_annotation_delete(self, annotation_id: str, final_value: Dict[str, Any]):
        """Log annotation deletion."""
        self._log_event(
            event_type="annotation",
            action="delete",
            details={
                "annotation_id": annotation_id,
                "final_value": final_value,
            },
        )

    def log_export_start(
        self,
        export_id: str,
        export_type: str,
        conversation_id: Optional[str] = None,
    ):
        """Log export operation start."""
        self._log_event(
            event_type="export",
            action="start",
            details={
                "export_id": export_id,
                "export_type": export_type,
                "conversation_id": conversation_id,
            },
        )

    def log_export_complete(
        self,
        export_id: str,
        export_hash: str,
        message_count: int,
        annotation_count: int,
        duration_seconds: float,
    ):
        """Log export operation completion."""
        self._log_event(
            event_type="export",
            action="complete",
            details={
                "export_id": export_id,
                "export_hash": export_hash,
                "message_count": message_count,
                "annotation_count": annotation_count,
                "duration_seconds": duration_seconds,
            },
        )

    def log_hash_verification(
        self,
        file_path: str,
        expected_hash: str,
        actual_hash: str,
        verification_result: bool,
    ):
        """Log hash verification result."""
        status = "success" if verification_result else "failure"
        self._log_event(
            event_type="hash_verification",
            action="verify",
            status=status,
            details={
                "file_path": file_path,
                "expected_hash": expected_hash,
                "actual_hash": actual_hash,
                "match": verification_result,
            },
        )

    def log_database_operation(self, operation: str, table: str, record_count: int):
        """Log database operation."""
        self._log_event(
            event_type="database",
            action=operation,
            details={
                "table": table,
                "record_count": record_count,
            },
        )

    def log_custom_event(
        self,
        event_type: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Log custom forensic event."""
        self._log_event(
            event_type=event_type,
            action=action,
            details=details,
        )


def read_audit_log(case_id: str, date: Optional[str] = None) -> list:
    """
    Read audit log for a case.

    Args:
        case_id: Case identifier
        date: Optional date filter (YYYYMMDD format)

    Returns:
        List of audit events (parsed JSON)
    """
    if date:
        log_filename = f"audit_{case_id}_{date}.jsonl"
    else:
        # Find most recent log for case
        log_pattern = f"audit_{case_id}_*.jsonl"
        log_files = sorted(AUDIT_LOG_DIR.glob(log_pattern), reverse=True)
        if not log_files:
            return []
        log_filename = log_files[0].name

    log_path = AUDIT_LOG_DIR / log_filename

    if not log_path.exists():
        return []

    events = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                event = json.loads(line.strip())
                events.append(event)
            except json.JSONDecodeError:
                continue

    return events


if __name__ == "__main__":
    # Test audit logger
    import time

    print("Testing Audit Logger")
    print("=" * 50)

    # Create audit logger
    audit = AuditLogger(case_id="TEST2024", user="test.user@example.com")

    # Log extraction
    audit.log_extraction_start(
        source_db_path="/path/to/chat.db",
        source_db_hash="abc123...",
        config={"filter": "all", "include_attachments": True},
    )

    time.sleep(0.1)

    audit.log_extraction_complete(
        total_messages=1000,
        total_attachments=50,
        total_conversations=10,
        duration_seconds=5.2,
    )

    # Log annotation
    audit.log_annotation_create(
        annotation_id="ANN_TEST2024_001",
        message_id="MSG_TEST2024_001",
        tags=["Key", "Timeline"],
        note="Important message for case",
    )

    # Log export
    audit.log_export_start(
        export_id="EXP_TEST2024_001",
        export_type="annotated",
    )

    audit.log_export_complete(
        export_id="EXP_TEST2024_001",
        export_hash="def456...",
        message_count=1000,
        annotation_count=5,
        duration_seconds=2.1,
    )

    # Log hash verification
    audit.log_hash_verification(
        file_path="/path/to/export.html",
        expected_hash="abc123...",
        actual_hash="abc123...",
        verification_result=True,
    )

    print(f"Audit log written to: {audit.log_path}")

    # Read audit log
    events = read_audit_log("TEST2024")
    print(f"\nAudit events read: {len(events)}")
    for event in events:
        print(f"  - {event['event_type']}.{event['action']}: {event['status']}")

    print("\nAudit logger tested successfully!")
