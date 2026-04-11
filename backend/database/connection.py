"""
Database Connection Management

Provides:
    - Auto-detection: SQLite (local) vs PostgreSQL (cloud)
    - Session management with dependency injection
    - Automatic table creation on startup
    - Connection pooling and logging

Environment Variables:
    DATABASE_URL: PostgreSQL connection string (if not set, uses SQLite)
    Example: postgresql://user:password@localhost:5432/violations_db
"""

import os
import logging
from contextlib import contextmanager
from typing import Generator
from pathlib import Path

from sqlalchemy import create_engine, event, pool, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from backend.database.models import Base

logger = logging.getLogger(__name__)


# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

class DatabaseConfig:
    """Database configuration with auto-detection"""
    
    def __init__(self):
        """Initialize database config from environment"""
        self.database_url = os.getenv('DATABASE_URL', None)
        
        if self.database_url:
            # Cloud: PostgreSQL
            self.db_type = 'postgresql'
            self.use_sqlite = False
            self.url = self.database_url
            logger.info(f"Using PostgreSQL: {self._mask_url(self.url)}")
        else:
            # Local: SQLite
            self.db_type = 'sqlite'
            self.use_sqlite = True
            
            # Create data directory if needed
            data_dir = Path(__file__).parent.parent.parent / 'data'
            data_dir.mkdir(exist_ok=True)
            
            db_path = data_dir / 'violations.db'
            self.url = f'sqlite:///{db_path}'
            logger.info(f"Using SQLite: {db_path}")
    
    @staticmethod
    def _mask_url(url: str) -> str:
        """Mask sensitive info in connection URL"""
        if '@' in url:
            parts = url.split('@')
            masked_auth = '***:***'
            return f"{parts[0].split('//')[0]}//{masked_auth}@{parts[1]}"
        return url


# ============================================================================
# ENGINE AND SESSION SETUP
# ============================================================================

def create_db_engine(config: DatabaseConfig):
    """
    Create SQLAlchemy engine with appropriate settings.
    
    Args:
        config: DatabaseConfig instance
    
    Returns:
        SQLAlchemy Engine
    """
    if config.use_sqlite:
        # SQLite: Use check_same_thread=False for multi-threading
        engine = create_engine(
            config.url,
            connect_args={'check_same_thread': False},
            echo=False,  # Set to True for SQL logging
            pool_pre_ping=True,  # Verify connections before using
        )
        
        # Enable WAL mode for SQLite (better concurrency)
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_con, connection_record):
            cursor = dbapi_con.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()
        
        logger.info("SQLite WAL mode enabled for better concurrency")
    
    else:
        # PostgreSQL: Use connection pooling
        engine = create_engine(
            config.url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Verify connections
            echo=False,
        )
        
        logger.info("PostgreSQL connection pool initialized (size=10)")
    
    return engine


def init_db(engine):
    """
    Create all tables in database.
    
    Safe to call multiple times (only creates if not exists).
    
    Args:
        engine: SQLAlchemy Engine
    """
    logger.info("Creating database tables...")
    Base.metadata.create_all(engine)
    
    # Log created tables
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    logger.info(f"Database tables: {tables}")


# ============================================================================
# GLOBAL SESSION FACTORY
# ============================================================================

# Create config
_config = DatabaseConfig()

# Create engine
engine = create_db_engine(_config)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Initialize database (create tables if needed)
init_db(engine)


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection for database sessions.
    
    Usage in route/function:
        def my_handler(db: Session = Depends(get_db)):
            violations = db.query(Violation).all()
    
    Or with context manager:
        with get_db() as db:
            violations = db.query(Violation).all()
    
    Yields:
        SQLAlchemy Session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database sessions.
    
    Usage:
        with get_db_context() as db:
            violations = db.query(Violation).all()
    
    Yields:
        SQLAlchemy Session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# CONNECTION UTILITIES
# ============================================================================

def get_connection_info() -> dict:
    """
    Get current database connection information.
    
    Returns:
        Dictionary with connection details
    """
    return {
        'db_type': _config.db_type,
        'url': _config._mask_url(_config.url),
        'use_sqlite': _config.use_sqlite,
        'pool_size': engine.pool.size() if hasattr(engine.pool, 'size') else 'N/A',
        'pool_checked_out': engine.pool.checkedout() if hasattr(engine.pool, 'checkedout') else 'N/A',
    }


def health_check():
    """
    Check database connectivity.
    
    Returns:
        Tuple (is_healthy: bool, message: str)
    """
    try:
        with get_db_context() as db:
            db.execute(text("SELECT 1"))
        return True, "Database connection healthy"
    except Exception as e:
        return False, f"Database connection failed: {str(e)}"


def close_db():
    """Explicitly close database engine and connections."""
    engine.dispose()
    logger.info("Database connections closed")


# ============================================================================
# ALEMBIC SETUP (for future migrations)
# ============================================================================

def get_alembic_config():
    """
    Get Alembic configuration for database migrations.
    
    Usage:
        alembic init alembic_migrations
        cd alembic_migrations
        alembic revision --autogenerate -m "Initial migration"
        alembic upgrade head
    """
    from alembic.config import Config
    
    alembic_cfg = Config()
    alembic_cfg.set_main_option("sqlalchemy.url", _config.url)
    
    return alembic_cfg


# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

def startup():
    """Initialize database on application startup"""
    logger.info("Database startup sequence")
    
    # Check connection
    is_healthy, message = health_check()
    if is_healthy:
        logger.info(f"✓ {message}")
    else:
        logger.error(f"✗ {message}")
        raise RuntimeError("Failed to connect to database")
    
    # Log info
    info = get_connection_info()
    logger.info(f"Database type: {info['db_type']}")
    logger.info(f"Database URL: {info['url']}")


def shutdown():
    """Cleanup database on application shutdown"""
    logger.info("Database shutdown sequence")
    close_db()


# ============================================================================
# DEBUG UTILITIES
# ============================================================================

def print_db_info():
    """Print database information (for debugging)"""
    info = get_connection_info()
    print("\n" + "=" * 70)
    print("DATABASE INFORMATION")
    print("=" * 70)
    for key, value in info.items():
        print(f"{key:20}: {value}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    # Debug: Print database info
    logging.basicConfig(level=logging.INFO)
    print_db_info()
    
    # Test connection
    is_healthy, message = health_check()
    print(f"Health check: {message}")
    if is_healthy:
        print("✓ Database connection successful")
    else:
        print("✗ Database connection failed")
