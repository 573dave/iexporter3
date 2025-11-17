"""
Configuration Management for iExporter3
Centralized configuration for extraction, export, and forensic settings
"""

import os
from pathlib import Path
from typing import Dict, Any

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Data Directories
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_DIR = DATA_DIR / "databases"
ATTACHMENTS_DIR = DATA_DIR / "attachments"
EXPORTS_DIR = DATA_DIR / "exports"

# Export Directories
EXPORT_ROOT = PROJECT_ROOT / "exports"

# Ensure directories exist
for directory in [DATA_DIR, DATABASE_DIR, ATTACHMENTS_DIR, EXPORTS_DIR, EXPORT_ROOT]:
    directory.mkdir(parents=True, exist_ok=True)

# Database Configuration
DATABASE_CONFIG = {
    "pragmas": {
        "journal_mode": "WAL",  # Write-Ahead Logging for better concurrency
        "synchronous": "NORMAL",  # Balance safety and performance
        "foreign_keys": "ON",  # Enforce referential integrity
        "secure_delete": "ON",  # Forensic requirement: overwrite deleted data
        "temp_store": "MEMORY",  # Keep temp tables in memory
        "cache_size": -64000,  # 64MB cache (negative = KB)
    },
    "pool_size": 5,
    "max_overflow": 10,
    "pool_pre_ping": True,  # Verify connections before using
}

# Forensic Settings
FORENSIC_CONFIG = {
    "hash_algorithm": "sha256",
    "hash_encoding": "utf-8",
    "line_ending_normalization": "LF",  # Convert to Unix line endings
    "timestamp_format": "iso8601",
    "timezone_storage": "UTC",
    "audit_log_enabled": True,
    "chain_of_custody_enabled": True,
}

# Message ID Format
MESSAGE_ID_FORMAT = {
    "prefix": "MSG",
    "separator": "_",
    "case_id_max_length": 20,
    "timestamp_format": "%Y%m%d%H%M%S",
    "hash_length": 8,  # First 8 chars of conversation hash
    "sequence_digits": 5,  # Zero-padded sequence number
}

# Annotation Configuration
ANNOTATION_CONFIG = {
    "tags": ["Key", "Timeline", "Privileged", "WorkProduct"],
    "note_max_length": 10000,
    "snippet_text_length": 200,
    "audit_retention_days": None,  # Keep forever (forensic requirement)
}

# Export Configuration
EXPORT_CONFIG = {
    "messages_per_part": 10000,
    "thumbnail_max_dimension": 150,
    "thumbnail_format": "JPEG",
    "thumbnail_quality": 85,
    "html_template_dir": PROJECT_ROOT / "frontend" / "templates",
    "static_assets_dir": PROJECT_ROOT / "frontend" / "static",
    "work_product_watermark": "INTERNAL WORK PRODUCT ONLY",
}

# Performance Settings
PERFORMANCE_CONFIG = {
    "load_time_target_ms": 2000,
    "memory_limit_mb": 200,
    "search_timeout_ms": 500,
    "hash_verification_timeout_ms": 1000,
    "export_timeout_seconds": 30,
    "batch_size_messages": 1000,
    "batch_size_attachments": 100,
}

# Schema Versions
SCHEMA_VERSIONS = {
    "database": "1.0",
    "annotations_json": "1.0",
    "hash_json": "1.0",
    "attachments_json": "1.0",
    "export_metadata": "1.0",
}

# Browser Compatibility
BROWSER_COMPATIBILITY = {
    "supported": [
        {"name": "Chrome", "versions": ["130", "131"]},
        {"name": "Edge", "versions": ["130", "131"]},
        {"name": "Safari", "versions": ["17", "18"]},
    ],
    "not_tested": ["Firefox"],
}

# macOS iMessage Database Location
IMESSAGE_DB_PATH = Path.home() / "Library" / "Messages" / "chat.db"
IMESSAGE_ATTACHMENTS_PATH = Path.home() / "Library" / "Messages" / "Attachments"

# Logging Configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "forensic": {
            "format": "[%(asctime)s UTC] [%(levelname)s] [%(name)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "colored": {
            "()": "colorlog.ColoredFormatter",
            "format": "%(log_color)s[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "log_colors": {
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "colored",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "forensic",
            "filename": str(PROJECT_ROOT / "logs" / "iexporter3.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "encoding": "utf-8",
        },
        "audit": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "forensic",
            "filename": str(PROJECT_ROOT / "logs" / "audit.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 50,  # Keep more audit logs
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "iexporter3": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        "iexporter3.audit": {
            "level": "INFO",
            "handlers": ["audit"],
            "propagate": False,
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
}

# Create logs directory
(PROJECT_ROOT / "logs").mkdir(exist_ok=True)


def get_config(section: str = None) -> Dict[str, Any]:
    """
    Get configuration section or entire config.

    Args:
        section: Configuration section name (e.g., 'database', 'forensic')
                If None, returns all configuration.

    Returns:
        Configuration dictionary
    """
    config_map = {
        "database": DATABASE_CONFIG,
        "forensic": FORENSIC_CONFIG,
        "message_id": MESSAGE_ID_FORMAT,
        "annotation": ANNOTATION_CONFIG,
        "export": EXPORT_CONFIG,
        "performance": PERFORMANCE_CONFIG,
        "schema": SCHEMA_VERSIONS,
        "browser": BROWSER_COMPATIBILITY,
        "logging": LOGGING_CONFIG,
    }

    if section is None:
        return config_map

    return config_map.get(section, {})


def validate_environment() -> Dict[str, bool]:
    """
    Validate that the environment is properly configured.

    Returns:
        Dictionary of validation results
    """
    validations = {
        "python_version": False,
        "imessage_db_exists": False,
        "imessage_db_readable": False,
        "data_directories": False,
        "write_permissions": False,
    }

    # Check Python version (3.11+)
    import sys
    validations["python_version"] = sys.version_info >= (3, 11)

    # Check iMessage database
    validations["imessage_db_exists"] = IMESSAGE_DB_PATH.exists()
    if validations["imessage_db_exists"]:
        validations["imessage_db_readable"] = os.access(IMESSAGE_DB_PATH, os.R_OK)

    # Check data directories
    validations["data_directories"] = all(
        d.exists() for d in [DATA_DIR, DATABASE_DIR, ATTACHMENTS_DIR, EXPORTS_DIR]
    )

    # Check write permissions
    validations["write_permissions"] = os.access(DATA_DIR, os.W_OK)

    return validations


if __name__ == "__main__":
    # Print configuration summary
    print("iExporter3 Configuration Summary")
    print("=" * 50)
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"iMessage DB Path: {IMESSAGE_DB_PATH}")
    print(f"Hash Algorithm: {FORENSIC_CONFIG['hash_algorithm']}")
    print(f"Messages per Part: {EXPORT_CONFIG['messages_per_part']}")
    print("\nEnvironment Validation:")
    for check, passed in validate_environment().items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}")
