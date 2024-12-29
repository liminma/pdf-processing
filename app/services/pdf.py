import pymupdf
from pymupdf import Page
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
