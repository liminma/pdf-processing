from pydantic import BaseModel


class FiguresResponse(BaseModel):
    """
    Represents the response data for figure extraction from a PDF document.

    Attributes:
        doc (str): The file path to the updated PDF document.
        figures (dict[int, list[tuple[str, str | None]]]):
            A dictionary where keys are page numbers and values are lists of tuples.
            Each tuple contains:
                - A string representing the file path to an extracted figure.
                - A string (or None) representing the file path to the figure's caption, if available.
    """
    doc: str
    figures: dict[int, list[tuple[str, str | None]]]
