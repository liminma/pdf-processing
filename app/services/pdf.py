import numpy as np
import pymupdf
from pymupdf import Document, Page
from PIL import Image


def page_to_image(page: Page, dpi: int = 96) -> Image.Image:
    """Convert a PDF page to an image."""
    pixmap = page.get_pixmap(dpi=dpi)
    return Image.frombytes('RGB', [pixmap.w, pixmap.h], pixmap.samples_mv)


def doc_to_images(pdfbytes: bytes, dpi: int = 96):
    """A pdf page to image generator."""
    doc = pymupdf.open('pdf', pdfbytes)
    for page in doc:
        yield page_to_image(page, dpi=dpi)


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


def redact_doc(pdfbytes: bytes, redaction_bboxes, figure_bboxes):
    doc = pymupdf.open('pdf', pdfbytes)

    delete_pages = []
    for k, v in redaction_bboxes.items():
        page = doc[k]
        redact_page(v, page)
        if is_blank_page(page):
            delete_pages.append(k)

    print(figure_bboxes)
    for k, v in figure_bboxes.items():
        page = doc[k]
        flattened = [item for pair in v for item in pair if item]
        print(flattened)
        redact_page(flattened, page)
        if is_blank_page(page):
            delete_pages.append(k)

    if delete_pages:
        doc.delete_pages(delete_pages)
    doc = reduce_pdf_size(doc)
    return doc


def reduce_pdf_size(doc: Document) -> Document:
    docbytes = doc.tobytes(garbage=3, deflate=True, use_objstms=1)
    doc = pymupdf.open('pdf', docbytes)
    return doc
