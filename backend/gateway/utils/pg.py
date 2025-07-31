"""
Gateway Service Database Utilities Module

This module provides helper functions for interacting with the PostgreSQL database,
especially for recording and retrieving work task identifiers.

Functions:

- `get_postgresql_engine()`:
    Initializes and returns a SQLAlchemy engine connected to the configured database.

- `insert_work_id(work_id: str)`:
    Inserts a new record into the `meeting_summary` table with the given `work_id`.
    Commits the transaction and logs the operation. Any errors during insertion are printed.

Configuration:
- Relies on `DB_URL` from `gateway.config.settings` for database connection details.

Usage:
```python
from gateway.utils.pg import insert_work_id
insert_work_id(task_id)
```

Raises:
- Exceptions during database operations are caught and printed; consider enhancing error handling and logging.

TODO:
- Add retrieval and cleanup utilities.
- Integrate structured logging instead of prints.
- Parameterize table name and SQL statements for flexibility.
"""
from sqlalchemy import create_engine, text

from gateway.utils.logger import logger
from gateway.config.settings import DB_URL


def get_postgresql_engine():
    """
    Create and return a SQLAlchemy engine for PostgreSQL.

    Returns:
        Engine: An instance of SQLAlchemy Engine connected to the database.
    """
    pg_engine = create_engine(DB_URL)
    logger.info(f"DB connected at: {pg_engine} with {DB_URL}")
    return pg_engine


def insert_work_id(work_id: str):
    """
    Insert a work identifier into the `meeting_summary` table.

    Args:
        work_id (str): Unique identifier for the processing task.

    Returns:
        None

    Notes:
        - Commits the transaction after insertion.
        - Prints error messages on exception.
    """
    pg_engine = get_postgresql_engine()
    with pg_engine.connect() as conn:
        try:
            stmt = text("INSERT INTO meeting_summary (work_id) VALUES (:work_id)")
            conn.execute(stmt, {"work_id": str(work_id)})
            conn.commit()
            logger.info(f"Inserted work_id: {work_id} into database")
        except Exception as e:
            logger.error(f"Error inserting work_id {work_id}: {e}")
