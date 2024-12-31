import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.endpoints import heartbeat, pdf
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

app.include_router(heartbeat.router)
app.include_router(pdf.router)

os.makedirs(settings.TEMPFILE_ROOT_DIR, exist_ok=True)
app.mount(
    f'/{settings.TEMPFILE_ROOT_DIR}',
    StaticFiles(directory=settings.TEMPFILE_ROOT_DIR),
    name=settings.TEMPFILE_ROOT_DIR
)
