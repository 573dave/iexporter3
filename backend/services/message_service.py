"""
Message Service Layer
Query and retrieval operations for messages and attachments
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models import Message, Attachment, Annotation
from backend.config import EXPORT_CONFIG

logger = logging.getLogger("iexporter3.services.message")


class MessageService:
    """
    Service layer for message operations.
    Provides query methods for messages and attachments.
    """

    def __init__(self, session: Session):
        """
        Initialize message service.

        Args:
            session: Database session
        """
        self.session = session

    def get_message(self, message_id: str) -> Optional[Message]:
        """
        Get message by ID.

        Args:
            message_id: Message ID

        Returns:
            Message instance or None
        """
        return self.session.query(Message).filter_by(message_id=message_id).first()

    def get_messages_for_conversation(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Message]:
        """
        Get messages for a conversation.

        Args:
            conversation_id: Conversation ID
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            List of Message instances
        """
        query = (
            self.session.query(Message)
            .filter_by(conversation_id=conversation_id)
            .order_by(Message.timestamp.asc())
        )

        if offset:
            query = query.offset(offset)

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_messages_for_part(
        self,
        conversation_id: str,
        part_number: int,
    ) -> List[Message]:
        """
        Get messages for a specific conversation part.

        Args:
            conversation_id: Conversation ID
            part_number: Part number

        Returns:
            List of Message instances
        """
        return (
            self.session.query(Message)
            .filter_by(conversation_id=conversation_id, part_number=part_number)
            .order_by(Message.sequence_in_part.asc())
            .all()
        )

    def split_conversation_into_parts(
        self,
        conversation_id: str,
        messages_per_part: Optional[int] = None,
    ) -> Dict[int, List[Message]]:
        """
        Split conversation messages into parts.

        Args:
            conversation_id: Conversation ID
            messages_per_part: Messages per part (default from config)

        Returns:
            Dictionary mapping part number to list of messages
        """
        if messages_per_part is None:
            messages_per_part = EXPORT_CONFIG["messages_per_part"]

        # Get all messages for conversation
        messages = self.get_messages_for_conversation(conversation_id)

        # Split into parts
        parts = {}
        part_number = 1

        for i in range(0, len(messages), messages_per_part):
            part_messages = messages[i : i + messages_per_part]

            # Update part_number and sequence_in_part for each message
            for seq, message in enumerate(part_messages, start=1):
                message.part_number = part_number
                message.sequence_in_part = seq

            parts[part_number] = part_messages
            part_number += 1

        # Commit part assignments
        self.session.commit()

        logger.info(
            f"Split conversation {conversation_id} into {len(parts)} parts "
            f"({messages_per_part} messages per part)"
        )

        return parts

    def search_messages(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Message]:
        """
        Search messages by text content.

        Args:
            query: Search query
            conversation_id: Optional conversation filter
            limit: Maximum results

        Returns:
            List of matching Message instances
        """
        search_query = self.session.query(Message).filter(
            Message.message_text.like(f"%{query}%")
        )

        if conversation_id:
            search_query = search_query.filter_by(conversation_id=conversation_id)

        results = search_query.order_by(Message.timestamp.asc()).limit(limit).all()

        logger.info(f"Search for '{query}' returned {len(results)} results")

        return results

    def get_attachments_for_message(self, message_id: str) -> List[Attachment]:
        """
        Get all attachments for a message.

        Args:
            message_id: Message ID

        Returns:
            List of Attachment instances
        """
        return (
            self.session.query(Attachment)
            .filter_by(message_id=message_id)
            .order_by(Attachment.created_at.asc())
            .all()
        )

    def get_annotated_messages(
        self, conversation_id: Optional[str] = None
    ) -> List[Tuple[Message, List[Annotation]]]:
        """
        Get messages that have annotations.

        Args:
            conversation_id: Optional conversation filter

        Returns:
            List of (Message, [Annotations]) tuples
        """
        query = (
            self.session.query(Message)
            .join(Annotation, Message.message_id == Annotation.message_id)
            .distinct()
        )

        if conversation_id:
            query = query.filter(Message.conversation_id == conversation_id)

        messages = query.order_by(Message.timestamp.asc()).all()

        # Get annotations for each message
        result = []
        for message in messages:
            annotations = (
                self.session.query(Annotation)
                .filter_by(message_id=message.message_id)
                .all()
            )
            result.append((message, annotations))

        return result

    def get_conversation_statistics(
        self, conversation_id: str
    ) -> Dict[str, Any]:
        """
        Get statistics for a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            Dictionary with statistics
        """
        messages = self.get_messages_for_conversation(conversation_id)

        if not messages:
            return {
                "conversation_id": conversation_id,
                "total_messages": 0,
                "total_attachments": 0,
                "date_range": None,
                "participants": [],
            }

        # Count attachments
        total_attachments = (
            self.session.query(Attachment)
            .join(Message)
            .filter(Message.conversation_id == conversation_id)
            .count()
        )

        # Get date range
        timestamps = [m.timestamp for m in messages]
        date_range = {
            "start": datetime.utcfromtimestamp(min(timestamps)).isoformat(),
            "end": datetime.utcfromtimestamp(max(timestamps)).isoformat(),
        }

        # Get unique participants
        participants = list(set(m.sender_id for m in messages if m.sender_id))

        return {
            "conversation_id": conversation_id,
            "total_messages": len(messages),
            "total_attachments": total_attachments,
            "date_range": date_range,
            "participants": participants,
            "messages_from_me": sum(1 for m in messages if m.is_from_me),
            "messages_from_them": sum(1 for m in messages if not m.is_from_me),
        }

    def get_all_conversations(self) -> List[Dict[str, Any]]:
        """
        Get list of all conversations with summary info.

        Returns:
            List of conversation summaries
        """
        # Get unique conversation IDs
        conversations = (
            self.session.query(Message.conversation_id)
            .distinct()
            .all()
        )

        conversation_list = []

        for (conv_id,) in conversations:
            stats = self.get_conversation_statistics(conv_id)
            conversation_list.append(stats)

        return conversation_list

    def prepare_message_for_export(self, message: Message) -> Dict[str, Any]:
        """
        Prepare message data for HTML export.

        Args:
            message: Message instance

        Returns:
            Dictionary with message data and related info
        """
        # Get attachments
        attachments = self.get_attachments_for_message(message.message_id)

        # Get annotations
        annotations = (
            self.session.query(Annotation)
            .filter_by(message_id=message.message_id)
            .all()
        )

        return {
            "message": message.to_dict(),
            "attachments": [a.to_dict() for a in attachments],
            "annotations": [a.to_dict() for a in annotations],
            "has_annotation": len(annotations) > 0,
        }


if __name__ == "__main__":
    # Test message service
    from backend.models import init_database, get_session

    print("Testing Message Service")
    print("=" * 50)

    # Initialize test database
    test_db = "/tmp/test_messages.db"
    init_database(test_db, drop_existing=True)
    session = get_session(test_db)

    # Create test messages
    print("\n1. Creating test messages...")
    for i in range(25):
        message = Message(
            message_id=f"MSG_TEST2024_{i+1:03d}",
            conversation_id="CONV_001",
            sender_id="+15551234567" if i % 2 == 0 else "+15559876543",
            sender_name="Alice" if i % 2 == 0 else "Bob",
            message_text=f"Test message {i+1}",
            timestamp=int(datetime.utcnow().timestamp()) + i,
            timezone="UTC",
            hash=f"hash{i+1}",
            extraction_timestamp=int(datetime.utcnow().timestamp()),
        )
        session.add(message)

    session.commit()
    print("   Created 25 test messages")

    # Initialize service
    service = MessageService(session)

    # Get conversation messages
    print("\n2. Getting conversation messages...")
    messages = service.get_messages_for_conversation("CONV_001")
    print(f"   Retrieved {len(messages)} messages")

    # Split into parts
    print("\n3. Splitting into parts (10 messages per part)...")
    parts = service.split_conversation_into_parts("CONV_001", messages_per_part=10)
    print(f"   Split into {len(parts)} parts")
    for part_num, part_messages in parts.items():
        print(f"   - Part {part_num}: {len(part_messages)} messages")

    # Search messages
    print("\n4. Searching messages...")
    results = service.search_messages("message 1")
    print(f"   Found {len(results)} messages matching 'message 1'")

    # Get statistics
    print("\n5. Getting conversation statistics...")
    stats = service.get_conversation_statistics("CONV_001")
    print(f"   Stats: {stats}")

    # Get all conversations
    print("\n6. Getting all conversations...")
    conversations = service.get_all_conversations()
    print(f"   Found {len(conversations)} conversations")

    session.close()
    print("\n✓ Message service tested successfully!")
