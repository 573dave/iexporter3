# iExporter3 - Forensic-Grade iMessage Extraction & Annotation System
## Architecture Document v1.0

---

## TECHNOLOGY STACK

### Backend/Extraction Pipeline
- **Language**: Python 3.11+
- **Database**: SQLite 3.35+ with WAL mode
- **ORM**: SQLAlchemy 2.0+ (provides abstraction while maintaining forensic transparency)
- **Hashing**: hashlib (SHA-256 for all evidence integrity)
- **Date/Time**: All timestamps in UTC, stored with timezone info

### Desktop Application
- **Framework**: Electron 28+
- **Renderer**: Chromium-based WebView
- **IPC**: Electron IPC for Python ↔ JavaScript communication
- **Process Model**: Main process (Python extraction) + Renderer (UI)

### HTML Export (Standalone Viewer)
- **Frontend**: Vanilla JavaScript (ES6+)
- **CSS**: Modern CSS3 (Grid, Flexbox)
- **No frameworks**: Ensures transparency, auditability, and forensic compliance
- **Browser Support**: Chrome 130+, Edge 130+, Safari 17+

### Reporting
- **HTML Reports**: Jinja2 templates
- **PDF Generation**: WeasyPrint (HTML → PDF with proper formatting)

---

## FORENSIC COMPLIANCE

### Standards Compliance
- **ISO 27037**: Guidelines for identification, collection, acquisition, and preservation of digital evidence
- **ISO 17025**: General requirements for the competence of testing and calibration laboratories
- **NIST SP 800-86**: Guide to Integrating Forensic Techniques into Incident Response
- **NIST SP 800-101**: Guidelines on Mobile Device Forensics

### Forensic Principles

#### 1. **Evidence Integrity**
- SHA-256 hashing at every stage:
  - Original database hash (extraction time)
  - Individual message hashes
  - Attachment file hashes
  - Export package hashes
- No modification of source data
- Read-only access to original iMessage database
- Cryptographic verification on every load

#### 2. **Chain of Custody**
- Audit log for all operations:
  - Extraction timestamp and user
  - Export timestamp and user
  - Annotation changes (create, update, delete)
  - Hash verification results
- User identification for all modifications
- Immutable audit trail (append-only)

#### 3. **Reproducibility**
- Stable message IDs across re-exports
- Deterministic extraction process
- Documented methodology
- Version tracking for all schema changes

#### 4. **Evidence Separation**
- **EVIDENCE LAYER**: Original messages, attachments (immutable)
- **WORK PRODUCT LAYER**: Annotations, notes, tags (mutable, internal only)
- **PRESENTATION LAYER**: HTML rendering (derived, reproducible)

#### 5. **Documentation**
- Extraction methodology documentation
- Tool version tracking
- Configuration preservation
- Error logging for all operations

---

## SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                         DESKTOP APPLICATION                      │
│                         (Electron + Python)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌───────────────┐  ┌──────────────┐  ┌─────────────────────┐  │
│  │   EXTRACTION  │  │  ANNOTATION  │  │   EXPORT ENGINE     │  │
│  │    ENGINE     │  │   MANAGER    │  │                     │  │
│  │               │  │              │  │  - Clean HTML       │  │
│  │  - iMessage   │  │  - CRUD ops  │  │  - Annotated HTML   │  │
│  │    DB reader  │  │  - Audit log │  │  - Reports (PDF)    │  │
│  │  - Message    │  │  - SQLite    │  │  - Hash generation  │  │
│  │    parser     │  │    with WAL  │  │                     │  │
│  │  - Attachment │  │              │  │                     │  │
│  │    extractor  │  │              │  │                     │  │
│  │  - Hash gen   │  │              │  │                     │  │
│  └───────┬───────┘  └──────┬───────┘  └──────────┬──────────┘  │
│          │                 │                     │              │
│          └─────────────────┴─────────────────────┘              │
│                            │                                     │
│                            ▼                                     │
│                  ┌──────────────────┐                           │
│                  │  MESSAGES.DB     │                           │
│                  │  (SQLite + WAL)  │                           │
│                  │                  │                           │
│                  │  - messages      │                           │
│                  │  - attachments   │                           │
│                  │  - annotations   │                           │
│                  │  - audit_log     │                           │
│                  │  - metadata      │                           │
│                  └──────────────────┘                           │
│                                                                   │
└───────────────────────────┬───────────────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────────┐
            │         EXPORT PACKAGES           │
            ├───────────────────────────────────┤
            │                                   │
            │  CLEAN EXPORT (Evidence Only)     │
            │  ├── conversation_001.html        │
            │  ├── conversation_001.hash.json   │
            │  ├── attachments/                 │
            │  │   ├── original/               │
            │  │   └── thumbs/                 │
            │  └── attachments.json             │
            │                                   │
            │  ANNOTATED EXPORT (+ Annotations) │
            │  ├── conversation_001.html        │
            │  ├── conversation_001.hash.json   │
            │  ├── annotations.json             │
            │  ├── attachments/                 │
            │  │   ├── original/               │
            │  │   └── thumbs/                 │
            │  └── attachments.json             │
            │                                   │
            │  REPORT BUNDLE                    │
            │  ├── key_messages_report.html     │
            │  ├── key_messages_report.pdf      │
            │  ├── annotations.json             │
            │  └── README.txt                   │
            │                                   │
            └───────────────────────────────────┘
```

---

## UI LAYOUT (3-Column Design)

### Desktop App & HTML Export

```
┌────────────────────────────────────────────────────────────────────┐
│  iExporter3 - Case: [CASE_ID] - Part 1 of 10    [WORK PRODUCT]   │
├──────────┬──────────────────────────────────┬─────────────────────┤
│          │                                  │                     │
│   LEFT   │            MIDDLE                │       RIGHT         │
│ SIDEBAR  │      (iMessage View)             │     SIDEBAR         │
│          │                                  │                     │
│ NAV &    │  ┌────────────────────────┐      │  ANNOTATIONS        │
│ DETAILS  │  │  [Sender Name]         │      │                     │
│          │  │  Message text here...  │      │  [Filter: All ▼]    │
│ ✓ Hash   │  │  10:23 AM             │      │                     │
│ Verified │  └────────────────────────┘      │  ☆ Key Messages (5) │
│          │                                  │  ⏱ Timeline (12)    │
│ Case:    │  ┌────────────────────────┐      │  🔒 Privileged (3)  │
│ ABC-2024 │  │         [Sender Name]  │      │  📝 Work Product(8) │
│          │  │  Message text here...  │      │                     │
│ Extracted│  │             10:24 AM  │      │  ─────────────────  │
│ 2024-    │  └────────────────────────┘      │                     │
│ 11-17    │                                  │  [MSG_ABC_001]      │
│          │  ┌────────────────────────┐      │  ☆⏱ "Key admission" │
│ Messages:│  │  [Image Attachment]    │ 📎   │  Click to jump →    │
│ 10,000   │  │  IMG_2024.jpg          │      │                     │
│          │  │  10:25 AM             │      │  [MSG_ABC_042]      │
│ Parts:   │  └────────────────────────┘      │  🔒 "Attorney       │
│ 1 of 10  │                                  │     communication"  │
│          │         [Load More ▼]            │  Click to jump →    │
│ ────────│                                  │                     │
│          │                                  │  [MSG_ABC_089]      │
│ Jump to: │                                  │  📝⏱ "Timeline ref" │
│ [Part #] │                                  │  Click to jump →    │
│          │                                  │                     │
│ Search:  │                                  │  [+ Annotate]       │
│ [     ]  │                                  │  (Desktop only)     │
│          │                                  │                     │
└──────────┴──────────────────────────────────┴─────────────────────┘
```

### Column Responsibilities

#### LEFT SIDEBAR (Nav & Details)
- **Hash Verification Status**
  - ✓ Green: Evidence Verified
  - ⚠ Red: Hash Mismatch
  - ? Yellow: Cannot Verify
- **Case Metadata**
  - Case ID
  - Extraction timestamp
  - Exporter name
  - Total message count
- **Navigation**
  - Part selector (if multi-part)
  - Jump to message ID
  - Date range navigator
- **Search**
  - Full-text search within current part
  - Filter by sender
  - Filter by date range

#### MIDDLE COLUMN (iMessage View)
- **iMessage-style bubbles**
  - Sender bubbles (blue/gray)
  - Receiver bubbles (gray)
  - Timestamps
  - Read receipts (if available)
- **Message Content**
  - Text messages
  - Attachments (thumbnails with lightbox)
  - Reactions (if supported)
  - Group chat indicators
- **Scrolling**
  - Infinite scroll / load more
  - Jump-to-message highlighting
  - Smooth scroll animations
- **Annotate Button**
  - Visible on hover (desktop only)
  - Opens annotation modal

#### RIGHT SIDEBAR (Annotations)
- **Filter Controls**
  - Multi-select tag filter
  - Show/hide annotations
- **Annotation Count by Tag**
  - Key Messages (count)
  - Timeline (count)
  - Privileged (count)
  - Work Product (count)
- **Annotation List**
  - Message ID reference
  - Tag icons
  - Note preview (truncated)
  - Click to jump to message
- **Actions (Desktop Only)**
  - [+ Annotate] button
  - Edit/delete on click

---

## MESSAGE ID FORMAT

### Stable ID Structure
```
MSG_<CASEID>_<EXTRACTION_TS>_<CONV_HASH>_<SEQ>

Example:
MSG_ABC2024_20241117120000_A3F2B91C_00001

Components:
- MSG_          : Fixed prefix
- ABC2024       : Case identifier (alphanumeric, max 20 chars)
- 20241117120000: Extraction timestamp (YYYYMMDDHHmmss UTC)
- A3F2B91C      : First 8 chars of conversation SHA-256 hash
- 00001         : Sequential message number (5 digits, zero-padded)
```

### Properties
- **Globally unique**: No collisions across cases or extractions
- **Stable**: Re-exporting same source produces same IDs
- **Sortable**: Sequential numbers maintain order
- **Traceable**: Extraction timestamp embedded
- **Forensically sound**: Hash component proves uniqueness

---

## DATABASE SCHEMA

### SQLite Configuration
```python
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;
PRAGMA secure_delete = ON;  # Forensic requirement
```

### Tables

#### messages
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT UNIQUE NOT NULL,  -- MSG_<CASEID>_<TS>_<HASH>_<SEQ>
    conversation_id TEXT NOT NULL,
    sender_id TEXT,
    sender_name TEXT,
    recipient_ids TEXT,  -- JSON array
    message_text TEXT,
    timestamp INTEGER NOT NULL,  -- Unix timestamp (UTC)
    timezone TEXT,  -- Original timezone (e.g., "America/New_York")
    has_attachment BOOLEAN DEFAULT 0,
    attachment_ids TEXT,  -- JSON array of attachment IDs
    message_type TEXT,  -- 'text', 'attachment', 'reaction', etc.
    service_name TEXT,  -- 'iMessage', 'SMS', etc.
    is_from_me BOOLEAN,
    read_receipt BOOLEAN,
    hash TEXT NOT NULL,  -- SHA-256 of message content
    extraction_timestamp INTEGER NOT NULL,
    part_number INTEGER DEFAULT 1,
    sequence_in_part INTEGER,
    created_at INTEGER NOT NULL,
    INDEX idx_message_id (message_id),
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_part_number (part_number)
);
```

#### attachments
```sql
CREATE TABLE attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attachment_id TEXT UNIQUE NOT NULL,
    message_id TEXT NOT NULL,
    original_filename TEXT,
    mime_type TEXT,
    file_size INTEGER,
    hash TEXT NOT NULL,  -- SHA-256 of original file
    original_path TEXT,  -- Relative path in export
    thumbnail_path TEXT,  -- Relative path to thumbnail
    width INTEGER,
    height INTEGER,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (message_id) REFERENCES messages(message_id) ON DELETE CASCADE,
    INDEX idx_message_id (message_id),
    INDEX idx_attachment_id (attachment_id)
);
```

#### annotations
```sql
CREATE TABLE annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    annotation_id TEXT UNIQUE NOT NULL,
    message_id TEXT NOT NULL,
    conversation_id TEXT NOT NULL,
    tags TEXT NOT NULL,  -- JSON array: ["Key", "Timeline"]
    note TEXT,
    created_by TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    updated_by TEXT,
    updated_at INTEGER,
    FOREIGN KEY (message_id) REFERENCES messages(message_id) ON DELETE CASCADE,
    INDEX idx_message_id (message_id),
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_created_at (created_at)
);
```

#### annotation_audit
```sql
CREATE TABLE annotation_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    annotation_id TEXT NOT NULL,
    action TEXT NOT NULL,  -- 'CREATE', 'UPDATE', 'DELETE'
    old_value TEXT,  -- JSON snapshot before change
    new_value TEXT,  -- JSON snapshot after change
    changed_by TEXT NOT NULL,
    changed_at INTEGER NOT NULL,
    INDEX idx_annotation_id (annotation_id),
    INDEX idx_changed_at (changed_at)
);
```

#### extraction_metadata
```sql
CREATE TABLE extraction_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id TEXT NOT NULL,
    extraction_timestamp INTEGER NOT NULL,
    extractor_name TEXT,
    extractor_version TEXT,
    source_db_path TEXT,
    source_db_hash TEXT NOT NULL,  -- SHA-256 of original iMessage DB
    total_messages INTEGER,
    total_attachments INTEGER,
    total_conversations INTEGER,
    extraction_config TEXT,  -- JSON config used
    created_at INTEGER NOT NULL
);
```

#### export_metadata
```sql
CREATE TABLE export_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    export_id TEXT UNIQUE NOT NULL,
    export_timestamp INTEGER NOT NULL,
    export_type TEXT NOT NULL,  -- 'clean', 'annotated', 'report'
    exported_by TEXT NOT NULL,
    case_id TEXT NOT NULL,
    conversation_id TEXT,
    part_number INTEGER,
    total_parts INTEGER,
    message_count INTEGER,
    annotation_count INTEGER,
    export_hash TEXT NOT NULL,  -- SHA-256 of export package
    created_at INTEGER NOT NULL
);
```

---

## HASH VERIFICATION SYSTEM

### Hash Types

#### 1. Source Database Hash
- **What**: SHA-256 of original iMessage database (chat.db)
- **When**: At extraction time, before any processing
- **Stored**: extraction_metadata.source_db_hash
- **Purpose**: Proves extraction source integrity

#### 2. Message Hash
- **What**: SHA-256 of message content (text + metadata)
- **When**: During extraction, per message
- **Stored**: messages.hash
- **Purpose**: Detects any message-level tampering

#### 3. Attachment Hash
- **What**: SHA-256 of original attachment file
- **When**: During extraction, per attachment
- **Stored**: attachments.hash
- **Purpose**: Proves attachment file integrity

#### 4. Export Hash
- **What**: SHA-256 of exported HTML evidence layer
- **When**: During export generation
- **Stored**: .hash.json sidecar file
- **Purpose**: Detects post-export modifications

### Hash Verification Workflow

```
EXTRACTION TIME:
1. Hash original iMessage DB → source_db_hash
2. For each message: Hash content → messages.hash
3. For each attachment: Hash file → attachments.hash
4. Store all hashes in messages.db

EXPORT TIME:
1. Extract evidence layer from messages.db
2. Generate HTML with embedded message IDs
3. Hash HTML evidence layer → export_hash
4. Create .hash.json:
   {
     "schema_version": "1.0",
     "export_timestamp": "2024-11-17T12:00:00Z",
     "export_id": "EXP_ABC2024_20241117120000",
     "source_db_hash": "<extraction_metadata.source_db_hash>",
     "export_hash": "<SHA-256 of HTML evidence layer>",
     "message_count": 10000,
     "part_number": 1,
     "total_parts": 10,
     "verification_algorithm": "SHA-256",
     "normalized_for_hash": ["line_endings:LF", "encoding:UTF-8"]
   }

VIEWING TIME (HTML load):
1. Read .hash.json → expected_hash
2. Extract evidence layer from current HTML
3. Normalize (line endings, encoding)
4. Calculate current_hash
5. Compare current_hash === expected_hash
6. Display result in left sidebar:
   - Match: ✓ Green "Evidence Verified"
   - Mismatch: ⚠ Red "Evidence Modified - Hash Mismatch"
   - Missing: ? Yellow "Cannot Verify - Hash File Missing"
```

### Normalization for Hashing
To ensure cross-platform hash stability:
- **Line endings**: Convert to LF (\n)
- **Encoding**: UTF-8 with BOM removal
- **Whitespace**: Preserve (forensic requirement)
- **Content extracted**: Evidence layer only (exclude annotations, navigation UI)

---

## EXPORT FORMATS

### Clean Export (Evidence Only)
```
case_ABC2024_clean/
├── conversation_001_of_010.html       # Evidence + viewer UI
├── conversation_001_of_010.hash.json  # Hash verification data
├── conversation_002_of_010.html
├── conversation_002_of_010.hash.json
├── ...
├── attachments/
│   ├── original/
│   │   ├── ATT_001_IMG_2024.jpg       # Original files
│   │   ├── ATT_002_document.pdf
│   │   └── ...
│   └── thumbs/
│       ├── ATT_001_thumb.jpg          # 150px thumbnails
│       ├── ATT_002_thumb.jpg
│       └── ...
├── attachments.json                    # Attachment metadata
├── extraction_report.json              # Extraction metadata
└── README.txt                          # Usage instructions
```

### Annotated Export (+ Annotations)
```
case_ABC2024_annotated/
├── conversation_001_of_010.html       # Evidence + annotations viewer
├── conversation_001_of_010.hash.json  # Hash verification data
├── conversation_001_of_010_annotations.json  # Annotations data
├── conversation_002_of_010.html
├── conversation_002_of_010.hash.json
├── conversation_002_of_010_annotations.json
├── ...
├── attachments/                        # Same as clean export
├── attachments.json
├── extraction_report.json
└── README.txt                          # + annotation usage instructions
```

### Report Bundle
```
case_ABC2024_report_20241117/
├── key_messages_report.html           # Styled HTML report
├── key_messages_report.pdf            # PDF version
├── annotations.json                    # All annotations (all parts)
└── README.txt                          # Report explanation
```

---

## ANNOTATION JSON SCHEMA

### annotations.json (per conversation part)
```json
{
  "schema_version": "1.0",
  "export_timestamp": "2024-11-17T12:00:00Z",
  "case_id": "ABC2024",
  "conversation_id": "CONV_A3F2B91C",
  "part_number": 1,
  "total_parts": 10,
  "annotations": [
    {
      "annotation_id": "ANN_001",
      "message_id": "MSG_ABC2024_20241117120000_A3F2B91C_00001",
      "tags": ["Key", "Timeline"],
      "note": "Defendant admits to being at the scene at 10:30 PM, contradicts earlier statement.",
      "created_by": "john.attorney@lawfirm.com",
      "created_at": "2024-11-17T14:30:00Z",
      "updated_by": null,
      "updated_at": null
    }
  ]
}
```

---

## FORENSIC REQUIREMENTS CHECKLIST

### Evidence Collection
- [ ] Read-only access to source iMessage database
- [ ] Hash source database before processing
- [ ] Preserve all message metadata
- [ ] Preserve attachment file metadata (timestamps, size)
- [ ] Document extraction configuration
- [ ] Log extraction process and any errors

### Evidence Integrity
- [ ] Hash all messages at extraction
- [ ] Hash all attachments at extraction
- [ ] Hash export packages at generation
- [ ] Verify hashes on load
- [ ] No modification of source data
- [ ] Audit trail for all operations

### Chain of Custody
- [ ] Record extractor name/ID
- [ ] Record extraction timestamp
- [ ] Record exporter name/ID for each export
- [ ] Record all annotation changes with user and timestamp
- [ ] Immutable audit log (append-only)

### Reproducibility
- [ ] Stable message IDs across re-exports
- [ ] Deterministic extraction process
- [ ] Version tracking (tool version, schema version)
- [ ] Configuration preservation

### Documentation
- [ ] Methodology documentation
- [ ] Tool version tracking
- [ ] Schema versioning
- [ ] User manual
- [ ] Technical documentation

### Separation of Evidence and Work Product
- [ ] Evidence layer immutable
- [ ] Annotations stored separately
- [ ] Clear visual distinction (UI labels)
- [ ] Annotations never modify message content
- [ ] Work product not included in clean exports

---

## DEVELOPMENT PHASES

### Phase 0: Project Setup (Current)
- Initialize project structure
- Set up Python environment
- Set up Electron skeleton
- Create development documentation

### Phase 1: Extraction Pipeline
- iMessage database reader
- Message parser
- Attachment extractor
- Hash generation system
- SQLite storage

### Phase 2: Hash Verification
- Hash verification module
- .hash.json generation
- Verification UI component

### Phase 3: HTML Export
- 3-column layout template
- iMessage-style conversation view
- Navigation sidebar
- Attachment viewer

### Phase 4: Annotation System (Desktop)
- Annotation modal UI
- SQLite annotation CRUD
- Audit logging
- Annotation sidebar (interactive)

### Phase 5: Read-Only Export
- Remove editing affordances
- Annotations JSON export
- Read-only annotation sidebar
- Work product warnings

### Phase 6: Report Generator
- Report data assembly
- HTML report template
- PDF generation
- Report bundle packaging

### Phase 7: Testing & Validation
- Forensic validation tests
- Performance testing
- Cross-platform testing
- Documentation completion

---

## NEXT STEPS

1. Initialize Python project structure
2. Set up Electron application skeleton
3. Create database schema and initialization
4. Begin Phase 1: Extraction Pipeline

---

END OF ARCHITECTURE DOCUMENT
