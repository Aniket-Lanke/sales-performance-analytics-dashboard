import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "sales-analytics-dev-secret-2026")
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    PORT = int(os.getenv("PORT", 5000))
    
    # Base paths
    BASE_DIR = BASE_DIR
    DATA_DIR = BASE_DIR / "data"
    UPLOAD_FOLDER = BASE_DIR / os.getenv("UPLOAD_FOLDER", "data/uploads")
    EXPORT_FOLDER = BASE_DIR / os.getenv("EXPORT_FOLDER", "data/exports")
    
    # Upload constraints
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 33554432)) # 32 MB
    ALLOWED_EXTENSIONS = set(os.getenv("ALLOWED_EXTENSIONS", "csv,xlsx,xls").split(","))
    
    # Database Settings
    DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").lower()
    ALLOW_SQLITE_FALLBACK = os.getenv("ALLOW_SQLITE_FALLBACK", "True").lower() in ("true", "1", "yes")
    
    # MySQL specific settings
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "sales_analytics_db")
    
    # SQLite fallback path
    SQLITE_DB_PATH = BASE_DIR / os.getenv("SQLITE_DB_PATH", "data/sales_analytics.db")
    
    # Raw override if DATABASE_URL is set
    DATABASE_URL = os.getenv("DATABASE_URL")

    # Pagination & Export
    PAGE_SIZE = int(os.getenv("PAGE_SIZE", 25))
    MAX_EXPORT_ROWS = int(os.getenv("MAX_EXPORT_ROWS", 100000))

    @classmethod
    def get_database_uri(cls):
        """
        Determines the active database URI.
        If DATABASE_URL is explicitly set, uses that.
        If DB_ENGINE is 'mysql', builds mysql+pymysql URI.
        Otherwise falls back to SQLite.
        """
        if cls.DATABASE_URL:
            return cls.DATABASE_URL

        if cls.DB_ENGINE == "mysql":
            pwd_part = f":{cls.DB_PASSWORD}" if cls.DB_PASSWORD else ""
            return f"mysql+pymysql://{cls.DB_USER}{pwd_part}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}?charset=utf8mb4"

        # Ensure directory for SQLite exists
        cls.SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Use absolute path with forward slashes for SQLite URI
        sqlite_abs_path = str(cls.SQLITE_DB_PATH.resolve()).replace("\\", "/")
        return f"sqlite:///{sqlite_abs_path}"

    @classmethod
    def init_folders(cls):
        """Ensure necessary runtime directories exist."""
        cls.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.EXPORT_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    DB_ENGINE = "sqlite"
    SQLITE_DB_PATH = Config.BASE_DIR / "data" / "test_sales_analytics.db"


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}
