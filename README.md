# iExporter3 - Forensic-Grade iMessage Extraction & Review System

**Version**: 1.0.0
**Status**: Development
**Forensic Compliance**: ISO 27037, ISO 17025, NIST SP 800-86

---

## Overview

iExporter3 is a forensic-grade tool for extracting, reviewing, and annotating iMessage conversations with complete evidence integrity preservation. Designed for legal professionals, forensic examiners, and litigation support teams.

### Key Features

✅ **Forensically Sound Extraction**
- SHA-256 hash verification at every stage
- Read-only access to source data
- Complete audit trail
- Chain of custody preservation

✅ **Professional Review Interface**
- 3-column layout (Navigation | iMessage View | Annotations)
- iPad-style iMessage conversation display
- Attachment viewer with thumbnails
- Full-text search and filtering

✅ **Annotation System**
- Message-level annotations (tags + notes)
- Tag categories: Key, Timeline, Privileged, Work Product
- Desktop app: Full CRUD operations
- Export mode: Read-only display
- Audit logging for all changes

✅ **Multi-Format Exports**
- Clean HTML (evidence only)
- Annotated HTML (evidence + annotations)
- PDF reports (key messages summary)
- Cryptographic hash verification

✅ **Shared Drive Support**
- Multi-user access (last-write-wins)
- SQLite with WAL mode
- Offline operation (no servers required)

---

## Technology Stack

- **Backend**: Python 3.11+ (extraction, database, exports)
- **Desktop App**: Electron 28+ (cross-platform UI)
- **Database**: SQLite 3.35+ with WAL mode
- **ORM**: SQLAlchemy 2.0+
- **Hashing**: SHA-256 (all evidence integrity)
- **HTML/CSS/JS**: Vanilla (no frameworks for transparency)
- **PDF Generation**: WeasyPrint

---

## Project Structure

```
iexporter3/
├── backend/                 # Python extraction and processing
│   ├── models/              # SQLAlchemy database models
│   ├── extractors/          # iMessage extraction logic
│   ├── exporters/           # HTML/PDF export generators
│   ├── utils/               # Hashing, validation, helpers
│   └── tests/               # Unit and integration tests
├── frontend/                # UI and presentation layer
│   ├── desktop/             # Electron app
│   ├── templates/           # Jinja2 HTML templates
│   └── static/              # CSS, JavaScript, assets
│       ├── css/
│       ├── js/
│       └── assets/
├── docs/                    # Documentation
│   ├── ARCHITECTURE.md      # System architecture
│   ├── USER_GUIDE.md        # Attorney-facing guide
│   └── DEVELOPER.md         # Developer documentation
├── data/                    # Working data (gitignored)
│   ├── databases/           # SQLite databases
│   ├── attachments/         # Extracted attachments
│   └── exports/             # Generated exports
└── exports/                 # Final export packages
```

---

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- macOS (for iMessage database access)

### Installation

```bash
# Clone repository
git clone <repository_url>
cd iexporter3

# Set up Python environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up Electron app
cd frontend/desktop
npm install
cd ../..
```

### Usage

#### 1. Extract iMessage Conversations

```bash
python -m backend.extractors.imessage_extractor \
    --case-id "ABC2024" \
    --output data/databases/case_ABC2024.db
```

#### 2. Launch Desktop App (Annotation Mode)

```bash
cd frontend/desktop
npm start
```

#### 3. Export Conversations

```bash
# Clean export (evidence only)
python -m backend.exporters.html_exporter \
    --database data/databases/case_ABC2024.db \
    --output exports/case_ABC2024_clean \
    --mode clean

# Annotated export (evidence + annotations)
python -m backend.exporters.html_exporter \
    --database data/databases/case_ABC2024.db \
    --output exports/case_ABC2024_annotated \
    --mode annotated

# Generate report
python -m backend.exporters.report_generator \
    --database data/databases/case_ABC2024.db \
    --output exports/case_ABC2024_report
```

---

## Forensic Compliance

### Standards

- **ISO 27037**: Digital evidence collection and preservation
- **ISO 17025**: Testing and calibration laboratory competence
- **NIST SP 800-86**: Forensic techniques integration
- **NIST SP 800-101**: Mobile device forensics

### Evidence Integrity

1. **Hash Verification**
   - Source database hashed at extraction (SHA-256)
   - Every message hashed during extraction
   - Every attachment file hashed
   - Export packages hashed at generation
   - Automatic verification on HTML load

2. **Chain of Custody**
   - User identification for all operations
   - Timestamp tracking (UTC with timezone preservation)
   - Immutable audit log (append-only)
   - Complete action history

3. **Evidence Separation**
   - Evidence layer: Immutable messages and attachments
   - Work product layer: Mutable annotations (internal only)
   - Clear visual distinction in UI
   - Annotations never modify evidence content

### Audit Trail

All operations logged:
- Extraction: timestamp, user, source DB hash, message count
- Annotation changes: create, update, delete with before/after snapshots
- Exports: timestamp, user, export type, hash, message count
- Hash verification: timestamp, result, expected vs actual hash

---

## Message ID Format

Every message receives a globally unique, stable identifier:

```
MSG_<CASEID>_<EXTRACTION_TS>_<CONV_HASH>_<SEQ>

Example:
MSG_ABC2024_20241117120000_A3F2B91C_00001

Components:
- MSG_          : Fixed prefix
- ABC2024       : Case identifier
- 20241117120000: Extraction timestamp (UTC)
- A3F2B91C      : Conversation hash (first 8 chars)
- 00001         : Sequential message number
```

**Properties:**
- Globally unique across all cases
- Stable across re-exports from same source
- Sortable by sequence
- Traceable to extraction time

---

## Annotation System

### Tags (Fixed Set)

- **Key**: Important messages for case strategy
- **Timeline**: Timeline-relevant events or facts
- **Privileged**: Attorney-client privileged communications
- **Work Product**: Attorney work product (notes, analysis)

### Notes

Free-form text field (up to 10,000 characters) for detailed annotations.

### Annotation Scope

- Annotations apply to **messages only**, not attachments directly
- To annotate an attachment, annotate the message containing it
- Annotations are **per-file** (no cross-part linking)
- Annotations are **internal work product only** (never for external distribution)

### Multi-User Support

- **Deployment**: Shared drive (network or local)
- **Concurrent editing**: Last-write-wins (no merge conflict resolution)
- **Coordination**: Users must coordinate to avoid conflicts
- **Acceptable use**: Small teams (2-5 concurrent users)

---

## Export Modes

### Clean Export (Evidence Only)

- HTML conversation viewer
- Hash verification display
- Navigation and search
- Attachment viewer
- **No annotations** displayed or included
- For: External distribution (court, opposing counsel, expert witnesses)

### Annotated Export (Read-Only)

- All features of clean export
- **+ Annotations sidebar** (read-only)
- Filter by tag
- Jump to annotated messages
- **INTERNAL WORK PRODUCT ONLY** - Not for external distribution
- For: Internal team review and collaboration

### Report Bundle

- HTML report: Key messages summary table
- PDF report: Print-ready version
- Annotations JSON: Complete annotation data
- For: Team distribution, case preparation

---

## Security & Privacy

### Work Product Protection

- Annotations clearly labeled "INTERNAL WORK PRODUCT"
- UI watermarks on annotated exports
- Documentation warnings against external distribution
- Annotations stored separately from evidence layer

### Data Security

- All data stored locally (no cloud sync)
- SQLite with secure_delete pragma
- Attachment files preserved with original permissions
- No telemetry or external connections

---

## Browser Compatibility

### Desktop App (Electron)
- Built-in Chromium engine
- Full feature support
- Cross-platform (macOS, Windows, Linux)

### Exported HTML Viewers
- **Chrome 130+**: Full support ✅
- **Edge 130+**: Full support ✅
- **Safari 17-18**: Full support ✅
- **Firefox**: Not tested (may work)

---

## Performance Targets

- **Load time**: <2 seconds for 10,000 messages + 500 annotations
- **Memory usage**: <200MB for large conversation parts
- **Search**: <500ms for full-text search in 10,000 messages
- **Hash verification**: <1 second for 10,000-message HTML file
- **Export generation**: <30 seconds for 10-part conversation with attachments

---

## Limitations (Intentional)

- **No cloud sync**: All data local for security and forensic integrity
- **Fixed tag set**: No custom tags in v1.0 (future enhancement)
- **Per-file annotations**: No cross-part annotation linking in v1.0
- **Last-write-wins**: No collaborative merge conflict resolution
- **No attachment-level annotations**: Annotate containing message instead
- **macOS only** for extraction (iMessage database access)
- **Read-only source**: Cannot modify original iMessage database

---

## Development Status

### Completed
- [x] Architecture design
- [x] Project structure
- [x] Documentation framework

### In Progress
- [ ] Database schema implementation
- [ ] iMessage extraction pipeline
- [ ] Hash verification system

### Planned
- [ ] HTML export templates
- [ ] Annotation system (desktop)
- [ ] Read-only export mode
- [ ] Report generator
- [ ] Performance testing
- [ ] Forensic validation

---

## License

**Proprietary** - Internal use only

---

## Support

For questions or issues:
- Documentation: `docs/` directory
- Architecture: `ARCHITECTURE.md`
- User Guide: `docs/USER_GUIDE.md`
- Developer Guide: `docs/DEVELOPER.md`

---

## Changelog

### v1.0.0 (In Development)
- Initial release
- Core extraction pipeline
- Annotation system (desktop + read-only export)
- Hash verification system
- Report generator
- Forensic compliance (ISO 27037, NIST)

---

END OF README
