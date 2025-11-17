"""
Database Base Configuration
SQLAlchemy base class and session management with forensic-grade settings
"""

import logging
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, event, Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import StaticPool

from backend.config import DATABASE_CONFIG

logger = logging.getLogger("iexporter3.models")

# SQLAlchemy declarative base
Base = declarative_base()


def configure_sqlite_connection(dbapi_conn, connection_record):
    """
    Configure SQLite connection with forensic-grade pragmas.
    Called automatically for each new connection.
    """
    cursor = dbapi_conn.cursor()
    for pragma, value in DATABASE_CONFIG["pragmas"].items():
        cursor.execute(f"PRAGMA {pragma} = {value}")
    cursor.close()


def get_engine(database_path: str, echo: bool = False) -> Engine:
    """
    Create SQLAlchemy engine with forensic configuration.

    Args:
        database_path: Path to SQLite database file
        echo: If True, log all SQL statements

    Returns:
        Configured SQLAlchemy engine
    """
    # Ensure parent directory exists
    db_path = Path(database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Create engine with connection pooling
    engine = create_engine(
        f"sqlite:///{database_path}",
        echo=echo,
        poolclass=StaticPool,  # SQLite works best with single connection pool
        connect_args={"check_same_thread": False},  # Allow multi-threaded access
    )

    # Register connection configuration listener
    event.listen(engine, "connect", configure_sqlite_connection)

    logger.info(f"Database engine created: {database_path}")
    return engine


def get_session(database_path: str, echo: bool = False) -> Session:
    """
    Create database session.

    Args:
        database_path: Path to SQLite database file
        echo: If True, log all SQL statements

    Returns:
        SQLAlchemy session
    """
    engine = get_engine(database_path, echo=echo)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return SessionLocal()


def init_database(database_path: str, drop_existing: bool = False) -> Engine:
    """
    Initialize database with all tables and forensic configuration.

    Args:
        database_path: Path to SQLite database file
        drop_existing: If True, drop all existing tables first (DANGEROUS)

    Returns:
        Configured SQLAlchemy engine
    """
    engine = get_engine(database_path)

    if drop_existing:
        logger.warning(f"Dropping all existing tables in {database_path}")
        Base.metadata.drop_all(engine)

    # Create all tables
    Base.metadata.create_all(engine)
    logger.info(f"Database initialized: {database_path}")

    # Verify forensic configuration
    with engine.connect() as conn:
        pragmas = {}
        for pragma in DATABASE_CONFIG["pragmas"].keys():
            result = conn.execute(f"PRAGMA {pragma}").fetchone()
            pragmas[pragma] = result[0] if result else None

        logger.info(f"Forensic SQLite configuration verified: {pragmas}")

    return engine


def verify_database_integrity(database_path: str) -> dict:
    """
    Verify database integrity using SQLite's built-in checks.

    Args:
        database_path: Path to SQLite database file

    Returns:
        Dictionary with integrity check results
    """
    engine = get_engine(database_path)
    results = {
        "integrity_check": None,
        "foreign_key_check": None,
        "quick_check": None,
    }

    with engine.connect() as conn:
        # Full integrity check
        integrity = conn.execute("PRAGMA integrity_check").fetchall()
        results["integrity_check"] = [row[0] for row in integrity]

        # Foreign key check
        fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        results["foreign_key_check"] = (
            "OK" if not fk_violations else f"{len(fk_violations)} violations"
        )

        # Quick check
        quick = conn.execute("PRAGMA quick_check").fetchone()
        results["quick_check"] = quick[0] if quick else None

    return results


if __name__ == "__main__":
    # Test database initialization
    test_db = "/tmp/test_iexporter3.db"
    print(f"Testing database initialization: {test_db}")

    engine = init_database(test_db, drop_existing=True)
    print("Database initialized successfully")

    # Verify integrity
    integrity_results = verify_database_integrity(test_db)
    print("Integrity check results:")
    for check, result in integrity_results.items():
        print(f"  {check}: {result}")
