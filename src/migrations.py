"""Database migration utilities."""
import logging

from sqlalchemy import text

from src.database import engine, get_session

logger = logging.getLogger(__name__)


def run_migrations() -> None:
    """Run all database migrations."""
    _add_score_threshold_to_assistants()


def _add_score_threshold_to_assistants() -> None:
    """Add score_threshold column to assistants table if it doesn't exist."""
    session = get_session()
    try:
        # Check if column exists
        result = session.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'assistants' AND column_name = 'score_threshold'"
        ))
        if not result.fetchone():
            session.execute(text(
                "ALTER TABLE assistants ADD COLUMN score_threshold "
                "FLOAT NOT NULL DEFAULT 0.6"
            ))
            session.commit()
            logger.info("Migration: Added score_threshold column to assistants table")
        else:
            logger.debug("Migration: score_threshold column already exists")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        session.rollback()
    finally:
        session.close()
