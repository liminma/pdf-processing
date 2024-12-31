import numpy as np
import pymupdf
from pymupdf import Document, Page
from PIL import Image, ImageOps


class PDFService:
    def __init__(self, pdfbytes: bytes, DPI=96):
        self.doc = PDFService.bytes_to_doc(pdfbytes)
        self.DPI = DPI

    def doc_to_images_gen(self):
        """Convert the doc to images."""
        for page in self.doc:
            yield self.page_to_image(page)

    def extract_figures(self, figure_bboxes):
        results = {}
        for k, v in figure_bboxes.items():
            page_image = self.page_to_image(self.doc[k])
            figures = []
            for pair in v:
                figure = PDFService.pad_border(page_image.crop(pair[0]))
                if pair[1]:  # optional caption
                    caption = PDFService.pad_border(page_image.crop(pair[1]))
                else:
                    caption = None
                figures.append([figure, caption])
            results[k] = figures

        return results

    def redact_doc(self, redaction_bboxes, figure_bboxes):
        delete_pages = []
        for k, v in redaction_bboxes.items():
            page = self.doc[k]
            PDFService.redact_page(v, page, self.DPI)
            if PDFService.is_blank_page(page):
                delete_pages.append(k)

        for k, v in figure_bboxes.items():
            page = self.doc[k]
            flattened = [item for pair in v for item in pair if item]
            PDFService.redact_page(flattened, page, self.DPI)
            if PDFService.is_blank_page(page):
                delete_pages.append(k)

        if delete_pages:
            self.doc.delete_pages(delete_pages)
        self.reduce_pdf_size()

    def delete_pages(
            self,
            del_page_start: int | None = None,
            del_page_end: int | None = None,
            del_pages_list: list[int] | None = None,
    ):
        pages_to_delete = PDFService.selected_pages(
            len(self.doc),
            start_page=del_page_start,
            end_page=del_page_end,
            pages_list=del_pages_list
        )
        if pages_to_delete:
            self.doc.delete_pages(pages_to_delete)
            self.reduce_pdf_size()

    def page_to_image(self, page: Page) -> Image.Image:
        """Convert a page to an image."""
        pixmap = page.get_pixmap(dpi=self.DPI)
        return Image.frombytes('RGB', [pixmap.w, pixmap.h], pixmap.samples_mv)

    def reduce_pdf_size(self):
        docbytes = PDFService.doc_to_bytes(self.doc)
        self.doc = PDFService.bytes_to_doc(docbytes)

    def save(self, output_filepath):
        self.doc.save(output_filepath)

    @staticmethod
    def doc_to_bytes(doc: Document) -> bytes:
        return doc.tobytes(garbage=3, deflate=True, use_objstms=1)

    @staticmethod
    def bytes_to_doc(pdfbytes: bytes) -> Document:
        return pymupdf.open('pdf', pdfbytes)

    @staticmethod
    def pad_border(image: Image.Image, border_width=10, border_color=(255, 255, 255)):
        return ImageOps.expand(image, border=border_width, fill=border_color)

    @staticmethod
    def redact_page(bboxes: list[list[int]], page: Page, DPI: int):
        """Redact a page with given bounding boxes."""
        # need to convert bboxes to coords used by pymupdf when doing redaction
        # pymupdf uses DPI 72 for redaction
        arr = np.array(bboxes) * 72 / DPI
        arr = arr.astype(int).tolist()

        for bbox in arr:
            page.add_redact_annot(bbox)
        page.apply_redactions(2, 2, 0)

    @staticmethod
    def is_blank_page(page: Page) -> bool:
        text = page.get_text().strip()
        if not text:
            return True
        else:
            return False

    @staticmethod
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
