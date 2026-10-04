import logging
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from app.config import Config

logger = logging.getLogger("sales_dashboard.database")

Base = declarative_base()

_engine = None
_SessionFactory = None
active_db_type = "unknown"


def get_engine(config_class=None):
    """
    Creates or returns the active SQLAlchemy engine.
    Supports seamless fallback to SQLite if MySQL is unavailable.
    """
    global _engine, active_db_type
    
    if _engine is not None:
        return _engine
        
    cfg = config_class or Config
    target_uri = cfg.get_database_uri()
    
    if "mysql" in target_uri:
        try:
            logger.info(f"Attempting connection to MySQL at {cfg.DB_HOST}:{cfg.DB_PORT}/{cfg.DB_NAME}...")
            engine = create_engine(
                target_uri,
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_size=10,
                max_overflow=20,
                connect_args={"connect_timeout": 5}
            )
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Successfully connected to MySQL database.")
            _engine = engine
            active_db_type = "MySQL"
            return _engine
        except Exception as e:
            logger.warning(f"MySQL connection failed: {e}")
            if cfg.ALLOW_SQLITE_FALLBACK:
                logger.info("Falling back to local SQLite demo database...")
                cfg.SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
                sqlite_path = str(cfg.SQLITE_DB_PATH.resolve()).replace("\\", "/")
                fallback_uri = f"sqlite:///{sqlite_path}"
                engine = create_engine(
                    fallback_uri,
                    connect_args={"check_same_thread": False}
                )
                _engine = engine
                active_db_type = "SQLite (Local Fallback)"
                _setup_sqlite_pragmas(_engine)
                return _engine
            else:
                raise e
    else:
        # Direct SQLite
        cfg.SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        sqlite_path = str(cfg.SQLITE_DB_PATH.resolve()).replace("\\", "/")
        sqlite_uri = f"sqlite:///{sqlite_path}"
        engine = create_engine(
            sqlite_uri,
            connect_args={"check_same_thread": False}
        )
        _engine = engine
        active_db_type = "SQLite"
        _setup_sqlite_pragmas(_engine)
        return _engine


def _setup_sqlite_pragmas(engine):
    """Enables foreign keys and WAL mode for SQLite performance and integrity."""
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


def get_session(engine=None):
    """Returns a thread-safe scoped session."""
    global _SessionFactory
    if engine is None:
        engine = get_engine()
    if _SessionFactory is None:
        _SessionFactory = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
    return _SessionFactory()


def init_db(engine=None):
    """Initializes all database tables from models."""
    if engine is None:
        engine = get_engine()
    # Import models so Base metadata is populated
    from app.models import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")


def get_db_status():
    """Returns diagnostics regarding the active database connection."""
    engine = get_engine()
    status = {
        "engine_type": active_db_type,
        "is_connected": False,
        "url_sanitized": str(engine.url).split("@")[-1] if "@" in str(engine.url) else str(engine.url),
        "table_counts": {}
    }
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            status["is_connected"] = True
            
            # Count rows in key tables if they exist
            for tbl in ["orders", "order_items", "customers", "products", "regions", "categories"]:
                try:
                    res = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
                    status["table_counts"][tbl] = res
                except Exception:
                    status["table_counts"][tbl] = 0
    except Exception as e:
        status["error"] = str(e)
    return status
