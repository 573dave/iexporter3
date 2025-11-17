"""
Annotation Service Layer
CRUD operations for annotations with full audit trail
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.models import Annotation, AnnotationAudit, Message
from backend.utils import generate_annotation_id, AuditLogger
from backend.config import ANNOTATION_CONFIG

logger = logging.getLogger("iexporter3.services.annotation")


class AnnotationService:
    """
    Service layer for annotation management.
    Provides CRUD operations with automatic audit logging.
    """

    def __init__(self, session: Session, case_id: str, user: str):
        """
        Initialize annotation service.

        Args:
            session: Database session
            case_id: Case identifier
            user: User performing operations (for audit trail)
        """
        self.session = session
        self.case_id = case_id
        self.user = user
        self.audit_logger = AuditLogger(case_id=case_id, user=user)

    def create_annotation(
        self,
        message_id: str,
        tags: List[str],
        note: Optional[str] = None,
    ) -> Annotation:
        """
        Create a new annotation for a message.

        Args:
            message_id: ID of message to annotate
            tags: List of tags (from fixed set)
            note: Optional free-form note

        Returns:
            Created Annotation instance

        Raises:
            ValueError: If message not found or tags invalid
            SQLAlchemyError: If database operation fails
        """
        # Validate message exists
        message = self.session.query(Message).filter_by(message_id=message_id).first()
        if not message:
            raise ValueError(f"Message not found: {message_id}")

        # Validate tags
        valid_tags = ANNOTATION_CONFIG["tags"]
        invalid_tags = [t for t in tags if t not in valid_tags]
        if invalid_tags:
            raise ValueError(f"Invalid tags: {invalid_tags}. Valid tags: {valid_tags}")

        if not tags:
            raise ValueError("At least one tag is required")

        # Validate note length
        if note and len(note) > ANNOTATION_CONFIG["note_max_length"]:
            raise ValueError(
                f"Note exceeds maximum length of {ANNOTATION_CONFIG['note_max_length']} characters"
            )

        # Generate annotation ID
        timestamp = int(datetime.utcnow().timestamp())
        annotation_sequence = self._get_next_annotation_sequence()
        annotation_id = generate_annotation_id(self.case_id, timestamp, annotation_sequence)

        # Create annotation
        annotation = Annotation(
            annotation_id=annotation_id,
            message_id=message_id,
            conversation_id=message.conversation_id,
            created_by=self.user,
            created_at=timestamp,
        )

        annotation.set_tags(tags)
        annotation.note = note

        try:
            # Save to database
            self.session.add(annotation)

            # Create audit log entry
            audit_entry = AnnotationAudit(
                annotation_id=annotation_id,
                action="CREATE",
                new_value=annotation.to_dict(),
                changed_by=self.user,
                changed_at=timestamp,
            )
            self.session.add(audit_entry)

            self.session.commit()

            # Log to audit file
            self.audit_logger.log_annotation_create(
                annotation_id=annotation_id,
                message_id=message_id,
                tags=tags,
                note=note or "",
            )

            logger.info(f"Created annotation {annotation_id} for message {message_id}")

            return annotation

        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Failed to create annotation: {e}")
            raise

    def update_annotation(
        self,
        annotation_id: str,
        tags: Optional[List[str]] = None,
        note: Optional[str] = None,
    ) -> Annotation:
        """
        Update an existing annotation.

        Args:
            annotation_id: ID of annotation to update
            tags: New tags (if provided)
            note: New note (if provided)

        Returns:
            Updated Annotation instance

        Raises:
            ValueError: If annotation not found or tags invalid
            SQLAlchemyError: If database operation fails
        """
        # Find annotation
        annotation = (
            self.session.query(Annotation).filter_by(annotation_id=annotation_id).first()
        )

        if not annotation:
            raise ValueError(f"Annotation not found: {annotation_id}")

        # Store old value for audit
        old_value = annotation.to_dict()

        # Update tags if provided
        if tags is not None:
            valid_tags = ANNOTATION_CONFIG["tags"]
            invalid_tags = [t for t in tags if t not in valid_tags]
            if invalid_tags:
                raise ValueError(f"Invalid tags: {invalid_tags}")

            if not tags:
                raise ValueError("At least one tag is required")

            annotation.set_tags(tags)

        # Update note if provided
        if note is not None:
            if len(note) > ANNOTATION_CONFIG["note_max_length"]:
                raise ValueError(
                    f"Note exceeds maximum length of {ANNOTATION_CONFIG['note_max_length']}"
                )
            annotation.note = note

        # Update metadata
        timestamp = int(datetime.utcnow().timestamp())
        annotation.updated_by = self.user
        annotation.updated_at = timestamp

        try:
            # Create audit log entry
            new_value = annotation.to_dict()
            audit_entry = AnnotationAudit(
                annotation_id=annotation_id,
                action="UPDATE",
                old_value=old_value,
                new_value=new_value,
                changed_by=self.user,
                changed_at=timestamp,
            )
            self.session.add(audit_entry)

            self.session.commit()

            # Log to audit file
            self.audit_logger.log_annotation_update(
                annotation_id=annotation_id,
                old_value=old_value,
                new_value=new_value,
            )

            logger.info(f"Updated annotation {annotation_id}")

            return annotation

        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Failed to update annotation: {e}")
            raise

    def delete_annotation(self, annotation_id: str) -> None:
        """
        Delete an annotation.

        Args:
            annotation_id: ID of annotation to delete

        Raises:
            ValueError: If annotation not found
            SQLAlchemyError: If database operation fails
        """
        # Find annotation
        annotation = (
            self.session.query(Annotation).filter_by(annotation_id=annotation_id).first()
        )

        if not annotation:
            raise ValueError(f"Annotation not found: {annotation_id}")

        # Store final value for audit
        final_value = annotation.to_dict()

        # Create audit log entry BEFORE deleting
        timestamp = int(datetime.utcnow().timestamp())
        audit_entry = AnnotationAudit(
            annotation_id=annotation_id,
            action="DELETE",
            old_value=final_value,
            changed_by=self.user,
            changed_at=timestamp,
        )

        try:
            self.session.add(audit_entry)
            self.session.delete(annotation)
            self.session.commit()

            # Log to audit file
            self.audit_logger.log_annotation_delete(
                annotation_id=annotation_id,
                final_value=final_value,
            )

            logger.info(f"Deleted annotation {annotation_id}")

        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Failed to delete annotation: {e}")
            raise

    def get_annotation(self, annotation_id: str) -> Optional[Annotation]:
        """
        Get annotation by ID.

        Args:
            annotation_id: ID of annotation

        Returns:
            Annotation instance or None if not found
        """
        return (
            self.session.query(Annotation).filter_by(annotation_id=annotation_id).first()
        )

    def get_annotations_for_message(self, message_id: str) -> List[Annotation]:
        """
        Get all annotations for a specific message.

        Args:
            message_id: Message ID

        Returns:
            List of Annotation instances
        """
        return (
            self.session.query(Annotation)
            .filter_by(message_id=message_id)
            .order_by(Annotation.created_at.desc())
            .all()
        )

    def get_annotations_for_conversation(
        self, conversation_id: str, tags: Optional[List[str]] = None
    ) -> List[Annotation]:
        """
        Get all annotations for a conversation, optionally filtered by tags.

        Args:
            conversation_id: Conversation ID
            tags: Optional list of tags to filter by

        Returns:
            List of Annotation instances
        """
        query = self.session.query(Annotation).filter_by(conversation_id=conversation_id)

        # Filter by tags if provided
        if tags:
            # This is a simplification - proper implementation would parse JSON
            # For now, filter in Python
            annotations = query.order_by(Annotation.created_at.desc()).all()
            filtered = [
                a for a in annotations if any(tag in a.get_tags() for tag in tags)
            ]
            return filtered

        return query.order_by(Annotation.created_at.desc()).all()

    def get_all_annotations(self) -> List[Annotation]:
        """
        Get all annotations for the case.

        Returns:
            List of all Annotation instances
        """
        return self.session.query(Annotation).order_by(Annotation.created_at.desc()).all()

    def get_annotation_audit_trail(self, annotation_id: str) -> List[AnnotationAudit]:
        """
        Get complete audit trail for an annotation.

        Args:
            annotation_id: Annotation ID

        Returns:
            List of AnnotationAudit entries
        """
        return (
            self.session.query(AnnotationAudit)
            .filter_by(annotation_id=annotation_id)
            .order_by(AnnotationAudit.changed_at.desc())
            .all()
        )

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get annotation statistics for the case.

        Returns:
            Dictionary with statistics
        """
        all_annotations = self.get_all_annotations()

        tag_counts = {
            "Key": 0,
            "Timeline": 0,
            "Privileged": 0,
            "WorkProduct": 0,
        }

        for annotation in all_annotations:
            for tag in annotation.get_tags():
                if tag in tag_counts:
                    tag_counts[tag] += 1

        return {
            "total_annotations": len(all_annotations),
            "tag_counts": tag_counts,
            "annotated_conversations": len(
                set(a.conversation_id for a in all_annotations)
            ),
        }

    def export_annotations_to_json(
        self, conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export annotations to JSON format for HTML export.

        Args:
            conversation_id: Optional conversation ID to filter by

        Returns:
            Dictionary in annotations.json format
        """
        if conversation_id:
            annotations = self.get_annotations_for_conversation(conversation_id)
        else:
            annotations = self.get_all_annotations()

        return {
            "schema_version": "1.0",
            "export_timestamp": datetime.utcnow().isoformat() + "Z",
            "case_id": self.case_id,
            "conversation_id": conversation_id,
            "annotations": [a.to_dict() for a in annotations],
        }

    def _get_next_annotation_sequence(self) -> int:
        """
        Get next annotation sequence number.

        Returns:
            Next sequence number (1-based)
        """
        # Count existing annotations for this case
        # This is a simplified implementation
        # Production would use a more sophisticated counter
        count = self.session.query(Annotation).count()
        return count + 1


if __name__ == "__main__":
    # Test annotation service
    from backend.models import init_database, get_session

    print("Testing Annotation Service")
    print("=" * 50)

    # Initialize test database
    test_db = "/tmp/test_annotations.db"
    init_database(test_db, drop_existing=True)
    session = get_session(test_db)

    # Create test message
    test_message = Message(
        message_id="MSG_TEST2024_001",
        conversation_id="CONV_001",
        sender_id="+15551234567",
        sender_name="John Doe",
        message_text="Test message for annotation",
        timestamp=int(datetime.utcnow().timestamp()),
        timezone="UTC",
        hash="abc123",
        extraction_timestamp=int(datetime.utcnow().timestamp()),
    )
    session.add(test_message)
    session.commit()

    # Initialize service
    service = AnnotationService(
        session=session,
        case_id="TEST2024",
        user="test.user@example.com",
    )

    # Create annotation
    print("\n1. Creating annotation...")
    annotation = service.create_annotation(
        message_id="MSG_TEST2024_001",
        tags=["Key", "Timeline"],
        note="This is a test annotation for demonstrating the service layer.",
    )
    print(f"   Created: {annotation}")

    # Update annotation
    print("\n2. Updating annotation...")
    updated = service.update_annotation(
        annotation_id=annotation.annotation_id,
        tags=["Key", "Privileged"],
        note="Updated note text.",
    )
    print(f"   Updated: {updated}")

    # Get annotation
    print("\n3. Retrieving annotation...")
    retrieved = service.get_annotation(annotation.annotation_id)
    print(f"   Retrieved: {retrieved}")

    # Get audit trail
    print("\n4. Getting audit trail...")
    audit_trail = service.get_annotation_audit_trail(annotation.annotation_id)
    print(f"   Audit entries: {len(audit_trail)}")
    for entry in audit_trail:
        print(f"   - {entry.action} by {entry.changed_by} at {entry.get_changed_datetime()}")

    # Get statistics
    print("\n5. Getting statistics...")
    stats = service.get_statistics()
    print(f"   Stats: {stats}")

    # Export to JSON
    print("\n6. Exporting to JSON...")
    json_export = service.export_annotations_to_json()
    print(f"   Exported {len(json_export['annotations'])} annotations")

    # Delete annotation
    print("\n7. Deleting annotation...")
    service.delete_annotation(annotation.annotation_id)
    print("   Deleted successfully")

    # Verify deletion
    deleted = service.get_annotation(annotation.annotation_id)
    print(f"   Annotation exists after deletion: {deleted is not None}")

    # Audit trail still exists
    audit_after_delete = service.get_annotation_audit_trail(annotation.annotation_id)
    print(f"   Audit trail entries after deletion: {len(audit_after_delete)}")

    session.close()
    print("\n✓ Annotation service tested successfully!")
