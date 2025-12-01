"""Application configuration"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # App
    APP_NAME: str = "ClearDOH"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./cleardoh.db"

    # Directories
    BASE_DIR: Path = Path(__file__).parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    OUTPUT_DIR: Path = BASE_DIR / "output"
    TEMPLATE_DIR: Path = BASE_DIR / "templates"
    DATA_DIR: Path = BASE_DIR / "data"

    # Auto-tagging
    CONFIDENCE_THRESHOLD: float = 0.92

    # File limits
    MAX_FILE_SIZE: int = 50  # MB

    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.UPLOAD_DIR.mkdir(exist_ok=True)
        self.OUTPUT_DIR.mkdir(exist_ok=True)
        self.TEMPLATE_DIR.mkdir(exist_ok=True)
        self.DATA_DIR.mkdir(exist_ok=True)


settings = Settings()
