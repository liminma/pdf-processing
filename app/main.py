import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.endpoints import heartbeat, pdf_v1
from app.core.config import settings


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="A REST API service for processing PDF files.",
)

# Configure CORS
if settings.CORS_ORIGINS:  # Only add CORS middleware if origins are defined
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

# Include routers for API endpoints
app.include_router(heartbeat.router)
app.include_router(pdf_v1.router, prefix='/v1')
app.include_router(pdf_v1.router, prefix='/latest')

os.makedirs(settings.TEMPFILE_ROOT_DIR, exist_ok=True)

# Mount the temporary file root directory to serve static files
app.mount(
    f'/{settings.TEMPFILE_ROOT_DIR}',
    StaticFiles(directory=settings.TEMPFILE_ROOT_DIR),
    name=settings.TEMPFILE_ROOT_DIR
)
