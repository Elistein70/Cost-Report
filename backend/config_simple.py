"""Simple config for Streamlit - no database needed"""
from pathlib import Path


class Settings:
    """Application settings"""
    BASE_DIR: Path = Path(__file__).parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    OUTPUT_DIR: Path = BASE_DIR / "output"
    TEMPLATE_DIR: Path = BASE_DIR / "data" / "templates"
    CONFIDENCE_THRESHOLD: float = 0.92

    def __init__(self):
        self.UPLOAD_DIR.mkdir(exist_ok=True)
        self.OUTPUT_DIR.mkdir(exist_ok=True)


settings = Settings()
