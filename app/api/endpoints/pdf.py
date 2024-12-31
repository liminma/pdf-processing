import json
import os
from uuid import uuid4
from datetime import datetime, timedelta
from fastapi import APIRouter, UploadFile, File, status, HTTPException, Form

import app.services.pdf as pdf_service
from app.core.config import settings


router = APIRouter(prefix='/pdf', tags=['pdf'])


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
    _, file_paths = list_tempfiles()
    return file_paths


@router.delete('/tempfiles', status_code=status.HTTP_204_NO_CONTENT)
async def delete_tempfiles():
    try:
        cleanup_tempfiles()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to delete temp files.")


@router.post('/images', response_model=list[str])
async def pdf_to_images(file: UploadFile = File(...)):
    if file.content_type != 'application/pdf':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid file type. Only PDF file allowed.'
        )

    try:
        pdfbytes = await file.read()

        random_str = uuid4().hex
        urls = []
        for i, image in enumerate(pdf_service.doc_to_images_gen(pdfbytes)):
            imagepath = f'{settings.TEMPFILE_ROOT_DIR}/{random_str}-p{i}.png'
            image.save(imagepath)
            urls.append(imagepath)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to convert the pdf file to images: {str(e)}'
        )

    return urls


@router.post('/figures', response_model=tuple[str, dict[int, list[tuple[str, str | None]]]])
async def extract_figures(
    file: UploadFile = File(...),
    redaction_bboxes: str = Form(...),
    figure_bboxes: str = Form(...),
    del_page_start: int | None = Form(None),
    del_page_end: int | None = Form(None),
    del_pages_list: str | None = Form(None)
):
    del_pages = json.loads(del_pages_list) if del_pages_list else None

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
        doc = pdf_service.bytes_to_doc(pdfbytes)

        random_str = uuid4().hex
        extracted_figures = pdf_service.extract_figures(doc, parsed_figure_bboxes)
        for k, v in extracted_figures.items():
            for idx, pair in enumerate(v):
                figure_path = f'{settings.TEMPFILE_ROOT_DIR}/{random_str}-page{k}-figure{idx}.png'
                pair[0].save(figure_path)
                pair[0] = figure_path
                if pair[1]:
                    caption_path = f'{settings.TEMPFILE_ROOT_DIR}/{random_str}-page{k}-caption{idx}.png'
                    pair[1].save(caption_path)
                    pair[1] = caption_path

        doc = pdf_service.redact_doc(doc, parsed_redaction_bboxes, parsed_figure_bboxes)
        doc = pdf_service.delete_pages(doc, del_page_start, del_page_end, del_pages)

        docpath = f'{settings.TEMPFILE_ROOT_DIR}/{random_str}.pdf'
        doc.save(docpath)
        return [docpath, extracted_figures]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to extract figures from the pdf file: {str(e)}'
        )
