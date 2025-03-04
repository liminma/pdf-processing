# PDF Processing
This FastAPI application provides REST API endpoints for processing PDF files, including converting PDFs to images, extracting figures and captions, and managing temporary files.

## Features
- **Convert PDF to Images**: Generate one image per page of a PDF.
- **Extract Figures and Captions**: Extract figures and captions from PDF files based on bounding boxes.
- **CORS Support**: Configurable Cross-Origin Resource Sharing (CORS).

## Project Structure

```
app
├── main.py
├── api
│   └── endpoints
│       ├── heartbeat.py
│       └── pdf_v1.py
├── core
│   └── config.py
├── schemas
│   └── pdf_v1.py
├── services
│   └── pdf_service_v1.py
└── tests
    ├── test_data
    └── test_pdf.py
```

## Installation

1. **Clone the repository:**

    ```bash
    git clone git@github.com:liminma/pdf-processing.git
    cd pdf-processing
    ```

2. **Create a virtual environment and activate it:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Set up environment variables:**

    copy the `.env.example` file to `.env`:

    ```sh
    cp .env.example .env
    ```

    modify the environment variables in the .env file if needed:

    ```env
    PROJECT_NAME="PDF Processing Service"
    PROJECT_VERSION=0.1.0
    FILE_RETENTION_TIME=3600 # File retention time in seconds
    TEMPFILE_ROOT_DIR=static
    CORS_ORIGINS=["*"] # Update with specific origins if needed
    ```

5. **Run the application:**

    ```bash
    uvicorn app.main:app --reload
    ```

6. **Access the API:**

    Open your browser and navigate to [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to view the interactive API documentation.

## API Endpoints

### Heartbeat Endpoint

- **GET /heartbeat**

  Returns a simple health check response.

### PDF Endpoints

#### Convert PDF to Images
- **POST /v1/pdf/images**
  - Upload a PDF file and get a list of image URLs for pages.

#### Extract Figures and Captions
- **POST /v1/pdf/figures**
  - Upload a PDF file with additional bounding boxes to extract and redact content.

#### List Temporary Files
- **GET /v1/pdf/tempfiles**
  - Retrieve a list of temporary files older than the configured retention time.

#### Delete Temporary Files
- **DELETE /v1/pdf/tempfiles**
  - Remove all temporary files older than the retention time.

## Configuration

### Environment Variables

- **PROJECT_NAME**: The name of the project.
- **PROJECT_VERSION**: The version of the project.
- **TEMPFILE_ROOT_DIR**: Directory where temporary files are stored.
- **FILE_RETENTION_TIME**: Retention time (in seconds) for temporary files.
- **CORS_ORIGINS**: List of allowed origins for CORS.

### Static File Serving

Generated files are served through static routes. For example, if a file is saved as `static/page1.png`, it can be accessed at `/static/page1.png`.

## About license

This project is licensed under the AGPL-3.0 license because it depends on the AGPL-3.0-licensed `PyMuPDF` library.
