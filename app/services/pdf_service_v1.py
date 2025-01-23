import numpy as np
import pymupdf
from pymupdf import Document, Page
from PIL import Image, ImageOps


class PDFService:
    """
    Processing and manipulating PDF files, including functionalities such as converting PDF pages to images,
    extracting figures, redacting content, deleting pages, and reducing PDF file size.
    """

    def __init__(self, pdfbytes: bytes, DPI: int = 96):
        """
        Initialize the PDFService with PDF data in bytes format and an optional DPI value.

        Args:
            pdfbytes (bytes): The PDF file data in bytes.
            DPI (int, optional): The dots per inch (resolution) for image conversion from a PDF page. Defaults to 96.
        """
        self.doc = PDFService.bytes_to_doc(pdfbytes)
        self.DPI = DPI

    def doc_to_images_gen(self):
        """
        Generator that converts each page of the PDF document to an image.

        Yields:
            Image: An image of a PDF page.
        """
        for page in self.doc:
            yield self.page_to_image(page)

    def extract_figures(self, figure_bboxes):
        """
        Extract figures and optional captions from specified regions of PDF pages.

        Args:
            figure_bboxes (dict): A dictionary mapping page numbers to bounding boxes of figures and captions.

        Returns:
            dict: Extracted figures and optional captions organized by page numbers.
        """
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
        """
        Redact specified regions of PDF pages and delete blank pages.

        Args:
            redaction_bboxes (dict): Bounding boxes for redaction.
            figure_bboxes (dict): Bounding boxes for figures and captions.
        """
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
        """
        Delete selected pages from the PDF document.

        Args:
            del_page_start (int | None): The starting page index for deletion.
            del_page_end (int | None): The ending page index for deletion.
            del_pages_list (list[int] | None): Specific page indices to delete.
        """
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
        """
        Convert a single PDF page to an image.

        Args:
            page (Page): The PDF page to convert.

        Returns:
            Image.Image: The converted image.
        """
        pixmap = page.get_pixmap(dpi=self.DPI)
        return Image.frombytes('RGB', [pixmap.w, pixmap.h], pixmap.samples_mv)

    def reduce_pdf_size(self):
        """
        Reduce the size of the PDF file after processing.
        """
        docbytes = PDFService.doc_to_bytes(self.doc)
        self.doc = PDFService.bytes_to_doc(docbytes)

    def save(self, output_filepath):
        """
        Save the PDF document to a specified file path.

        Args:
            output_filepath (str): The file path to save the updated PDF.
        """
        self.doc.save(output_filepath)

    @staticmethod
    def doc_to_bytes(doc: Document) -> bytes:
        """
        Convert a PDF Document to bytes.

        Args:
            doc (Document): The PDF document to convert.

        Returns:
            bytes: The PDF data in bytes.
        """
        return doc.tobytes(garbage=3, deflate=True, use_objstms=1)

    @staticmethod
    def bytes_to_doc(pdfbytes: bytes) -> Document:
        """
        Convert PDF bytes to a Document object.

        Args:
            pdfbytes (bytes): The PDF data in bytes.

        Returns:
            Document: The Document object representing the PDF.
        """
        return pymupdf.open('pdf', pdfbytes)

    @staticmethod
    def pad_border(image: Image.Image, border_width=10, border_color=(255, 255, 255)):
        """
        Add padding around an image.

        Args:
            image (Image.Image): The image to pad.
            border_width (int, optional): The width of the padding. Defaults to 10.
            border_color (tuple, optional): The color of the padding. Defaults to white.

        Returns:
            Image.Image: The padded image.
        """
        return ImageOps.expand(image, border=border_width, fill=border_color)

    @staticmethod
    def redact_page(bboxes: list[list[int]], page: Page, DPI: int):
        """
        Redact regions of a PDF page based on bounding boxes.

        Args:
            bboxes (list[list[int]]): The bounding boxes to redact.
            page (Page): The PDF page to redact.
            DPI (int): The resolution for converting bounding boxes.
        """
        # need to convert bboxes to coords used by pymupdf when doing redaction
        # pymupdf uses DPI 72 for redaction
        arr = np.array(bboxes) * 72 / DPI
        arr = arr.astype(int).tolist()

        for bbox in arr:
            page.add_redact_annot(bbox)
        page.apply_redactions(2, 2, 0)

    @staticmethod
    def is_blank_page(page: Page) -> bool:
        """
        Check if a PDF page is blank.

        Args:
            page (Page): The PDF page to check.

        Returns:
            bool: True if the page is blank, False otherwise.
        """
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
        """
        Determine pages to process based on user input.

        Args:
            total_pages (int): The total number of pages in the document.
            start_page (int | None, optional): The starting page index. Defaults to None.
            end_page (int | None, optional): The ending page index. Defaults to None.
            pages_list (list[int] | None, optional): Specific page indices to process. Defaults to None.

        Returns:
            list[int]: The list of pages to process.

        Raises:
            ValueError: If the page selection is invalid.
        """
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

            if start_page or end_page:
                start_page = start_page if start_page else 0
                end_page = end_page if end_page else total_pages - 1
                pages_to_process.update(
                    list(range(start_page, end_page+1))
                )

        if pages_list:
            pages_to_process.update(pages_list)

        pages_to_process = list(filter(lambda x: x < total_pages, pages_to_process))
        return sorted(pages_to_process)
