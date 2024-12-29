import os
from uuid import uuid4
from datetime import datetime, timedelta
from fastapi import APIRouter, UploadFile, File, status, HTTPException

import app.services.pdf as pdf_service
from app.core.config import settings


router = APIRouter()


# TODO:
# - switch to non-blocking file handling
def list_tempfiles():
    curr_time = datetime.now()
    cutoff_time = curr_time - timedelta(seconds=settings.FILE_RETENTION_TIME)

    file_names = []
    file_paths = []
    for file_name in os.listdir(settings.TEMPFILE_ROOT_DIR):
        file_path = os.path.join(settings.TEMPFILE_ROOT_DIR, file_name)
        file_modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        if file_modified_time < cutoff_time:
            file_names.append(file_name)
            file_paths.append(file_path)
    return file_names, file_paths


def cleanup_tempfiles():
    _, file_paths = list_tempfiles()
    for file_path in file_paths:
        os.remove(file_path)


@router.get('/tempfiles', response_model=list[str])
async def get_tempfiles():
    file_names, _ = list_tempfiles()
    return file_names


@router.delete('/tempfiles', status_code=status.HTTP_204_NO_CONTENT)
async def delete_tempfiles():
    try:
        cleanup_tempfiles()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to delete temp files.")


@router.post('/convert/images', response_model=list[str])
async def pdf_to_images(file: UploadFile = File(...)):
    if file.content_type != 'application/pdf':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid file type. Only PDF file allowed.'
        )

    try:
        pdfbytes = await file.read()
        urls = []

        random_str = uuid4().hex
        for i, image in enumerate(pdf_service.doc_to_images(pdfbytes)):
            imagepath = f'{settings.TEMPFILE_ROOT_DIR}/{random_str}-p{i}.png'
            image.save(imagepath)
            urls.append(imagepath)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to convert the pdf file to images: {str(e)}'
        )

    return urls
