import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_NAME: str = os.getenv('PROJECT_NAME', '')
PROJECT_VERSION: str = os.getenv('PROJECT_VERSION', '')
FILE_RETENTION_TIME: int = int(os.getenv('FILE_RETENTION_TIME', 3600))  # seconds
TEMPFILE_ROOT_DIR: str = os.getenv('TEMPFILE_ROOT_DIR', 'static')
CORS_ORIGINS: str = os.getenv('CORS_ORIGINS', '')


class Settings:
    PROJECT_NAME: str = PROJECT_NAME
    PROJECT_VERSION: str = PROJECT_VERSION
    FILE_RETENTION_TIME: int = FILE_RETENTION_TIME
    TEMPFILE_ROOT_DIR: str = TEMPFILE_ROOT_DIR
    CORS_ORIGINS: str = CORS_ORIGINS


settings = Settings()
