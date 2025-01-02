import tempfile
import json
import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.core.config import settings
from app.api.endpoints import pdf, heartbeat


@pytest.fixture(scope='module')
def app():
    test_app = FastAPI(title=settings.PROJECT_NAME,
                       version=settings.PROJECT_VERSION)
    test_app.include_router(pdf.router)
    test_app.include_router(heartbeat.router)
    yield test_app


@pytest.fixture(scope='module')
def client(app: FastAPI):
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope='function')
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_dir = settings.TEMPFILE_ROOT_DIR
        settings.TEMPFILE_ROOT_DIR = tmp_dir
        yield tmp_dir
        settings.TEMPFILE_ROOT_DIR = original_dir


def test_pdf_to_images_valid(client: TestClient, temp_dir):
    """
    Test /pdf/images endpoint with valid file type
    """
    test_file_path = 'app/tests/test_data/test_document.pdf'
    with open(test_file_path, 'rb') as f:
        files = {'file': f}
        response = client.post('/pdf/images', files=files)

    assert response.status_code == status.HTTP_200_OK
    image_paths = response.json()
    assert isinstance(image_paths, list)
    assert len(image_paths) == 2  # the test doc has 2 pages
    for path in image_paths:
        assert path.startswith(settings.TEMPFILE_ROOT_DIR)
        assert path.endswith('.png')


def test_pdf_to_images_invalid_file_type(client: TestClient, temp_dir):
    """
    Test /pdf/images endpoint with invalid file type
    """
    test_file_path = 'app/tests/test_data/gemini_generated_image.jpeg'
    with open(test_file_path, 'rb') as f:
        files = {'file': f}
        response = client.post('/pdf/images', files=files)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    error_response = response.json()
    assert 'detail' in error_response
    assert 'Invalid file type. Only PDF file allowed.' == error_response['detail']


def test_pdf_to_images_missing_file(client: TestClient):
    """
    Test /pdf/images endpoint without providing any file
    """
    response = client.post('/pdf/images')
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_response = response.json()
    assert 'detail' in error_response
    assert 'file' in str(error_response['detail'])


def test_extract_figures_valid(client: TestClient, temp_dir):
    """
    Test /pdf/figures endpoint with valid PDF file and data
    """
    test_file_path = 'app/tests/test_data/test_document.pdf'
    redaction_bboxes = {
        "0": [[0, 0, 816, 66], [761, 0, 816, 1056], [0, 990, 816, 1056], [0, 0, 77, 1056]],
        "1": [[0, 0, 816, 66], [761, 0, 816, 1056], [0, 990, 816, 1056], [0, 0, 55, 1056], [92, 906, 719, 987]]
    }
    figure_bboxes = {
        "1": [[[171, 64, 643, 370], [264, 368, 548, 404]]]
    }
    del_pages_list = [1]
    with open(test_file_path, 'rb') as f:
        files = {'file': f}
        data = {
            "redaction_bboxes": json.dumps(redaction_bboxes),
            "figure_bboxes": json.dumps(figure_bboxes),
            "del_pages_list": json.dumps(del_pages_list)
        }

        response = client.post('/pdf/figures', files=files, data=data)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()

    assert 'doc' in response_data
    assert response_data['doc'].startswith(settings.TEMPFILE_ROOT_DIR)
    assert response_data['doc'].endswith('.pdf')

    assert 'figures' in response_data
    assert isinstance(response_data['figures'], dict)

    for page, figures in response_data['figures'].items():
        for fig_pair in figures:
            assert len(fig_pair) == 2
            for fig in fig_pair:
                assert isinstance(fig, str)
                if fig:
                    assert fig.startswith(settings.TEMPFILE_ROOT_DIR)
                    assert fig.endswith('.png')


def test_extract_figures_missing_required_data(client: TestClient):
    """
    Test /pdf/figures endpoint without required form data
    """
    test_file_path = 'app/tests/test_data/test_document.pdf'
    with open(test_file_path, 'rb') as f:
        files = {'file': f}
        response = client.post('/pdf/figures', files=files)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_response = response.json()
    assert 'detail' in error_response
    assert 'redaction_bboxes' in str(error_response['detail'])
    assert 'figure_bboxes' in str(error_response['detail'])
