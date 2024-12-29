import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_NAME = os.getenv('PROJECT_NAME', '')
PROJECT_VERSION = os.getenv('PROJECT_VERSION', '')
FILE_RETENTION_TIME: int = int(os.getenv('FILE_RETENTION_TIME', 60))  # seconds
TEMPFILE_ROOT_DIR: str = os.getenv('TEMPFILE_ROOT_DIR', 'static')


class Settings:
    PROJECT_NAME: str = PROJECT_NAME
    PROJECT_VERSION: str = PROJECT_VERSION
    FILE_RETENTION_TIME: int = FILE_RETENTION_TIME
    TEMPFILE_ROOT_DIR: str = TEMPFILE_ROOT_DIR


settings = Settings()
