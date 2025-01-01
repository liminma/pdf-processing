"""
This module defines the router for handling PDF-related operations. It includes API endpoints for:
    - Converting a PDF file to images.
    - Extracting figures and captions from a PDF file.
    - Listing temporary files.
    - Deleting temporary files.
"""

import json
import os
from uuid import uuid4
from datetime import datetime, timedelta
from fastapi import APIRouter, UploadFile, File, status, HTTPException, Form

from app.core.config import settings
from app.services.pdf_service import PDFService
from app.schemas.pdf import FiguresResponse


router = APIRouter(prefix='/pdf', tags=['pdf'])


@router.post('/images', response_model=list[str])
async def pdf_to_images(file: UploadFile = File(...)):
    """
    Convert a PDF file to images, one image per page.

    Args:
        file (UploadFile): The uploaded PDF file.

    Returns:
        list[str]: List of paths to the generated images.

    Raises:
        HTTPException: If the file type is invalid or conversion fails.
    """
    if file.content_type != 'application/pdf':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid file type. Only PDF file allowed.'
        )

    try:
        pdfbytes = await file.read()
        pdf_service = PDFService(pdfbytes)

        random_str = uuid4().hex
        urls = []
        for i, image in enumerate(pdf_service.doc_to_images_gen()):
            imagepath = f'{settings.TEMPFILE_ROOT_DIR}/{random_str}-page{i}.png'
            image.save(imagepath)
            urls.append(imagepath)

        return urls
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to convert the pdf file to images: {str(e)}'
        )


@router.post('/figures', response_model=FiguresResponse)
async def extract_figures(
    file: UploadFile = File(...),
    redaction_bboxes: str = Form(...),
    figure_bboxes: str = Form(...),
    del_page_start: int | None = Form(None),
    del_page_end: int | None = Form(None),
    del_pages_list: str | None = Form(None)
):
    """
    Extract figures and captions from a PDF file and redact specified areas.

    Args:
        file (UploadFile): The uploaded PDF file.
        redaction_bboxes (str): JSON string of bounding boxes to redact.
        figure_bboxes (str): JSON string of bounding boxes for figures.
        del_page_start (int | None): Start of page range to delete (optional).
        del_page_end (int | None): End of page range to delete (optional).
        del_pages_list (str | None): JSON string of specific pages to delete (optional).

    Returns:
        FiguresResponse: A response object containing the updated PDF file path and extracted figures.

    Raises:
        HTTPException: If the file type is invalid or figure extraction fails.
    """
    if file.content_type != 'application/pdf':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid file type. Only PDF file allowed.'
        )

    try:
        parsed_redaction_bboxes = json.loads(redaction_bboxes)
        parsed_redaction_bboxes = {int(k): v for k, v in parsed_redaction_bboxes.items()}

        parsed_figure_bboxes = json.loads(figure_bboxes)
        parsed_figure_bboxes = {int(k): v for k, v in parsed_figure_bboxes.items()}

        pdfbytes = await file.read()
        pdf_service = PDFService(pdfbytes)

        random_str = uuid4().hex
        extracted_figures = pdf_service.extract_figures(parsed_figure_bboxes)
        for k, v in extracted_figures.items():
            for idx, pair in enumerate(v):
                figure_path = f'{settings.TEMPFILE_ROOT_DIR}/{random_str}-page{k}-figure{idx}.png'
                pair[0].save(figure_path)
                pair[0] = figure_path
                if pair[1]:
                    caption_path = f'{settings.TEMPFILE_ROOT_DIR}/{random_str}-page{k}-caption{idx}.png'
                    pair[1].save(caption_path)
                    pair[1] = caption_path

        pdf_service.redact_doc(parsed_redaction_bboxes, parsed_figure_bboxes)

        del_pages = json.loads(del_pages_list) if del_pages_list else None
        pdf_service.delete_pages(del_page_start, del_page_end, del_pages)

        docpath = f'{settings.TEMPFILE_ROOT_DIR}/{random_str}.pdf'
        pdf_service.save(docpath)

        return FiguresResponse(doc=docpath, figures=extracted_figures)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to extract figures from the pdf file: {str(e)}'
        )


@router.get('/tempfiles', response_model=list[str])
async def get_tempfiles():
    """
    Retrieve a list of temporary files older than the retention time.

    Returns:
        list[str]: List of paths to temporary files.

    Raises:
        HTTPException: If listing files fails.
    """
    try:
        return list_tempfiles()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to list temp files.")


@router.delete('/tempfiles', status_code=status.HTTP_204_NO_CONTENT)
async def delete_tempfiles():
    """
    Delete all temporary files older than the retention time.

    Raises:
        HTTPException: If deletion fails.
    """
    try:
        for f in list_tempfiles():
            os.remove(f)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to delete temp files.")


def list_tempfiles():
    """
    List temporary files that exceed the retention time.

    Returns:
        list[str]: Paths to temporary files.
    """
    curr_time = datetime.now()
    cutoff_time = curr_time - timedelta(seconds=settings.FILE_RETENTION_TIME)

    file_paths = []
    for file_name in os.listdir(settings.TEMPFILE_ROOT_DIR):
        file_path = os.path.join(settings.TEMPFILE_ROOT_DIR, file_name)
        file_modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        if file_modified_time < cutoff_time:
            file_paths.append(file_path)
    return file_paths
