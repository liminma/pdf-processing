import numpy as np
import re
import pymupdf
from pymupdf import Document, Page
from PIL import Image


def doc_to_images(pdfbytes: bytes, dpi: int = 96):
    """A pdf page to image generator."""
    doc = bytes_to_doc(pdfbytes)
    for page in doc:
        yield page_to_image(page, dpi=dpi)


def delete_pages(
    doc: Document,
    del_page_start: int | None = None,
    del_page_end: int | None = None,
    del_pages_list: list[int] | None = None,
):
    pages_to_delete = selected_pages(
        len(doc),
        start_page=del_page_start,
        end_page=del_page_end,
        pages_list=del_pages_list
    )
    if pages_to_delete:
        doc.delete_pages(pages_to_delete)
        doc = reduce_pdf_size(doc)
        return doc
    else:
        return doc


def redact_doc(doc: Document, redaction_bboxes, figure_bboxes):
    delete_pages = []
    for k, v in redaction_bboxes.items():
        page = doc[k]
        redact_page(v, page)
        if is_blank_page(page):
            delete_pages.append(k)

    for k, v in figure_bboxes.items():
        page = doc[k]
        flattened = [item for pair in v for item in pair if item]
        redact_page(flattened, page)
        if is_blank_page(page):
            delete_pages.append(k)

    if delete_pages:
        doc.delete_pages(delete_pages)
    doc = reduce_pdf_size(doc)
    return doc


def bytes_to_doc(pdfbytes: bytes) -> Document:
    return pymupdf.open('pdf', pdfbytes)


def doc_to_bytes(doc: Document) -> bytes:
    return doc.tobytes(garbage=3, deflate=True, use_objstms=1)


def page_to_image(page: Page, dpi: int = 96) -> Image.Image:
    """Convert a PDF page to an image."""
    pixmap = page.get_pixmap(dpi=dpi)
    return Image.frombytes('RGB', [pixmap.w, pixmap.h], pixmap.samples_mv)


def is_blank_page(page: Page) -> bool:
    text = page.get_text().strip()
    if not text:
        return True
    else:
        return False


def redact_page(bboxes: list[list[int]], page: Page):
    """Redact a page with given bounding boxes."""
    # bboxes are based on DPI 96, while pymupdf uses DPI 72 for redaction
    arr = np.array(bboxes) * 72 / 96
    arr = arr.astype(int).tolist()

    for bbox in arr:
        page.add_redact_annot(bbox)
    page.apply_redactions(2, 2, 0)


def reduce_pdf_size(doc: Document) -> Document:
    docbytes = doc_to_bytes(doc)
    doc = bytes_to_doc(docbytes)
    return doc


def selected_pages(
    total_pages: int,
    start_page: int | None = None,
    end_page: int | None = None,
    pages_list: list[int] | None = None,
):
    pages_to_process = set()

    if start_page or end_page:
        if start_page:
            if start_page < 0:
                # wrap from the end
                start_page = max(0, total_pages + start_page)
            elif start_page >= total_pages:
                raise ValueError("Invalid page selection.")

        if end_page:
            if end_page + total_pages < 0:
                raise ValueError("Invalid page selection.")
            elif end_page < 0:
                end_page = total_pages + end_page
            else:
                end_page = min(total_pages - 1, end_page)

        # print(start_page, end_page)
        if start_page or end_page:
            start_page = start_page if start_page else 0
            end_page = end_page if end_page else total_pages - 1
            pages_to_process.update(
                list(range(start_page, end_page+1))
            )

    if pages_list:
        pages_to_process.update(pages_list)

    if not pages_to_process:
        raise ValueError("Invalid page selection.")

    pages_to_process = list(filter(lambda x: x < total_pages, pages_to_process))
    return sorted(pages_to_process)
